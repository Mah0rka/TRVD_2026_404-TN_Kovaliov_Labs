# Модуль зберігає спільну інфраструктурну логіку застосунку.

import logging

from app.core.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    # Обслуговує сценарій filter.
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


# Налаштовує формат логів і фільтр з ідентифікатором запиту.
def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s")
    )
    handler.addFilter(RequestIdFilter())

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
