from __future__ import annotations

from contextvars import ContextVar, Token


request_id_var: ContextVar[str | None] = ContextVar("v12_request_id", default=None)
trace_id_var: ContextVar[str | None] = ContextVar("v12_trace_id", default=None)
session_id_var: ContextVar[str | None] = ContextVar("v12_session_id", default=None)
page_path_var: ContextVar[str | None] = ContextVar("v12_page_path", default=None)
request_path_var: ContextVar[str | None] = ContextVar("v12_request_path", default=None)


def bind_request_context(
    *,
    request_id: str,
    trace_id: str | None,
    session_id: str | None,
    page_path: str | None,
    request_path: str,
) -> tuple[Token, Token, Token, Token, Token]:
    return (
        request_id_var.set(request_id),
        trace_id_var.set(trace_id),
        session_id_var.set(session_id),
        page_path_var.set(page_path),
        request_path_var.set(request_path),
    )


def reset_request_context(tokens: tuple[Token, Token, Token, Token, Token]) -> None:
    request_id_var.reset(tokens[0])
    trace_id_var.reset(tokens[1])
    session_id_var.reset(tokens[2])
    page_path_var.reset(tokens[3])
    request_path_var.reset(tokens[4])
