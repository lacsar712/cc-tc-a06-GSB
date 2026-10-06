"""核心语义：改带只影响之后新提交的单；认领按行快照判定。"""
from claimer import claim_once
from models import ConvergenceLog, SessionLocal


def _pending_count(db):
    return db.query(ConvergenceLog).filter(ConvergenceLog.status == "pending").count()


def _get(db, id_):
    return db.get(ConvergenceLog, id_)


def test_snapshot_at_submit_then_band_change(client, auth):
    writer = auth("surveyor")
    monitor = auth("monitor")

    # 1) 默认 3.0/3.4 下提交 A=3.2（近阈），响应即带快照
    a = client.post("/api/logs", headers=writer, json={"chainage": "K1", "delta_mm": 3.2})
    assert a.status_code == 201
    a_json = a.get_json()
    assert a_json["status"] == "pending"
    assert a_json["verdict"] is None
    assert (a_json["band_inner_mm"], a_json["band_outer_mm"]) == (3.0, 3.4)
    a_id = a_json["id"]

    # 2) 监理改带 3.5/4.0
    assert client.put(
        "/api/band", headers=monitor, json={"inner_mm": 3.5, "outer_mm": 4.0}
    ).status_code == 200

    # 3) 改带后提交 B=3.7：旧带下应超限，新带快照下应近阈
    b = client.post("/api/logs", headers=writer, json={"chainage": "K2", "delta_mm": 3.7})
    assert b.status_code == 201
    b_json = b.get_json()
    assert (b_json["band_inner_mm"], b_json["band_outer_mm"]) == (3.5, 4.0)
    b_id = b_json["id"]

    # 4) 认领两次（按 id 最老优先，只处理 pending；种子行已是 done 不影响）
    assert claim_once() is True
    assert claim_once() is True

    db = SessionLocal()
    try:
        row_a, row_b = _get(db, a_id), _get(db, b_id)
        # A 按提交时旧界 3.0/3.4：3.2 近阈（若误读新界 3.5/4.0 会变成合格）
        assert row_a.status == "done"
        assert row_a.verdict == "近阈"
        assert "±3" in row_a.reason and "±3.4" in row_a.reason
        # B 按新界 3.5/4.0：3.7 近阈（若误用旧界会变成超限）
        assert row_b.verdict == "近阈"
        assert "±3.5" in row_b.reason and "±4" in row_b.reason
        assert _pending_count(db) == 0
    finally:
        db.close()


def test_acceptance_values_after_claim(client, auth):
    """题面验收：默认带下 3.2 近阈、3.8 超限（经真实提交+认链路）。"""
    writer = auth("surveyor")
    ids = {}
    for chainage, delta in (("K32", 3.2), ("K38", 3.8), ("K30", 3.0), ("K34", 3.4)):
        res = client.post("/api/logs", headers=writer, json={"chainage": chainage, "delta_mm": delta})
        ids[delta] = res.get_json()["id"]

    for _ in range(4):
        claim_once()

    db = SessionLocal()
    try:
        assert _get(db, ids[3.2]).verdict == "近阈"
        assert _get(db, ids[3.8]).verdict == "超限"
        assert _get(db, ids[3.0]).verdict == "合格"
        assert _get(db, ids[3.4]).verdict == "近阈"
    finally:
        db.close()


def test_legacy_null_snapshot_falls_back_to_defaults():
    """升级前老行无快照：认领不崩，回退默认 3.0/3.4。"""
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        row = ConvergenceLog(
            chainage="K-old",
            delta_mm=5.6,
            status="pending",
            band_inner_mm=None,
            band_outer_mm=None,
            created_by="surveyor",
            created_at=datetime.now(timezone.utc),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        old_id = row.id
    finally:
        db.close()

    assert claim_once() is True

    db = SessionLocal()
    try:
        done = _get(db, old_id)
        assert done.status == "done"
        assert done.verdict == "超限"
    finally:
        db.close()
