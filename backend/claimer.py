"""进程内认领：同一 Flask 进程后台线程抢 pending，不另起容器。"""
import threading
import time
from datetime import datetime, timezone

from models import ConvergenceLog, SessionLocal
from rules import DEFAULT_INNER_MM, DEFAULT_OUTER_MM, judge

_stop = threading.Event()


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
        # 只按本单提交时快照的界判定，不读实时配置；历史空快照回退默认界。
        inner = row.band_inner_mm if row.band_inner_mm is not None else DEFAULT_INNER_MM
        outer = row.band_outer_mm if row.band_outer_mm is not None else DEFAULT_OUTER_MM
        verdict, reason = judge(float(row.delta_mm), inner, outer)
        row.status = "done"
        row.verdict = verdict
        row.reason = reason
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
