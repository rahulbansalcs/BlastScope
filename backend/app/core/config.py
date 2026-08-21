import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()
@dataclass(frozen=True)
class Settings:
    app_name:str
    environment:str
    database_url:str
    cors_origins:list[str]
    max_repository_size_mb:int
    analysis_timeout_seconds:int
    git_clone_depth:int
def load_settings()->Settings:
    database_url=os.getenv("DATABASE_URL","").strip()
    if database_url.startswith("postgres://"):
        database_url=database_url.replace("postgres://","postgresql://",1)
    cors_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS","http://localhost:5173").split(",")
        if origin.strip()
    ]
    return Settings(
        app_name=os.getenv("APP_NAME","BlastScope"),
        environment=os.getenv("ENVIRONMENT","development"),
        database_url=database_url,
        cors_origins=cors_origins,
        max_repository_size_mb=int(os.getenv("MAX_REPOSITORY_SIZE_MB","200")),
        analysis_timeout_seconds=int(os.getenv("ANALYSIS_TIMEOUT_SECONDS","300")),
        git_clone_depth=int(os.getenv("GIT_CLONE_DEPTH","100"))
    )
settings=load_settings()