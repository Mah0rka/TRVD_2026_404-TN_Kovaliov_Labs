# Тести перевіряють ключові сценарії цього модуля.

from app.main import app


# Перевіряє, що openapi exists працює коректно.
def test_openapi_exists():
    assert app.openapi()["info"]["title"] == "MotionLab API"
