# Маршрути приймають HTTP-запити, валідовують дані та делегують роботу сервісам.

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.docs import (
    AUTH_REQUIRED_RESPONSE,
    PERMISSION_DENIED_RESPONSE,
    SCHEDULE_ATTENDEE_EXAMPLE,
    SCHEDULE_COMPLETE_EXAMPLE,
    SCHEDULE_EXAMPLE,
    VALIDATION_ERROR_RESPONSE,
    bad_request_response,
    merge_responses,
    no_content_response,
    not_found_response,
    response_example,
)
from app.api.deps import get_current_user, get_db_session, require_roles
from app.models.user import User, UserRole
from app.schemas.schedule import (
    RecurrenceScope,
    ScheduleAttendeeRead,
    ScheduleCompleteRequest,
    ScheduleCreate,
    ScheduleRead,
    ScheduleUpdate,
)
from app.services.schedule_service import ScheduleService

router = APIRouter()


# Створює schedule.
@router.post(
    "",
    response_model=ScheduleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити заняття або recurring-серію",
    description=(
        "Створює одиничне заняття або одразу всю recurring-серію, якщо в тілі передано "
        "блок recurrence. Доступно адміністраторам та власникам клубу."
    ),
    responses=merge_responses(
        {201: response_example("Заняття або перший occurrence серії успішно створено.", SCHEDULE_EXAMPLE)},
        bad_request_response(
            "Некоректний часовий інтервал, ціна або recurrence-правило.",
            "Для платного заняття потрібно вказати додаткову вартість",
        ),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def create_schedule(
    payload: ScheduleCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleRead:
    service = ScheduleService(db)
    schedule = await service.create_schedule(payload, current_user)
    return ScheduleRead.model_validate(schedule)


# Повертає список schedules.
@router.get(
    "",
    response_model=list[ScheduleRead],
    summary="Отримати розклад занять",
    description=(
        "Повертає список занять у вказаному часовому вікні. Якщо фільтри не задані, "
        "API повертає весь доступний materialized розклад."
    ),
    responses=merge_responses(
        {200: response_example("Список занять у вибраному діапазоні.", [SCHEDULE_EXAMPLE])},
        AUTH_REQUIRED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def list_schedules(
    start_datetime: datetime | None = Query(
        default=None,
        alias="from",
        description="Початок часової вибірки в ISO 8601.",
        examples=["2026-04-01T00:00:00Z"],
    ),
    end_datetime: datetime | None = Query(
        default=None,
        alias="to",
        description="Кінець часової вибірки в ISO 8601.",
        examples=["2026-04-07T23:59:59Z"],
    ),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ScheduleRead]:
    service = ScheduleService(db)
    schedules = await service.list_schedules(start_datetime, end_datetime)
    return [ScheduleRead.model_validate(item) for item in schedules]


# Обслуговує сценарій my classes.
@router.get(
    "/my-classes",
    response_model=list[ScheduleRead],
    summary="Отримати заняття поточного тренера",
    description=(
        "Повертає лише ті заняття, де поточний користувач призначений тренером. "
        "Маршрут орієнтований на тренерський робочий кабінет."
    ),
    responses=merge_responses(
        {200: response_example("Список занять поточного тренера.", [SCHEDULE_EXAMPLE])},
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def my_classes(
    start_datetime: datetime | None = Query(
        default=None,
        alias="from",
        description="Початок часової вибірки в ISO 8601.",
        examples=["2026-04-01T00:00:00Z"],
    ),
    end_datetime: datetime | None = Query(
        default=None,
        alias="to",
        description="Кінець часової вибірки в ISO 8601.",
        examples=["2026-04-07T23:59:59Z"],
    ),
    current_user: User = Depends(require_roles(UserRole.TRAINER)),
    db: AsyncSession = Depends(get_db_session),
) -> list[ScheduleRead]:
    service = ScheduleService(db)
    schedules = await service.list_my_classes(current_user.id, start_datetime, end_datetime)
    return [ScheduleRead.model_validate(item) for item in schedules]


# Обслуговує сценарій attendees.
@router.get(
    "/{class_id}/attendees",
    response_model=list[ScheduleAttendeeRead],
    summary="Переглянути відвідувачів заняття",
    description=(
        "Повертає список клієнтів, записаних на конкретне заняття. Доступ мають "
        "адміністрація клубу та тренер, який веде це заняття."
    ),
    responses=merge_responses(
        {200: response_example("Список відвідувачів заняття.", [SCHEDULE_ATTENDEE_EXAMPLE])},
        not_found_response("Заняття не знайдено.", "Class not found"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def attendees(
    class_id: str = Path(
        description="Ідентифікатор заняття, для якого треба показати список відвідувачів.",
        examples=["class-2026-04-01-0800"],
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ScheduleAttendeeRead]:
    service = ScheduleService(db)
    attendees = await service.list_attendees(class_id, current_user)
    return [ScheduleAttendeeRead.model_validate(item) for item in attendees]

# Дає тренеру або менеджменту зафіксувати завершення заняття й службовий коментар.
@router.patch(
    "/{class_id}/complete",
    response_model=ScheduleRead,
    summary="Підтвердити проведення заняття",
    description=(
        "Фіксує, що заняття фактично відбулося, зберігає службовий коментар та "
        "користувача, який підтвердив завершення."
    ),
    responses=merge_responses(
        {
            200: response_example(
                "Заняття позначено як завершене.",
                {
                    **SCHEDULE_EXAMPLE,
                    "completed_at": "2026-04-01T09:05:00Z",
                    "completion_comment": SCHEDULE_COMPLETE_EXAMPLE["comment"],
                    "completed_by": SCHEDULE_EXAMPLE["trainer"],
                },
            )
        },
        bad_request_response(
            "Заняття ще не завершилось або його не можна позначити завершеним.",
            "Заняття можна підтвердити лише після завершення",
        ),
        not_found_response("Заняття не знайдено.", "Class not found"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def complete_schedule(
    class_id: Annotated[
        str,
        Path(
            description="Ідентифікатор заняття, яке треба позначити завершеним.",
            examples=["class-2026-04-01-0800"],
        ),
    ],
    payload: ScheduleCompleteRequest,
    current_user: User = Depends(require_roles(UserRole.TRAINER, UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleRead:
    service = ScheduleService(db)
    schedule = await service.confirm_completion(class_id, payload, current_user)
    return ScheduleRead.model_validate(schedule)


# Оновлює schedule.
@router.patch(
    "/{class_id}",
    response_model=ScheduleRead,
    summary="Оновити заняття або recurring-серію",
    description=(
        "Оновлює окреме заняття, усі наступні occurrence або всю серію залежно від поля "
        "`scope` у тілі запиту."
    ),
    responses=merge_responses(
        {
            200: response_example(
                "Зміни до розкладу успішно застосовано.",
                {
                    **SCHEDULE_EXAMPLE,
                    "title": "Morning Flow Advanced",
                    "start_time": "2026-04-03T08:30:00Z",
                    "end_time": "2026-04-03T09:30:00Z",
                    "capacity": 18,
                },
            )
        },
        bad_request_response(
            "Параметри оновлення суперечать бізнес-правилам розкладу або recurring-серії.",
            "Recurring-правило можна змінювати лише для scope following або series",
        ),
        not_found_response("Заняття не знайдено.", "Class not found"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def update_schedule(
    class_id: Annotated[
        str,
        Path(
            description="Ідентифікатор заняття, яке треба змінити.",
            examples=["class-2026-04-01-0800"],
        ),
    ],
    payload: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleRead:
    service = ScheduleService(db)
    schedule = await service.update_schedule(class_id, payload, current_user)
    return ScheduleRead.model_validate(schedule)


# Видаляє schedule.
@router.delete(
    "/{class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити заняття або серію",
    description=(
        "Видаляє окремий occurrence, усі наступні occurrence або всю recurring-серію залежно "
        "від параметра `scope`."
    ),
    responses=merge_responses(
        {204: no_content_response("Розклад успішно оновлено: вибраний scope видалено.")},
        bad_request_response(
            "Заняття або серію не можна видалити через confirmed bookings чи некоректний scope.",
            "Не можна видалити заняття, поки в ньому є підтверджені записи",
        ),
        not_found_response("Заняття не знайдено.", "Class not found"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def delete_schedule(
    class_id: str = Path(
        description="Ідентифікатор заняття або одного occurrence в серії.",
        examples=["class-2026-04-01-0800"],
    ),
    scope: RecurrenceScope = Query(
        default=RecurrenceScope.OCCURRENCE,
        description="Обсяг видалення: лише одне заняття, усі наступні occurrence або вся серія.",
        examples=["OCCURRENCE"],
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    service = ScheduleService(db)
    await service.delete_schedule(class_id, current_user, scope)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
