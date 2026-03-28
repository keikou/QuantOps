from __future__ import annotations

from contextvars import ContextVar, Token


request_id_var: ContextVar[str | None] = ContextVar("quantops_request_id", default=None)
request_path_var: ContextVar[str | None] = ContextVar("quantops_request_path", default=None)
trace_id_var: ContextVar[str | None] = ContextVar("quantops_trace_id", default=None)
session_id_var: ContextVar[str | None] = ContextVar("quantops_session_id", default=None)
page_path_var: ContextVar[str | None] = ContextVar("quantops_page_path", default=None)


def bind_request_context(
    request_id: str,
    request_path: str,
    trace_id: str | None = None,
    session_id: str | None = None,
    page_path: str | None = None,
) -> tuple[Token, Token, Token, Token, Token]:
    return (
        request_id_var.set(request_id),
        request_path_var.set(request_path),
        trace_id_var.set(trace_id),
        session_id_var.set(session_id),
        page_path_var.set(page_path),
    )


def reset_request_context(tokens: tuple[Token, Token, Token, Token, Token]) -> None:
    request_id_var.reset(tokens[0])
    request_path_var.reset(tokens[1])
    trace_id_var.reset(tokens[2])
    session_id_var.reset(tokens[3])
    page_path_var.reset(tokens[4])


def current_request_id() -> str | None:
    return request_id_var.get()


def current_request_path() -> str | None:
    return request_path_var.get()


def current_trace_id() -> str | None:
    return trace_id_var.get()


def current_session_id() -> str | None:
    return session_id_var.get()


def current_page_path() -> str | None:
    return page_path_var.get()
