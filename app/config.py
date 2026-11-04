from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "root_secret_pass_123"
    POSTGRES_DB: str = "cinema_db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin123"
    S3_BUCKET_NAME: str = "cinema-backups"

    SECRET_KEY: str = "secret"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()