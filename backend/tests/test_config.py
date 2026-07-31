from app.core.config import Settings


def test_settings_builds_mysql_url_from_environment(monkeypatch):
    monkeypatch.setenv("MYSQL_HOST", "mysql.example")
    monkeypatch.setenv("MYSQL_PORT", "3307")
    monkeypatch.setenv("MYSQL_DATABASE", "analysis_db")
    monkeypatch.setenv("MYSQL_USER", "analysis_user")
    monkeypatch.setenv("MYSQL_PASSWORD", "safe-password")

    settings = Settings()

    assert settings.database_url == "mysql+pymysql://analysis_user:safe-password@mysql.example:3307/analysis_db"
