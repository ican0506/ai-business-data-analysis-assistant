from pydantic import BaseModel


class FieldMappingOverrideRequest(BaseModel):
    overrides: dict[str, str]
