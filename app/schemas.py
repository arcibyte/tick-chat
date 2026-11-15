from pydantic import BaseModel, ConfigDict, Field


class FederatedMessage(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str
    from_: str = Field(alias="from")
    origin: str
    lamport: int
    sent_at: str
    body: str


class LocalSendRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    username: str
    body: str


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    username: str
