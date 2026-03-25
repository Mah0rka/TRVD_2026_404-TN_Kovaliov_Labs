# Маршрути приймають HTTP-запити, валідовують дані та делегують роботу сервісам.

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_roles
from app.models.user import User, UserRole
from app.schemas.schedule import (
    ScheduleAttendeeRead,
    ScheduleCompleteRequest,
    ScheduleCreate,
    ScheduleRead,
    ScheduleUpdate,
)
from app.services.schedule_service import ScheduleService

router = APIRouter()


# Створює schedule.
@router.post("", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    payload: ScheduleCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleRead:
    service = ScheduleService(db)
    schedule = await service.create_schedule(payload, current_user)
    return ScheduleRead.model_validate(schedule)


# Повертає список schedules.
@router.get("", response_model=list[ScheduleRead])
async def list_schedules(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ScheduleRead]:
    service = ScheduleService(db)
    schedules = await service.list_schedules()
    return [ScheduleRead.model_validate(item) for item in schedules]


# Обслуговує сценарій my classes.
@router.get("/my-classes", response_model=list[ScheduleRead])
async def my_classes(
    current_user: User = Depends(require_roles(UserRole.TRAINER)),
    db: AsyncSession = Depends(get_db_session),
) -> list[ScheduleRead]:
    service = ScheduleService(db)
    schedules = await service.list_my_classes(current_user.id)
    return [ScheduleRead.model_validate(item) for item in schedules]


# Обслуговує сценарій attendees.
@router.get("/{class_id}/attendees", response_model=list[ScheduleAttendeeRead])
async def attendees(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ScheduleAttendeeRead]:
    service = ScheduleService(db)
    attendees = await service.list_attendees(class_id, current_user)
    return [ScheduleAttendeeRead.model_validate(item) for item in attendees]


@router.patch("/{class_id}/complete", response_model=ScheduleRead)
async def complete_schedule(
    class_id: str,
    payload: ScheduleCompleteRequest,
    current_user: User = Depends(require_roles(UserRole.TRAINER, UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleRead:
    service = ScheduleService(db)
    schedule = await service.confirm_completion(class_id, payload, current_user)
    return ScheduleRead.model_validate(schedule)


# Оновлює schedule.
@router.patch("/{class_id}", response_model=ScheduleRead)
async def update_schedule(
    class_id: str,
    payload: ScheduleUpdate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleRead:
    service = ScheduleService(db)
    schedule = await service.update_schedule(class_id, payload)
    return ScheduleRead.model_validate(schedule)


# Видаляє schedule.
@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    class_id: str,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    service = ScheduleService(db)
    await service.delete_schedule(class_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
