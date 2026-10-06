"""/api/band：读取、改带履历、监理权限与入参校验。"""


def test_anonymous_get_band_401(client):
    assert client.get("/api/band").status_code == 401
    assert client.get("/api/band/history").status_code == 401
    assert client.put("/api/band", json={"inner_mm": 1, "outer_mm": 2}).status_code == 401


def test_default_band_and_init_history(client, auth):
    h = auth("inspector")
    band = client.get("/api/band", headers=h).get_json()
    assert band["inner_mm"] == 3.0
    assert band["outer_mm"] == 3.4

    history = client.get("/api/band/history", headers=h).get_json()
    assert history[0]["note"] == "系统初始化"
    assert history[0]["new_inner_mm"] == 3.0
    assert history[0]["old_inner_mm"] is None


def test_monitor_can_change_band_and_history_appended(client, auth):
    h = auth("monitor")
    res = client.put(
        "/api/band",
        headers=h,
        json={"inner_mm": 3.5, "outer_mm": 4.0, "note": "二期收紧"},
    )
    assert res.status_code == 200
    assert res.get_json()["outer_mm"] == 4.0

    band = client.get("/api/band", headers=h).get_json()
    assert (band["inner_mm"], band["outer_mm"]) == (3.5, 4.0)
    assert band["updated_by"] == "monitor"

    history = client.get("/api/band/history", headers=h).get_json()
    assert history[0]["new_inner_mm"] == 3.5
    assert history[0]["old_inner_mm"] == 3.0
    assert history[0]["new_outer_mm"] == 4.0
    assert history[0]["old_outer_mm"] == 3.4
    assert history[0]["changed_by"] == "monitor"
    assert history[0]["note"] == "二期收紧"


def test_non_monitor_cannot_change_band(client, auth):
    history_before = client.get("/api/band/history", headers=auth("inspector")).get_json()

    assert client.put(
        "/api/band", headers=auth("inspector"), json={"inner_mm": 2, "outer_mm": 4}
    ).status_code == 403
    assert client.put(
        "/api/band", headers=auth("surveyor"), json={"inner_mm": 2, "outer_mm": 4}
    ).status_code == 403

    history_after = client.get("/api/band/history", headers=auth("inspector")).get_json()
    assert len(history_after) == len(history_before)


def test_invalid_band_payloads(client, auth):
    h = auth("monitor")
    bad_bodies = [
        {"inner_mm": 4.0, "outer_mm": 3.0},   # 内缘 >= 外缘
        {"inner_mm": 3.4, "outer_mm": 3.4},   # 相等
        {"inner_mm": -1, "outer_mm": 3.4},    # 负
        {"inner_mm": "x", "outer_mm": 3.4},   # 非数字
        {"inner_mm": None, "outer_mm": None},
        {"inner_mm": 3.0, "outer_mm": 3.4},   # 与当前相同（无变化）
    ]
    for body in bad_bodies:
        res = client.put("/api/band", headers=h, json=body)
        assert res.status_code == 400, body
