from pydantic import BaseModel


class Pagination(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
