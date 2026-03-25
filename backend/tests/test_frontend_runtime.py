# Тести перевіряють ключові сценарії цього модуля.

from app.main import resolve_frontend_file


# Перевіряє, що resolve frontend file returns existing asset працює коректно.
def test_resolve_frontend_file_returns_existing_asset(tmp_path):
    dist_dir = tmp_path
    index_file = dist_dir / "index.html"
    asset_dir = dist_dir / "assets"
    asset_dir.mkdir()
    asset_file = asset_dir / "app.js"
    index_file.write_text("index", encoding="utf-8")
    asset_file.write_text("console.log('ok')", encoding="utf-8")

    resolved = resolve_frontend_file(dist_dir, "assets/app.js")

    assert resolved == asset_file


# Перевіряє, що resolve frontend file falls back to index for spa route працює коректно.
def test_resolve_frontend_file_falls_back_to_index_for_spa_route(tmp_path):
    dist_dir = tmp_path
    index_file = dist_dir / "index.html"
    index_file.write_text("index", encoding="utf-8")

    resolved = resolve_frontend_file(dist_dir, "dashboard/subscriptions")

    assert resolved == index_file


# Перевіряє, що resolve frontend file keeps api 404 behavior працює коректно.
def test_resolve_frontend_file_keeps_api_404_behavior(tmp_path):
    dist_dir = tmp_path
    index_file = dist_dir / "index.html"
    index_file.write_text("index", encoding="utf-8")

    resolved = resolve_frontend_file(dist_dir, "auth/unknown")

    assert resolved is None
