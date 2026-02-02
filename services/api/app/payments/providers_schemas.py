from pydantic import BaseModel


class ProviderCreate(BaseModel):
    code: str
    name: str
    enabled: bool = False
    config_json: str | None = None


class ProviderUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    config_json: str | None = None


class ProviderOut(BaseModel):
    id: int
    code: str
    name: str
    enabled: bool
    config_json: str | None = None
