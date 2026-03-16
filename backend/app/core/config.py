from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "携观布线图自动生成软件"
    api_prefix: str = "/api"
    secret_key: str = "change-this-secret-key"
    access_token_expire_minutes: int = 60 * 24

    mysql_user: str = "root"
    mysql_password: str = "root"
    mysql_host: str = "db"
    mysql_port: int = 3306
    mysql_database: str = "xieguan_wire"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )


settings = Settings()
