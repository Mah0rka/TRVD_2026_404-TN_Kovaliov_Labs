from app.main import app


def test_openapi_exists():
    assert app.openapi()["info"]["title"] == "MotionLab API"
