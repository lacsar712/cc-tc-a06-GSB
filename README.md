# 隧道收敛测缝台

测量员登记里程桩号与收敛毫米值。接口进程内后台线程认领待判行（不另起 worker 容器），按三档判定带出结论：

| `|Δ|` 范围 | 结论 | 颜色 | 能否进队 |
|---|---|---|---|
| `|Δ| ≤ 内缘`（默认 3.0 mm） | 合格 | 绿 | 可 |
| `内缘 < |Δ| ≤ 外缘`（默认外缘 3.4 mm） | **近阈（琥珀带）** | 琥珀橙 | 可，标近阈 |
| `|Δ| > 外缘` | 超限 | 红 | 可提交，标超限 |

内缘/外缘由**监理**在"琥珀专页"调整。每行单据在**提交时**快照当时的内缘/外缘，之后改带只影响之后新提交的单；已提交（含仍在排队）和已认领的单据始终按自己快照的界判定。升级前的历史行无快照，回退默认 3.0/3.4。

页面是 Svelte：总表、单据详情（点编号进入）、琥珀专页（当前内缘/外缘、样例色、改带履历）共用同一套判定界与颜色文字。

## 技术栈

- 后端：Flask、Gunicorn（单 worker，认领线程在进程内）、SQLAlchemy、进程内认领线程
- 前端：Svelte、Vite、nginx 反代 `/api`
- 数据库：PostgreSQL 16（启动时 `create_all` + 幂等 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 自动升级老库）

## 端口

| 服务 | 地址 |
|------|------|
| 页面 | http://localhost:3201 |
| 接口 | http://localhost:8201 |
| PostgreSQL | localhost:54401（库名 `tunnelconv`） |

## 账号

| 用户 | 密码 | 角色 | 权限 |
|------|------|------|------|
| surveyor | surv123456 | 测量员（writer） | 提交读数 |
| inspector | insp123456 | 巡检员（reader） | 只读，不能改带 |
| monitor | mon123456 | 监理（monitor） | 只读 + 唯一可修改判定带、查改带履历 |

## 启动

```bash
docker compose up --build
```

健康检查：`GET http://localhost:8201/api/health`

## 判定带接口

- `GET /api/band`（登录即可）：当前 `inner_mm` / `outer_mm` / 更新人 / 更新时间。
- `GET /api/band/history`（登录即可）：改带履历，最新在前；首行为系统初始化。
- `PUT /api/band`（**仅 monitor**）：请求体 `{"inner_mm": 3.0, "outer_mm": 3.4, "note": "可选备注"}`。校验：均为有限非负数且 `内缘 < 外缘`，新旧不能完全相同；非法返回 400，非监理返回 403。

## 种子

| 桩号 | 收敛 | 结论 |
|------|------|------|
| K12+180 | 1.2 mm | 合格 |
| K18+040 | 5.6 mm | 超限 |

## 测试

```bash
# 后端（pytest；测试自动使用 sqlite 并关闭认领线程，无需 Postgres）
cd backend
pip install -r requirements-dev.txt
python -m pytest -q

# 前端（node 内置 test runner，无额外依赖）
cd frontend
npm install
npm test
```

覆盖：三档边界（3.0 合格 / 3.2、3.4 近阈 / 3.8 超限，含负值对称）、改带权限与履历、快照语义（改带前后提交的两单各按各的界认领）、历史空快照回退。
