from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    message: str


class PaginationResponse(BaseModel):
    total: int


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
