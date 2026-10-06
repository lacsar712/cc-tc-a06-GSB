"""pytest 全局配置：必须在导入 api/models 之前定好库与认领线程开关。"""
import os
import pathlib
import sys

_BACKEND = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))

_DB = _BACKEND / "t_test.db"
if _DB.exists():
    _DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_DB}"
os.environ["CLAIMER_ENABLED"] = "0"

import pytest  # noqa: E402

import api  # noqa: E402  导入即执行 seed()，建好 sqlite 表与默认判定带
from models import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    """每个用例重建表并重新 seed，保证判定带/履历/单据互不干扰。"""
    Base.metadata.drop_all(engine)
    api.seed()
    yield


PASSWORDS = {
    "surveyor": "surv123456",
    "inspector": "insp123456",
    "monitor": "mon123456",
}


@pytest.fixture
def client():
    return api.app.test_client()


@pytest.fixture
def auth(client):
    """返回给请求加 Authorization 头的小工具。"""

    def headers(user):
        res = client.post(
            "/api/auth/login",
            json={"username": user, "password": PASSWORDS[user]},
        )
        token = res.get_json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return headers
