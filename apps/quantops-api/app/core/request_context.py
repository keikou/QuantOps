from __future__ import annotations

from contextvars import ContextVar, Token


request_id_var: ContextVar[str | None] = ContextVar("quantops_request_id", default=None)
request_path_var: ContextVar[str | None] = ContextVar("quantops_request_path", default=None)


def bind_request_context(request_id: str, request_path: str) -> tuple[Token, Token]:
    return request_id_var.set(request_id), request_path_var.set(request_path)


def reset_request_context(tokens: tuple[Token, Token]) -> None:
    request_id_var.reset(tokens[0])
    request_path_var.reset(tokens[1])


def current_request_id() -> str | None:
    return request_id_var.get()


def current_request_path() -> str | None:
    return request_path_var.get()
