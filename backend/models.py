import os
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DSN = os.environ.get("DATABASE_URL", "postgresql://app:app@localhost:54401/tunnelconv")
engine = create_engine(DSN, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class ConvergenceLog(Base):
    __tablename__ = "convergence_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chainage: Mapped[str] = mapped_column(String, nullable=False)
    delta_mm: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    verdict: Mapped[str | None] = mapped_column(String, nullable=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    # 提交时快照的琥珀界；升级前的历史行可能为 NULL，判定时回退默认界。
    band_inner_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    band_outer_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BandSetting(Base):
    """当前判定带，单行（id 恒为 1）。"""

    __tablename__ = "band_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inner_mm: Mapped[float] = mapped_column(Float, nullable=False)
    outer_mm: Mapped[float] = mapped_column(Float, nullable=False)
    updated_by: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BandChange(Base):
    """改带履历：每次监理改带追加一行；首行为系统初始化（old_* 为 NULL）。"""

    __tablename__ = "band_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    old_inner_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_inner_mm: Mapped[float] = mapped_column(Float, nullable=False)
    old_outer_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_outer_mm: Mapped[float] = mapped_column(Float, nullable=False)
    changed_by: Mapped[str] = mapped_column(String, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)


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


def band_dict(band: BandSetting) -> dict:
    return {
        "inner_mm": band.inner_mm,
        "outer_mm": band.outer_mm,
        "updated_by": band.updated_by,
        "updated_at": band.updated_at.isoformat() if band.updated_at else None,
    }


def band_change_dict(change: BandChange) -> dict:
    return {
        "id": change.id,
        "old_inner_mm": change.old_inner_mm,
        "new_inner_mm": change.new_inner_mm,
        "old_outer_mm": change.old_outer_mm,
        "new_outer_mm": change.new_outer_mm,
        "changed_by": change.changed_by,
        "changed_at": change.changed_at.isoformat() if change.changed_at else None,
        "note": change.note,
    }
