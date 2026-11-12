import re

from datetime import datetime
from typing import Annotated, Optional
from fastapi import FastAPI, Header, Request, HTTPException, status, Response
from pydantic import BaseModel, Field, field_validator


app = FastAPI()

# Exceptions
class HeaderError(Exception):
    def __init__(self, message: str):
        self._message = message
        super().__init__(self._message)

    @property
    def message(self) -> str:
        return self._message


class EmptyHeaderError(HeaderError):
    ...


class InvalidAcceptLanguageError(HeaderError):
    ...


# Schemes
class CommonHeaders(BaseModel):
    user_agent: Annotated[Optional[str], Field(..., alias="User-Agent")]
    accept_language: Annotated[Optional[str], Field(..., alias="Accept-Language")]

    @field_validator("user_agent", "accept_language")
    @staticmethod
    def _validate_empty_value(value: Optional[str]) -> str:

        if not value:
            raise EmptyHeaderError("Отсуствует значение в заголовке User-Agent")

        return value

    @field_validator("accept_language")
    @staticmethod
    def _validate_format_accept_language(value: str) -> str:

        pattern = r"(?i:(?:\*|[a-z\-]{2,5})(?:;q=\d\.\d)?,)+(?:\*|[a-z\-]{2,5})(?:;q=\d\.\d)?"

        if not re.fullmatch(pattern, value):
            raise InvalidAcceptLanguageError("Неверный формат значения в заголовке Accept-Language")

        return value


class ResponseScheme(BaseModel):
    message: str
    common_headers: Optional[CommonHeaders]


# Exception Handler
@app.exception_handler(EmptyHeaderError)
def empty_header_exceptiom_handler(request: Request, exc: EmptyHeaderError):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=exc.message
    )


@app.exception_handler(InvalidAcceptLanguageError)
def invalid_accept_language_exception_handler(request: Request, exc: InvalidAcceptLanguageError):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=exc.message
    )


# Endpoints
@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Hello World!"
    }


Headers = Annotated[Optional[CommonHeaders], Header()]


@app.get("/headers", response_model=CommonHeaders)
def headers_endpoint(headers: Headers = None):
    return headers


@app.get("/info", response_model=ResponseScheme)
def info_endpoint(response: Response, headers: Headers = None):

    response.headers["X-Server-Time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    return ResponseScheme(
        message="Добро пожаловать! Ваши заголовки успешно обработаны.",
        common_headers=headers
    )
