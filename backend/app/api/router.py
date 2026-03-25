# Коротко: модуль готує HTTP-шар для маршрутизації.

from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.health import router as health_router
from app.api.routes.payments import router as payments_router
from app.api.routes.public import router as public_router
from app.api.routes.reports import router as reports_router
from app.api.routes.schedules import router as schedules_router
from app.api.routes.subscriptions import router as subscriptions_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(public_router, prefix="/public", tags=["public"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(bookings_router, prefix="/bookings", tags=["bookings"])
api_router.include_router(payments_router, prefix="/payments", tags=["payments"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(schedules_router, prefix="/schedules", tags=["schedules"])
api_router.include_router(subscriptions_router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
