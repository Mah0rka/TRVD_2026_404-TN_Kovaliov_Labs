import pytest
from fastapi import HTTPException

from app.models.user import UserRole
from app.services.user_service import UserService
from app.schemas.user import UserAdminCreate, UserAdminUpdate, UserProfileUpdate


@pytest.mark.asyncio
async def test_user_service_can_create_filter_and_update_users(db_session):
    service = UserService(db_session)

    created_admin = await service.create_user(
        UserAdminCreate(
            email="admin-flow@example.com",
            password="Password123!",
            first_name="Admin",
            last_name="Flow",
            role=UserRole.ADMIN,
            is_verified=True,
        )
    )
    created_trainer = await service.create_user(
        UserAdminCreate(
            email="trainer-flow@example.com",
            password="Password123!",
            first_name="Trainer",
            last_name="Flow",
            role=UserRole.TRAINER,
            is_verified=True,
        )
    )

    admins = await service.list_users(UserRole.ADMIN)
    assert len(admins) == 1
    assert admins[0].email == "admin-flow@example.com"

    updated_admin = await service.update_user(
        created_admin.id,
        UserAdminUpdate(first_name="Updated", phone="+380991112233", role=UserRole.OWNER),
    )
    assert updated_admin.first_name == "Updated"
    assert updated_admin.phone == "+380991112233"
    assert updated_admin.role == UserRole.OWNER

    updated_trainer = await service.update_profile(
        created_trainer,
        UserProfileUpdate(first_name="Coach", last_name="Prime", phone="+380509990000"),
    )
    assert updated_trainer.first_name == "Coach"
    assert updated_trainer.last_name == "Prime"
    assert updated_trainer.phone == "+380509990000"


@pytest.mark.asyncio
async def test_user_service_can_delete_user_but_not_self_or_last_owner(db_session):
    service = UserService(db_session)

    owner = await service.create_user(
        UserAdminCreate(
            email="owner-flow@example.com",
            password="Password123!",
            first_name="Owner",
            last_name="Flow",
            role=UserRole.OWNER,
            is_verified=True,
        )
    )
    admin = await service.create_user(
        UserAdminCreate(
            email="admin-delete@example.com",
            password="Password123!",
            first_name="Admin",
            last_name="Delete",
            role=UserRole.ADMIN,
            is_verified=True,
        )
    )
    client = await service.create_user(
        UserAdminCreate(
            email="client-delete@example.com",
            password="Password123!",
            first_name="Client",
            last_name="Delete",
            role=UserRole.CLIENT,
            is_verified=True,
        )
    )

    with pytest.raises(HTTPException) as self_delete_error:
        await service.delete_user(admin, admin.id)
    assert self_delete_error.value.detail == "You cannot delete your own account"

    with pytest.raises(HTTPException) as last_owner_error:
        await service.delete_user(admin, owner.id)
    assert last_owner_error.value.detail == "You cannot delete the last owner account"

    await service.delete_user(admin, client.id)
    assert await service.repository.get_by_id(client.id) is None
