# Модуль зберігає спільну інфраструктурну логіку застосунку.

from contextvars import ContextVar
from uuid import uuid4


_request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


# Зберігає request id у контексті поточного виконання.
def set_request_id(request_id: str) -> None:
    _request_id_context.set(request_id)


# Повертає request id з контексту поточного виконання.
def get_request_id() -> str:
    return _request_id_context.get()


# Генерує новий ідентифікатор запиту.
def generate_request_id() -> str:
    return str(uuid4())
