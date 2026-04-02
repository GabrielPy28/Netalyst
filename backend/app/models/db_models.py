from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_brand_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    criteria: Mapped[list[Criterion]] = relationship(
        back_populates="program",
        order_by="Criterion.orden",
        cascade="all, delete-orphan",
    )


class Criterion(Base):
    __tablename__ = "criteria"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    objetivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_slug: Mapped[str | None] = mapped_column(Text, nullable=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    program: Mapped[Program] = relationship(back_populates="criteria")
    steps: Mapped[list[CriterionStep]] = relationship(
        back_populates="criterion",
        order_by="CriterionStep.paso_num",
        cascade="all, delete-orphan",
    )


class CriterionStep(Base):
    __tablename__ = "criterion_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    criterion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("criteria.id", ondelete="CASCADE"),
        nullable=False,
    )
    paso_num: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    definicion: Mapped[str | None] = mapped_column(Text, nullable=True)
    funcion_a_ejecutar: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    criterion: Mapped[Criterion] = relationship(back_populates="steps")
