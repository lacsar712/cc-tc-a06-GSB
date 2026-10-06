"""进程内认领：同一 Flask 进程后台线程抢 pending，不另起容器。领走时快照当前琥珀界。"""
import threading
import time
from datetime import datetime, timezone

from models import BandConfig, ConvergenceLog, SessionLocal
from rules import DEFAULT_INNER_MM, DEFAULT_OUTER_MM, judge

_stop = threading.Event()


def current_band(db) -> tuple[float, float]:
    band = db.query(BandConfig).order_by(BandConfig.id.desc()).first()
    if band is None:
        return DEFAULT_INNER_MM, DEFAULT_OUTER_MM
    return band.inner_mm, band.outer_mm


def claim_once() -> bool:
    db = SessionLocal()
    try:
        row = (
            db.query(ConvergenceLog)
            .filter(ConvergenceLog.status == "pending")
            .order_by(ConvergenceLog.id)
            .with_for_update(skip_locked=True)
            .first()
        )
        if row is None:
            db.commit()
            return False
        inner_mm, outer_mm = current_band(db)
        verdict, reason = judge(float(row.delta_mm), inner_mm, outer_mm)
        row.status = "done"
        row.verdict = verdict
        row.reason = reason
        row.band_inner_mm = inner_mm
        row.band_outer_mm = outer_mm
        row.processed_at = datetime.now(timezone.utc)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def loop():
    while not _stop.is_set():
        try:
            if claim_once():
                time.sleep(0.4)
            else:
                time.sleep(1.0)
        except Exception as exc:
            print(f"claimer error: {exc}", flush=True)
            time.sleep(1.0)


def start():
    t = threading.Thread(target=loop, name="convergence-claimer", daemon=True)
    t.start()
