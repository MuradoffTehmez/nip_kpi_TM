from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DRIVER_KPI_DB: str
    USER_KPI_DB: str
    PASS_KPI_DB: str
    HOST_KPI_DB: str
    PORT_KPI_DB: int
    NAME_KPI_DB: str

    @property
    def get_db_url(self):
        return f"{self.DRIVER_KPI_DB}://{self.USER_KPI_DB}:{self.PASS_KPI_DB}@{self.HOST_KPI_DB}/{self.NAME_KPI_DB}"
    
    
settings = Settings(_env_file='.env', _env_file_encoding='utf-8') # type: ignore
    


