from datetime import date

from sqlalchemy import Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.user import Base


class ProductionRecord(Base):
    __tablename__ = "production_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    production_line: Mapped[str] = mapped_column(String(100), index=True)
    clinker_output: Mapped[float] = mapped_column(Numeric(12, 2))
    cement_output: Mapped[float] = mapped_column(Numeric(12, 2))
    planned_output: Mapped[float] = mapped_column(Numeric(12, 2))
    completion_rate: Mapped[float] = mapped_column(Numeric(7, 2))
    running_hours: Mapped[float] = mapped_column(Numeric(7, 2))
    downtime_hours: Mapped[float] = mapped_column(Numeric(7, 2))


class EquipmentRecord(Base):
    __tablename__ = "equipment_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    equipment_name: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    running_hours: Mapped[float] = mapped_column(Numeric(7, 2))
    fault_count: Mapped[int] = mapped_column(Integer, default=0)
    temperature: Mapped[float] = mapped_column(Numeric(7, 2))
    vibration: Mapped[float] = mapped_column(Numeric(7, 3))


class EnergyRecord(Base):
    __tablename__ = "energy_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    production_line: Mapped[str] = mapped_column(String(100), index=True)
    electricity_consumption: Mapped[float] = mapped_column(Numeric(12, 2))
    coal_consumption: Mapped[float] = mapped_column(Numeric(12, 2))
    unit_energy_consumption: Mapped[float] = mapped_column(Numeric(12, 2))
