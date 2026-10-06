import os
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DSN = os.environ.get("DATABASE_URL", "postgresql://app:app@localhost:54401/tunnelconv")
engine = create_engine(DSN, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class BandConfig(Base):
    """琥珀近阈带配置；每次改带追加一行，最新一行是当前带，全部行即改带履历。"""

    __tablename__ = "band_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inner_mm: Mapped[float] = mapped_column(Float, nullable=False)  # 内缘：合格带 ±inner
    outer_mm: Mapped[float] = mapped_column(Float, nullable=False)  # 外缘：超出才算超限
    changed_by: Mapped[str] = mapped_column(String, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(String, nullable=True)


class ConvergenceLog(Base):
    __tablename__ = "convergence_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chainage: Mapped[str] = mapped_column(String, nullable=False)
    delta_mm: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    verdict: Mapped[str | None] = mapped_column(String, nullable=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    # 领走时快照的琥珀界：改带不追溯，已领走的单据仍按此界显示
    band_inner_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    band_outer_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


def row_dict(row: ConvergenceLog) -> dict:
    return {
        "id": row.id,
        "chainage": row.chainage,
        "delta_mm": row.delta_mm,
        "status": row.status,
        "verdict": row.verdict,
        "reason": row.reason,
        "band_inner_mm": row.band_inner_mm,
        "band_outer_mm": row.band_outer_mm,
        "created_by": row.created_by,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "processed_at": row.processed_at.isoformat() if row.processed_at else None,
    }


def band_dict(band: BandConfig) -> dict:
    return {
        "id": band.id,
        "inner_mm": band.inner_mm,
        "outer_mm": band.outer_mm,
        "changed_by": band.changed_by,
        "changed_at": band.changed_at.isoformat() if band.changed_at else None,
        "note": band.note,
    }
