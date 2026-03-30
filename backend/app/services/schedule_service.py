# Сервіс інкапсулює бізнес-правила розкладу, recurring-серій і прав доступу.

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.booking import BookingStatus
from app.models.user import User, UserRole
from app.models.workout_class import WorkoutClass
from app.models.workout_series import WorkoutSeries, WorkoutSeriesExclusion
from app.repositories.booking_repository import BookingRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.workout_series_repository import WorkoutSeriesRepository
from app.schemas.schedule import (
    RecurrenceScope,
    ScheduleCompleteRequest,
    ScheduleCreate,
    RecurrenceWeekday,
    ScheduleRecurrence,
    ScheduleUpdate,
)
from app.services.schedule_recurrence import (
    ensure_aware,
    generate_occurrence_starts,
    serialize_recurrence_rule,
    weekday_codes_for_start,
)


class ScheduleService:
    CLUB_TIMEZONE = ZoneInfo("Europe/Kiev")
    CLUB_OPEN_TIME = time(6, 0)
    CLUB_CLOSE_TIME = time(22, 0)

    # Ініціалізує внутрішній стан обʼєкта.
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ScheduleRepository(session)
        self.series_repository = WorkoutSeriesRepository(session)
        self.booking_repository = BookingRepository(session)

    # Створює schedule.
    async def create_schedule(self, payload: ScheduleCreate, current_user: User) -> WorkoutClass:
        start_time = ensure_aware(payload.start_time)
        end_time = ensure_aware(payload.end_time)
        self._validate_time_range(start_time, end_time)
        self._validate_pricing(payload.is_paid_extra, payload.extra_price)

        trainer_id = payload.trainer_id or current_user.id
        if payload.recurrence:
            series = await self._create_series_from_payload(payload, trainer_id, start_time, end_time)
            occurrences = await self._materialize_series_occurrences(series, start_boundary=start_time)
            await self.session.commit()
            if not occurrences:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Не вдалося згенерувати occurrences для recurring-серії",
                )
            created = await self.repository.get_by_id(occurrences[0].id)
            assert created is not None
            return created

        workout_class = WorkoutClass(
            title=payload.title.strip(),
            type=payload.type,
            start_time=start_time,
            end_time=end_time,
            capacity=payload.capacity,
            trainer_id=trainer_id,
            is_paid_extra=payload.is_paid_extra,
            extra_price=payload.extra_price if payload.is_paid_extra else None,
        )
        created = await self.repository.create(workout_class)
        await self.session.commit()
        refreshed = await self.repository.get_by_id(created.id)
        assert refreshed is not None
        return refreshed

    # Повертає список schedules.
    async def list_schedules(
        self,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
    ) -> list[WorkoutClass]:
        return await self.repository.list_all(
            ensure_aware(start_datetime) if start_datetime else None,
            ensure_aware(end_datetime) if end_datetime else None,
        )

    # Повертає список my classes.
    async def list_my_classes(
        self,
        trainer_id: str,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
    ) -> list[WorkoutClass]:
        return await self.repository.list_by_trainer(
            trainer_id,
            ensure_aware(start_datetime) if start_datetime else None,
            ensure_aware(end_datetime) if end_datetime else None,
        )

    # Оновлює schedule.
    async def update_schedule(self, class_id: str, payload: ScheduleUpdate, current_user: User) -> WorkoutClass:
        workout_class = await self.repository.get_by_id(class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

        self._ensure_update_access(workout_class, current_user)

        if payload.recurrence and not workout_class.series_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recurring можна додати лише під час створення нової серії",
            )

        if payload.scope == RecurrenceScope.OCCURRENCE or not workout_class.series_id:
            updated = await self._update_occurrence(workout_class, payload)
            await self.session.commit()
            refreshed = await self.repository.get_by_id(updated.id)
            assert refreshed is not None
            return refreshed

        if payload.scope == RecurrenceScope.FOLLOWING:
            updated = await self._update_following(workout_class, payload)
            await self.session.commit()
            refreshed = await self.repository.get_by_id(updated.id)
            assert refreshed is not None
            return refreshed

        updated = await self._update_series(workout_class, payload)
        await self.session.commit()
        refreshed = await self.repository.get_by_id(updated.id)
        assert refreshed is not None
        return refreshed

    # Видаляє schedule.
    async def delete_schedule(
        self,
        class_id: str,
        current_user: User,
        scope: RecurrenceScope = RecurrenceScope.OCCURRENCE,
    ) -> None:
        workout_class = await self.repository.get_by_id(class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

        self._ensure_delete_access(current_user)

        if scope == RecurrenceScope.OCCURRENCE or not workout_class.series_id:
            await self._delete_occurrence(workout_class)
            await self.session.commit()
            return

        if scope == RecurrenceScope.FOLLOWING:
            await self._delete_following(workout_class)
            await self.session.commit()
            return

        await self._delete_series(workout_class)
        await self.session.commit()

    # Підтверджує, що завершене заняття фактично відбулося.
    async def confirm_completion(
        self,
        class_id: str,
        payload: ScheduleCompleteRequest,
        current_user: User,
    ) -> WorkoutClass:
        workout_class = await self.repository.get_by_id(class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

        allowed_roles = {UserRole.ADMIN, UserRole.OWNER}
        if current_user.role not in allowed_roles and workout_class.trainer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостатньо прав доступу")

        now = datetime.now(UTC)
        class_end = ensure_aware(workout_class.end_time)
        if class_end > now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Заняття можна підтвердити лише після завершення",
            )

        workout_class.completed_at = workout_class.completed_at or now
        workout_class.completed_by = current_user
        comment = payload.comment.strip() if payload.comment else None
        workout_class.completion_comment = comment or None
        await self.repository.commit()

        refreshed = await self.repository.get_by_id(class_id)
        assert refreshed is not None
        return refreshed

    # Повертає список attendees.
    async def list_attendees(self, class_id: str, current_user: User):
        workout_class = await self.repository.get_by_id(class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

        allowed_roles = {UserRole.ADMIN, UserRole.OWNER}
        if current_user.role not in allowed_roles and workout_class.trainer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостатньо прав доступу")

        return await self.booking_repository.list_attendees_for_class(class_id)

    # Добудовує materialized occurrences для всіх активних серій.
    async def materialize_future_occurrences(self) -> int:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(WorkoutSeries)
            .where((WorkoutSeries.until.is_(None)) | (WorkoutSeries.until >= now))
            .options(selectinload(WorkoutSeries.exclusions))
        )
        created_count = 0
        for series in result.scalars().all():
            created_count += len(await self._materialize_series_occurrences(series))
        await self.session.commit()
        return created_count

    # Створює recurring-серію з payload.
    async def _create_series_from_payload(
        self,
        payload: ScheduleCreate,
        trainer_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> WorkoutSeries:
        recurrence = self._normalize_recurrence(payload.recurrence, start_time)
        series = WorkoutSeries(
            title=payload.title.strip(),
            description=None,
            trainer_id=trainer_id,
            start_time=start_time,
            end_time=end_time,
            capacity=payload.capacity,
            type=payload.type,
            is_paid_extra=payload.is_paid_extra,
            extra_price=payload.extra_price if payload.is_paid_extra else None,
            frequency=recurrence.frequency,
            interval=recurrence.interval,
            by_weekday=",".join(day.value for day in recurrence.by_weekday) or None,
            count=recurrence.count,
            until=ensure_aware(recurrence.until) if recurrence.until else None,
            rule_text=serialize_recurrence_rule(start_time, recurrence),
        )
        series.exclusions = []
        series.occurrences = []
        await self.series_repository.create(series)
        return series

    # Оновлює окрему occurrence без впливу на решту серії.
    async def _update_occurrence(self, workout_class: WorkoutClass, payload: ScheduleUpdate) -> WorkoutClass:
        if payload.recurrence is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recurring-правило можна змінювати лише для scope following або series",
            )

        update_data = payload.model_dump(exclude_unset=True, by_alias=False)
        update_data.pop("scope", None)
        update_data.pop("recurrence", None)
        self._apply_occurrence_updates(workout_class, update_data)

        if workout_class.series_id:
            workout_class.is_series_exception = True

        self._validate_time_range(workout_class.start_time, workout_class.end_time)
        self._validate_pricing(workout_class.is_paid_extra, workout_class.extra_price)
        if not workout_class.is_paid_extra:
            workout_class.extra_price = None
        return workout_class

    # Оновлює вибрану occurrence і всі наступні через split серії.
    async def _update_following(self, workout_class: WorkoutClass, payload: ScheduleUpdate) -> WorkoutClass:
        series = await self._require_series(workout_class)
        affected_from = ensure_aware(workout_class.start_time)
        await self._ensure_scope_has_no_booked_occurrences(series.id, affected_from)

        recurrence = self._normalize_recurrence(payload.recurrence, affected_from, fallback_series=series)
        new_start, new_end = self._derive_following_anchor(workout_class, payload)
        self._validate_time_range(new_start, new_end)

        old_scope_occurrences = await self.series_repository.list_occurrences(series.id, start_datetime=affected_from)
        for occurrence in old_scope_occurrences:
            await self.repository.delete(occurrence)
        await self._clear_exclusions(series, affected_from)

        split_point = self._source_occurrence_start(workout_class) - timedelta(seconds=1)
        series.until = split_point
        series.count = None
        series.rule_text = serialize_recurrence_rule(
            series.start_time,
            ScheduleRecurrence(
                frequency=series.frequency,
                interval=series.interval,
                byWeekday=self._series_weekdays(series),
                count=None,
                until=split_point,
            ),
        )

        new_series = WorkoutSeries(
            title=(payload.title or workout_class.title).strip(),
            description=workout_class.description,
            trainer_id=payload.trainer_id or workout_class.trainer_id,
            start_time=new_start,
            end_time=new_end,
            capacity=payload.capacity or workout_class.capacity,
            type=payload.type or workout_class.type,
            is_paid_extra=payload.is_paid_extra if payload.is_paid_extra is not None else workout_class.is_paid_extra,
            extra_price=self._resolve_extra_price(payload, workout_class),
            frequency=recurrence.frequency,
            interval=recurrence.interval,
            by_weekday=",".join(day.value for day in recurrence.by_weekday) or None,
            count=recurrence.count,
            until=ensure_aware(recurrence.until) if recurrence.until else None,
            rule_text=serialize_recurrence_rule(new_start, recurrence),
        )
        new_series.exclusions = []
        new_series.occurrences = []
        self._validate_pricing(new_series.is_paid_extra, new_series.extra_price)
        await self.series_repository.create(new_series)
        created = await self._materialize_series_occurrences(new_series, start_boundary=new_start)
        if not created:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нова серія не згенерувала занять")
        return created[0]

    # Оновлює всю майбутню частину серії.
    async def _update_series(self, workout_class: WorkoutClass, payload: ScheduleUpdate) -> WorkoutClass:
        series = await self._require_series(workout_class)
        now = datetime.now(UTC)
        await self._ensure_scope_has_no_booked_occurrences(series.id, now)

        recurrence = self._normalize_recurrence(payload.recurrence, series.start_time, fallback_series=series)
        new_start, new_end = self._derive_series_anchor(series, workout_class, payload)

        future_occurrences = await self.series_repository.list_occurrences(series.id, start_datetime=now)
        for occurrence in future_occurrences:
            await self.repository.delete(occurrence)
        await self._clear_exclusions(series, now)

        series.title = (payload.title or series.title).strip()
        series.trainer_id = payload.trainer_id or series.trainer_id
        series.type = payload.type or series.type
        series.capacity = payload.capacity or series.capacity
        series.start_time = new_start
        series.end_time = new_end
        if payload.is_paid_extra is not None:
            series.is_paid_extra = payload.is_paid_extra
        series.extra_price = self._resolve_extra_price(payload, series)
        self._validate_time_range(series.start_time, series.end_time)
        self._validate_pricing(series.is_paid_extra, series.extra_price)
        if not series.is_paid_extra:
            series.extra_price = None
        series.frequency = recurrence.frequency
        series.interval = recurrence.interval
        series.by_weekday = ",".join(day.value for day in recurrence.by_weekday) or None
        series.count = recurrence.count
        series.until = ensure_aware(recurrence.until) if recurrence.until else None
        series.rule_text = serialize_recurrence_rule(series.start_time, recurrence)

        created = await self._materialize_series_occurrences(series, start_boundary=now)
        if not created:
            refreshed = await self.repository.get_by_id(workout_class.id)
            if refreshed:
                return refreshed
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Після оновлення серія не містить жодної майбутньої occurrence",
            )

        target = min(created, key=lambda item: abs((ensure_aware(item.start_time) - ensure_aware(workout_class.start_time)).total_seconds()))
        return target

    # Видаляє окрему occurrence.
    async def _delete_occurrence(self, workout_class: WorkoutClass) -> None:
        self._ensure_occurrence_is_unbooked(workout_class)
        if workout_class.series_id:
            exclusion = await self.series_repository.get_exclusion(
                workout_class.series_id,
                self._source_occurrence_start(workout_class),
            )
            if exclusion is None:
                await self.series_repository.add_exclusion(
                    WorkoutSeriesExclusion(
                        series_id=workout_class.series_id,
                        occurrence_start=self._source_occurrence_start(workout_class),
                    )
                )
        await self.repository.delete(workout_class)

    # Видаляє всі наступні occurrences серії.
    async def _delete_following(self, workout_class: WorkoutClass) -> None:
        series = await self._require_series(workout_class)
        affected_from = ensure_aware(workout_class.start_time)
        await self._ensure_scope_has_no_booked_occurrences(series.id, affected_from)

        future_occurrences = await self.series_repository.list_occurrences(series.id, start_datetime=affected_from)
        for occurrence in future_occurrences:
            await self.repository.delete(occurrence)
        await self._clear_exclusions(series, affected_from)

        split_point = self._source_occurrence_start(workout_class) - timedelta(seconds=1)
        series.until = split_point
        series.count = None
        series.rule_text = serialize_recurrence_rule(
            series.start_time,
            ScheduleRecurrence(
                frequency=series.frequency,
                interval=series.interval,
                byWeekday=self._series_weekdays(series),
                count=None,
                until=split_point,
            ),
        )

    # Видаляє всю майбутню частину серії.
    async def _delete_series(self, workout_class: WorkoutClass) -> None:
        series = await self._require_series(workout_class)
        now = datetime.now(UTC)
        await self._ensure_scope_has_no_booked_occurrences(series.id, now)

        future_occurrences = await self.series_repository.list_occurrences(series.id, start_datetime=now)
        for occurrence in future_occurrences:
            await self.repository.delete(occurrence)
        await self._clear_exclusions(series, now)

        if now > ensure_aware(series.start_time):
            series.until = now - timedelta(seconds=1)
            series.count = None
            series.rule_text = serialize_recurrence_rule(
                series.start_time,
                ScheduleRecurrence(
                    frequency=series.frequency,
                    interval=series.interval,
                    byWeekday=self._series_weekdays(series),
                    count=None,
                    until=series.until,
                ),
            )
        else:
            await self.session.delete(series)

    # Генерує materialized occurrences серії у доступному горизонті.
    async def _materialize_series_occurrences(
        self,
        series: WorkoutSeries,
        start_boundary: datetime | None = None,
    ) -> list[WorkoutClass]:
        boundary_start = ensure_aware(start_boundary or datetime.now(UTC))
        window_start = max(boundary_start, ensure_aware(series.start_time))
        window_end = self._materialization_window_end(series)
        if window_end < window_start:
            return []

        existing_occurrences = await self.series_repository.list_occurrences(
            series.id,
            start_datetime=window_start,
            end_datetime=window_end,
        )
        existing_by_source = {
            self._source_occurrence_start(item): item
            for item in existing_occurrences
            if item.source_occurrence_start is not None
        }
        excluded = {ensure_aware(item.occurrence_start) for item in series.exclusions}
        duration = ensure_aware(series.end_time) - ensure_aware(series.start_time)

        created: list[WorkoutClass] = []
        for occurrence_start in generate_occurrence_starts(
            start_time=series.start_time,
            rule_text=series.rule_text,
            window_start=window_start,
            window_end=window_end,
        ):
            normalized_start = ensure_aware(occurrence_start)
            if normalized_start in excluded or normalized_start in existing_by_source:
                continue

            occurrence = WorkoutClass(
                title=series.title,
                description=series.description,
                trainer_id=series.trainer_id,
                start_time=normalized_start,
                end_time=normalized_start + duration,
                capacity=series.capacity,
                type=series.type,
                is_paid_extra=series.is_paid_extra,
                extra_price=series.extra_price,
                series_id=series.id,
                source_occurrence_start=normalized_start,
                is_series_exception=False,
            )
            created.append(await self.repository.create(occurrence))

        return created

    # Видаляє винятки серії, починаючи з вказаної дати.
    async def _clear_exclusions(self, series: WorkoutSeries, start_datetime: datetime) -> None:
        start_boundary = ensure_aware(start_datetime)
        for exclusion in list(series.exclusions):
            if ensure_aware(exclusion.occurrence_start) >= start_boundary:
                await self.series_repository.delete_exclusion(exclusion)
                series.exclusions.remove(exclusion)

    # Перевіряє, чи немає booked occurrences в scope.
    async def _ensure_scope_has_no_booked_occurrences(self, series_id: str, start_datetime: datetime) -> None:
        occurrences = await self.series_repository.list_occurrences(
            series_id,
            start_datetime=ensure_aware(start_datetime),
        )
        if any(self._has_confirmed_bookings(item) for item in occurrences):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не можна змінювати або видаляти серію, поки в зачеплених заняттях є підтверджені записи",
            )

    # Застосовує значення patch-оновлення до occurrence.
    def _apply_occurrence_updates(self, workout_class: WorkoutClass, update_data: dict) -> None:
        for field_name, value in update_data.items():
            if field_name == "start_time" and value is not None:
                setattr(workout_class, field_name, ensure_aware(value))
                continue
            if field_name == "end_time" and value is not None:
                setattr(workout_class, field_name, ensure_aware(value))
                continue
            if field_name == "title" and value is not None:
                setattr(workout_class, field_name, value.strip())
                continue
            setattr(workout_class, field_name, value)

    # Повертає recurrence з fallback на існуючу серію.
    def _normalize_recurrence(
        self,
        recurrence: ScheduleRecurrence | None,
        start_time: datetime,
        *,
        fallback_series: WorkoutSeries | None = None,
    ) -> ScheduleRecurrence:
        if recurrence is None and fallback_series is not None:
            return ScheduleRecurrence(
                frequency=fallback_series.frequency,
                interval=fallback_series.interval,
                byWeekday=self._series_weekdays(fallback_series),
                count=fallback_series.count,
                until=fallback_series.until,
            )
        if recurrence is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Для серії потрібне recurrence-правило")
        if recurrence.frequency.value == "WEEKLY" and not recurrence.by_weekday:
            recurrence.by_weekday = [RecurrenceWeekday(weekday_codes_for_start(start_time)[0])]
        if recurrence.until is not None and ensure_aware(recurrence.until) <= ensure_aware(start_time):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Дата завершення recurring-серії має бути пізніше за перше заняття",
            )
        return recurrence

    # Повертає weekday-коди серії.
    @staticmethod
    def _series_weekdays(series: WorkoutSeries):
        values = [value for value in (series.by_weekday or "").split(",") if value]
        return [RecurrenceWeekday(value) for value in values] or [RecurrenceWeekday(weekday_codes_for_start(series.start_time)[0])]

    # Повертає кінець materialization-вікна.
    @staticmethod
    def _materialization_window_end(series: WorkoutSeries) -> datetime:
        horizon_end = datetime.now(UTC) + timedelta(days=settings.schedule_materialization_horizon_days)
        if series.until is None:
            return horizon_end
        return min(horizon_end, ensure_aware(series.until))

    # Виводить новий anchor для split-серії.
    def _derive_following_anchor(self, workout_class: WorkoutClass, payload: ScheduleUpdate) -> tuple[datetime, datetime]:
        start_time = ensure_aware(payload.start_time) if payload.start_time else ensure_aware(workout_class.start_time)
        if payload.end_time:
            end_time = ensure_aware(payload.end_time)
        else:
            end_time = start_time + (ensure_aware(workout_class.end_time) - ensure_aware(workout_class.start_time))
        return start_time, end_time

    # Виводить новий anchor для whole-series update.
    def _derive_series_anchor(
        self,
        series: WorkoutSeries,
        workout_class: WorkoutClass,
        payload: ScheduleUpdate,
    ) -> tuple[datetime, datetime]:
        current_series_start = ensure_aware(series.start_time)
        current_series_end = ensure_aware(series.end_time)
        current_occurrence_start = ensure_aware(workout_class.start_time)

        if payload.start_time:
            delta = ensure_aware(payload.start_time) - current_occurrence_start
            next_start = current_series_start + delta
        else:
            next_start = current_series_start

        if payload.start_time or payload.end_time:
            reference_start = ensure_aware(payload.start_time) if payload.start_time else current_occurrence_start
            reference_end = ensure_aware(payload.end_time) if payload.end_time else ensure_aware(workout_class.end_time)
            duration = reference_end - reference_start
            next_end = next_start + duration
        else:
            next_end = current_series_end

        return next_start, next_end

    # Повертає extra_price з урахуванням mutating payload.
    @staticmethod
    def _resolve_extra_price(payload: ScheduleUpdate, source) -> float | None:
        if payload.is_paid_extra is False:
            return None
        if payload.extra_price is not None:
            return payload.extra_price
        return source.extra_price

    # Повертає source_occurrence_start для recurring occurrence або її фактичний старт.
    @staticmethod
    def _source_occurrence_start(workout_class: WorkoutClass) -> datetime:
        return ensure_aware(workout_class.source_occurrence_start or workout_class.start_time)

    # Завантажує series-модель для occurrence.
    async def _require_series(self, workout_class: WorkoutClass) -> WorkoutSeries:
        if not workout_class.series_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Заняття не належить до серії")
        series = await self.series_repository.get_by_id(workout_class.series_id)
        if not series:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring-серію не знайдено")
        return series

    # Перевіряє права на update.
    @staticmethod
    def _ensure_update_access(workout_class: WorkoutClass, current_user: User) -> None:
        if current_user.role in {UserRole.ADMIN, UserRole.OWNER}:
            return
        if current_user.role == UserRole.TRAINER and workout_class.trainer_id == current_user.id:
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостатньо прав доступу")

    # Перевіряє права на delete.
    @staticmethod
    def _ensure_delete_access(current_user: User) -> None:
        if current_user.role in {UserRole.ADMIN, UserRole.OWNER}:
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостатньо прав доступу")

    # Перевіряє, що видалювана occurrence не має confirmed bookings.
    def _ensure_occurrence_is_unbooked(self, workout_class: WorkoutClass) -> None:
        if self._has_confirmed_bookings(workout_class):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не можна видалити заняття, поки в ньому є підтверджені записи",
            )

    # Повертає ознаку confirmed bookings.
    @staticmethod
    def _has_confirmed_bookings(workout_class: WorkoutClass) -> bool:
        return any(booking.status == BookingStatus.CONFIRMED for booking in workout_class.bookings)

    # Перевіряє time range.
    @classmethod
    def _validate_time_range(cls, start_time: datetime, end_time: datetime) -> None:
        normalized_start = ensure_aware(start_time)
        normalized_end = ensure_aware(end_time)

        if normalized_end <= normalized_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Час завершення має бути пізніше за час початку",
            )

        local_start = normalized_start.astimezone(cls.CLUB_TIMEZONE)
        local_end = normalized_end.astimezone(cls.CLUB_TIMEZONE)
        is_same_local_day = local_start.date() == local_end.date()
        if (
            not is_same_local_day
            or local_start.time() < cls.CLUB_OPEN_TIME
            or local_end.time() > cls.CLUB_CLOSE_TIME
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Заняття можна планувати лише в межах роботи клубу: 06:00-22:00",
            )

    # Перевіряє pricing.
    @staticmethod
    def _validate_pricing(is_paid_extra: bool, extra_price) -> None:
        if is_paid_extra:
            if extra_price is None or extra_price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Для платного заняття потрібно вказати додаткову вартість",
                )
