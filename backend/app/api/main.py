import os
from dataclasses import asdict
from pathlib import Path
from app.api.graph import router as graph_router
from app.api.repositories import router as repositories_router
from app.api.jobs import router as jobs_router
from app.services.remote_analysis_service import RemoteAnalysisService
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.analysis_service import AnalysisService
from app.api.schemas import AnalysisRequestSchema,FullAnalysisResponseSchema,HealthResponseSchema,RemoteAnalysisRequestSchema,RemoteAnalysisResponseSchema
app=FastAPI(
    title="BlastScope API",
    description="Dependency blast radius and change impact analysis platform",
    version="0.1.0"
)
cors_env=os.getenv("CORS_ORIGINS","")
cors_origins=[
"http://localhost:5173",
"http://127.0.0.1:5173"
]
if cors_env:
    cors_origins.extend(origin.strip() for origin in cors_env.split(",") if origin.strip())
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(jobs_router)
app.include_router(repositories_router)
allowed_origins=[
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS","http://localhost:5173").split(",")
    if origin.strip()
]
app.include_router(graph_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
@app.get("/")
def root():
    return {
        "name":"BlastScope",
        "service":"Dependency Blast Radius Analyzer",
        "version":"0.1.0",
        "status":"running"
    }
@app.get("/api/health",response_model=HealthResponseSchema)
def health():
    return {
        "status":"healthy"
    }
@app.post("/api/analysis",response_model=FullAnalysisResponseSchema)
def run_analysis(request:AnalysisRequestSchema):
    repository_path=Path(request.repository_path).resolve()
    if not repository_path.exists():
        raise HTTPException(status_code=404,detail="Repository path does not exist")
    if not repository_path.is_dir():
        raise HTTPException(status_code=400,detail="Repository path must be a directory")
    try:
        service=AnalysisService(str(repository_path))
        result=service.run(request.base_ref,request.target_ref)
        return asdict(result)
    except ValueError as error:
        raise HTTPException(status_code=400,detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500,detail=f"Analysis failed: {error}") from error
@app.post("/api/analysis/remote",response_model=RemoteAnalysisResponseSchema)
def run_remote_analysis(request:RemoteAnalysisRequestSchema):
    try:
        service=RemoteAnalysisService()
        result=service.analyze(
            repository_url=request.repository_url,
            base_ref=request.base_ref,
            target_ref=request.target_ref,
            branch=request.branch
        )
        return {
            "repository_url":result.repository_url,
            "branch":result.branch,
            "commit":result.commit,
            "analysis":result.analysis
        }
    except ValueError as error:
        raise HTTPException(status_code=400,detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500,detail=f"Remote analysis failed: {error}") from error