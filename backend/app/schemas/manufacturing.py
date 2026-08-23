from datetime import date

from pydantic import BaseModel, Field


class ProductionRecordCreate(BaseModel):
    date: date
    production_line: str = Field(min_length=1, max_length=100)
    clinker_output: float = Field(ge=0)
    cement_output: float = Field(ge=0)
    planned_output: float = Field(ge=0)
    completion_rate: float = Field(ge=0, le=1000)
    running_hours: float = Field(ge=0, le=24)
    downtime_hours: float = Field(ge=0, le=24)


class EquipmentRecordCreate(BaseModel):
    date: date
    equipment_name: str = Field(min_length=1, max_length=100)
    status: str = Field(min_length=1, max_length=30)
    running_hours: float = Field(ge=0, le=24)
    fault_count: int = Field(ge=0)
    temperature: float = Field(ge=-100, le=1000)
    vibration: float = Field(ge=0, le=1000)


class EnergyRecordCreate(BaseModel):
    date: date
    production_line: str = Field(min_length=1, max_length=100)
    electricity_consumption: float = Field(ge=0)
    coal_consumption: float = Field(ge=0)
    unit_energy_consumption: float = Field(ge=0)
