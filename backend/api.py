import os
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, g, jsonify, request
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import inspect, text

from claimer import start as start_claimer
from models import (
    BandChange,
    BandSetting,
    Base,
    ConvergenceLog,
    SessionLocal,
    band_change_dict,
    band_dict,
    engine,
    row_dict,
)
from rules import DEFAULT_INNER_MM, DEFAULT_OUTER_MM, judge, valid_bounds

SECRET = os.environ.get("JWT_SECRET", "tunnelconv-dev-secret")
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
USERS = {
    "surveyor": {"role": "writer", "password_hash": pwd.hash("surv123456")},
    "inspector": {"role": "reader", "password_hash": pwd.hash("insp123456")},
    "monitor": {"role": "monitor", "password_hash": pwd.hash("mon123456")},
}

ROLE_NAMES = {"writer": "测量员", "reader": "巡检员", "monitor": "监理"}

app = Flask(__name__)


def migrate_columns():
    """新库靠 create_all 建全部表/列；老库幂等补两列快照列。"""
    Base.metadata.create_all(engine)
    columns = ("band_inner_mm", "band_outer_mm")
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            for name in columns:
                conn.execute(
                    text(f"ALTER TABLE convergence_logs ADD COLUMN IF NOT EXISTS {name} DOUBLE PRECISION")
                )
    else:  # sqlite（测试用）不支持 ADD COLUMN IF NOT EXISTS
        existing = {c["name"] for c in inspect(engine).get_columns("convergence_logs")}
        with engine.begin() as conn:
            for name in columns:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE convergence_logs ADD COLUMN {name} FLOAT"))


def ensure_band(db) -> BandSetting:
    """无配置行则插入默认 3.0/3.4，并追加系统初始化履历。"""
    band = db.get(BandSetting, 1)
    if band is not None:
        return band
    now = datetime.now(timezone.utc)
    band = BandSetting(
        id=1,
        inner_mm=DEFAULT_INNER_MM,
        outer_mm=DEFAULT_OUTER_MM,
        updated_by="system",
        updated_at=now,
    )
    db.add(band)
    db.add(
        BandChange(
            old_inner_mm=None,
            new_inner_mm=DEFAULT_INNER_MM,
            old_outer_mm=None,
            new_outer_mm=DEFAULT_OUTER_MM,
            changed_by="system",
            changed_at=now,
            note="系统初始化",
        )
    )
    db.flush()
    return band


def seed():
    migrate_columns()
    db = SessionLocal()
    try:
        ensure_band(db)
        if db.query(ConvergenceLog).count() > 0:
            db.commit()
            return
        now = datetime.now(timezone.utc)
        for chainage, delta, expect in (("K12+180", 1.2, "合格"), ("K18+040", 5.6, "超限")):
            verdict, reason = judge(delta)
            assert verdict == expect
            db.add(
                ConvergenceLog(
                    chainage=chainage,
                    delta_mm=delta,
                    status="done",
                    verdict=verdict,
                    reason=reason,
                    band_inner_mm=DEFAULT_INNER_MM,
                    band_outer_mm=DEFAULT_OUTER_MM,
                    created_by="surveyor",
                    created_at=now,
                    processed_at=now,
                )
            )
        db.commit()
    finally:
        db.close()


seed()
if os.environ.get("CLAIMER_ENABLED", "1") != "0":
    start_claimer()


def current_user():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(auth[7:].strip(), SECRET, algorithms=["HS256"])
    except JWTError:
        return None
    sub = payload.get("sub")
    if sub not in USERS:
        return None
    return {"username": sub, "role": payload.get("role")}


def require_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return jsonify({"detail": "未登录"}), 401
        g.user = user
        return fn(*args, **kwargs)

    return wrapper


