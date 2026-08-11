"""Acumulador incremental de contratações do PNCP.

O PNCP não expõe nenhum total agregado pronto — só registros
individuais paginados. Para nunca precisar consultar o PNCP em tempo
real por requisição de usuário, o IFB acumula os totais localmente: a
cada sync, busca só os registros publicados desde a última execução
(`PncpSyncCheckpoint`), soma o valor por ano/UF, e **soma ao total já
acumulado** em `PncpContratacaoTotal` — nunca refaz a soma do histórico
inteiro do zero.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.common import uuid_pk


class PncpSyncCheckpoint(Base):
    """Até que data (`ultima_data_final`) já foram buscados e somados os
    registros de uma modalidade de contratação — o próximo sync busca só
    a partir daí."""

    __tablename__ = "pncp_sync_checkpoints"

    modalidade_codigo: Mapped[int] = mapped_column(Integer, primary_key=True)
    ultima_data_final: Mapped[date] = mapped_column(Date, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PncpContratacaoTotal(Base):
    """Total acumulado (soma incremental, nunca recalculada do zero) de
    valorTotalEstimado das contratações publicadas no PNCP, por ano de
    publicação, UF e modalidade."""

    __tablename__ = "pncp_contratacao_totals"
    __table_args__ = (UniqueConstraint("ano", "uf", "modalidade_codigo", name="uq_pncp_total_ano_uf_modalidade"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    modalidade_codigo: Mapped[int] = mapped_column(Integer, nullable=False)
    valor_total: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
