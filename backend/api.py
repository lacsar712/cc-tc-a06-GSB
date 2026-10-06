import os
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, g, jsonify, request
from jose import JWTError, jwt
from passlib.context import CryptContext

from claimer import start as start_claimer
from models import (
    Base,
    BandConfig,
    ConvergenceLog,
    SessionLocal,
    band_dict,
    engine,
    row_dict,
)
from rules import DEFAULT_INNER_MM, DEFAULT_OUTER_MM, judge

SECRET = os.environ.get("JWT_SECRET", "tunnelconv-dev-secret")
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
USERS = {
    "surveyor": {"role": "writer", "password_hash": pwd.hash("surv123456")},
    "inspector": {"role": "reader", "password_hash": pwd.hash("insp123456")},
}

app = Flask(__name__)


def migrate():
    Base.metadata.create_all(engine)
    # 老库补快照列；新库列已随 create_all 建好（SQLite 不支持 IF NOT EXISTS，忽略报错）
    with engine.begin() as conn:
        for col in ("band_inner_mm", "band_outer_mm"):
            try:
                conn.exec_driver_sql(
                    f"ALTER TABLE convergence_logs ADD COLUMN IF NOT EXISTS {col} DOUBLE PRECISION"
                )
            except Exception:
                pass


def seed():
    db = SessionLocal()
    try:
        band = db.query(BandConfig).order_by(BandConfig.id.desc()).first()
        if band is None:
            band = BandConfig(
                inner_mm=DEFAULT_INNER_MM,
                outer_mm=DEFAULT_OUTER_MM,
                changed_by="system",
                changed_at=datetime.now(timezone.utc),
                note=f"初始带：合格 ±{DEFAULT_INNER_MM} mm，琥珀近阈 {DEFAULT_INNER_MM}~{DEFAULT_OUTER_MM} mm",
            )
            db.add(band)
            db.commit()
            db.refresh(band)
        if db.query(ConvergenceLog).count() > 0:
            return
        now = datetime.now(timezone.utc)
        is_default_band = (
            band.inner_mm == DEFAULT_INNER_MM and band.outer_mm == DEFAULT_OUTER_MM
        )
        for chainage, delta, expect in (("K12+180", 1.2, "合格"), ("K18+040", 5.6, "超限")):
            verdict, reason = judge(delta, band.inner_mm, band.outer_mm)
            if is_default_band:
                assert verdict == expect
            db.add(
                ConvergenceLog(
                    chainage=chainage,
                    delta_mm=delta,
                    status="done",
                    verdict=verdict,
                    reason=reason,
                    band_inner_mm=band.inner_mm,
                    band_outer_mm=band.outer_mm,
                    created_by="surveyor",
                    created_at=now,
                    processed_at=now,
                )
            )
        db.commit()
    finally:
        db.close()


migrate()
seed()
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
    return jsonify({"access_token": token, "username": username, "role": user["role"]})


@app.get("/api/logs")
@require_login
def list_logs():
    db = SessionLocal()
    try:
        rows = db.query(ConvergenceLog).order_by(ConvergenceLog.id.desc()).all()
        return jsonify([row_dict(r) for r in rows])
    finally:
        db.close()


@app.get("/api/logs/<int:log_id>")
@require_login
def get_log(log_id):
    db = SessionLocal()
    try:
        row = db.get(ConvergenceLog, log_id)
        if row is None:
            return jsonify({"detail": "单据不存在"}), 404
        return jsonify(row_dict(row))
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
        row = ConvergenceLog(
            chainage=chainage,
            delta_mm=delta_mm,
            status="pending",
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
        band = db.query(BandConfig).order_by(BandConfig.id.desc()).first()
        if band is None:
            return jsonify({"detail": "尚未设置琥珀带"}), 404
        return jsonify(band_dict(band))
    finally:
        db.close()


@app.get("/api/band/history")
@require_login
def band_history():
    db = SessionLocal()
    try:
        rows = db.query(BandConfig).order_by(BandConfig.id.desc()).all()
        return jsonify([band_dict(b) for b in rows])
    finally:
        db.close()


@app.post("/api/band")
@require_login
def change_band():
    if g.user["role"] != "writer":
        return jsonify({"detail": "巡检员只读，不能改带"}), 403
    body = request.get_json(silent=True) or {}
    try:
        inner_mm = float(body.get("inner_mm"))
        outer_mm = float(body.get("outer_mm"))
    except (TypeError, ValueError):
        return jsonify({"detail": "内缘、外缘必须是数字"}), 400
    if inner_mm <= 0:
        return jsonify({"detail": "内缘必须大于 0"}), 400
    if outer_mm <= inner_mm:
        return jsonify({"detail": "外缘必须大于内缘"}), 400
    note = (body.get("note") or "").strip() or None
    db = SessionLocal()
    try:
        band = BandConfig(
            inner_mm=inner_mm,
            outer_mm=outer_mm,
            changed_by=g.user["username"],
            changed_at=datetime.now(timezone.utc),
            note=note,
        )
        db.add(band)
        db.commit()
        db.refresh(band)
        return jsonify(band_dict(band)), 201
    finally:
        db.close()