def require_writer(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return jsonify({"detail": "未登录"}), 401
        if user["role"] != "writer":
            return jsonify({"detail": "仅测量员可提交收敛读数"}), 403
        g.user = user
        return fn(*args, **kwargs)

    return wrapper


def require_monitor(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return jsonify({"detail": "未登录"}), 401
        if user["role"] != "monitor":
            return jsonify({"detail": "仅监理可修改判定带"}), 403
        g.user = user
        return fn(*args, **kwargs)

    return wrapper


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "tunnel-convergence-desk"})


@app.post("/api/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    user = USERS.get(username)
    if not user or not pwd.verify(password, user["password_hash"]):
        return jsonify({"detail": "用户名或密码错误"}), 401
    exp = datetime.now(timezone.utc) + timedelta(hours=8)
    token = jwt.encode(
        {"sub": username, "role": user["role"], "exp": exp}, SECRET, algorithm="HS256"
    )
    return jsonify(
        {
            "access_token": token,
            "username": username,
            "role": user["role"],
            "role_name": ROLE_NAMES.get(user["role"], user["role"]),
        }
    )


@app.get("/api/logs")
@require_login
def list_logs():
    db = SessionLocal()
    try:
        rows = db.query(ConvergenceLog).order_by(ConvergenceLog.id.desc()).all()
        return jsonify([row_dict(r) for r in rows])
    finally:
        db.close()


@app.post("/api/logs")
@require_writer
def create_log():
    body = request.get_json(silent=True) or {}
    chainage = (body.get("chainage") or "").strip()
    if not chainage:
        return jsonify({"detail": "桩号不能为空"}), 400
    try:
        delta_mm = float(body.get("delta_mm"))
    except (TypeError, ValueError):
        return jsonify({"detail": "收敛值必须是数字"}), 400
    db = SessionLocal()
    try:
        # 提交时快照当前判定带：之后改带不影响本单（含仍在排队的本单）。
        band = db.get(BandSetting, 1)
        inner = band.inner_mm if band else DEFAULT_INNER_MM
        outer = band.outer_mm if band else DEFAULT_OUTER_MM
        row = ConvergenceLog(
            chainage=chainage,
            delta_mm=delta_mm,
            status="pending",
            band_inner_mm=inner,
            band_outer_mm=outer,
            created_by=g.user["username"],
            created_at=datetime.now(timezone.utc),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return jsonify(row_dict(row)), 201
    finally:
        db.close()


@app.get("/api/band")
@require_login
def get_band():
    db = SessionLocal()
    try:
        band = ensure_band(db)
        db.commit()
        return jsonify(band_dict(band))
    finally:
        db.close()


@app.get("/api/band/history")
@require_login
def get_band_history():
    db = SessionLocal()
    try:
        rows = db.query(BandChange).order_by(BandChange.id.desc()).all()
        return jsonify([band_change_dict(r) for r in rows])
    finally:
        db.close()


@app.put("/api/band")
@require_monitor
def update_band():
    body = request.get_json(silent=True) or {}
    ok, message = valid_bounds(body.get("inner_mm"), body.get("outer_mm"))
    if not ok:
        return jsonify({"detail": message}), 400
    inner = float(body["inner_mm"])
    outer = float(body["outer_mm"])
    note = (body.get("note") or "").strip() or None
    db = SessionLocal()
    try:
        band = ensure_band(db)
        if inner == band.inner_mm and outer == band.outer_mm:
            return jsonify({"detail": "新旧判定带相同，无需修改"}), 400
        now = datetime.now(timezone.utc)
        db.add(
            BandChange(
                old_inner_mm=band.inner_mm,
                new_inner_mm=inner,
                old_outer_mm=band.outer_mm,
                new_outer_mm=outer,
                changed_by=g.user["username"],
                changed_at=now,
                note=note,
            )
        )
        band.inner_mm = inner
        band.outer_mm = outer
        band.updated_by = g.user["username"]
        band.updated_at = now
        db.commit()
        return jsonify(band_dict(band))
    finally:
        db.close()
