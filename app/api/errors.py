import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_response(
    request: Request, status: int, code: str, message: str, field: str | None = None
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "field": field,
                "request_id": request_id,
            }
        },
        headers={"Cache-Control": "no-store"},
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = "RESOURCE_NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return error_response(request, exc.status_code, code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        field = str(first.get("loc", [None])[-1]) if first.get("loc") else None
        return error_response(
            request,
            422,
            "VALIDATION_ERROR",
            str(first.get("msg", "Request validation failed")),
            field,
        )

    @app.exception_handler(Exception)
    async def unexpected_handler(request: Request, exc: Exception) -> JSONResponse:
        return error_response(
            request, 500, "INTERNAL_ERROR", "An unexpected error occurred."
        )
