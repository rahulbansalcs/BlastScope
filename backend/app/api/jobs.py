import uuid
import os
from fastapi import APIRouter,BackgroundTasks,Depends,HTTPException,Query
from datetime import datetime
from typing import Optional,List
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_session
from app.services.analysis_job_service import AnalysisJobService
from app.queue.connection import get_analysis_queue
from app.workers.analysis_worker import execute_analysis_job
router=APIRouter(prefix="/api/jobs",tags=["analysis-jobs"])
class CreateJobRequest(BaseModel):
    repository_url:str
    base_ref:str="main"
    target_ref:str="HEAD"
class JobResponse(BaseModel):
    id:uuid.UUID
    repository_url:str
    repository_name:str
    base_ref:str
    target_ref:str
    commit_sha:str|None
    status:str
    progress:int
    current_stage:str
    overall_risk_score:int|None
    overall_risk_level:str|None
    error_message:str|None
    result:dict|None
    created_at:datetime
    started_at:datetime|None
    completed_at:datetime|None
    class Config:
        from_attributes=True
class JobListItem(BaseModel):
    id:uuid.UUID
    repository_url:str
    repository_name:str
    base_ref:str
    target_ref:str
    status:str
    progress:int
    current_stage:str
    overall_risk_score:int|None
    overall_risk_level:str|None
    created_at:datetime
    completed_at:datetime|None
    class Config:
        from_attributes=True
class JobListResponse(BaseModel):
    total:int
    limit:int
    offset:int
    jobs:List[JobListItem]
@router.post("",response_model=JobResponse)
def create_job(request:CreateJobRequest,background_tasks:BackgroundTasks,session:Session=Depends(get_session)):
    try:
        service=AnalysisJobService(session)
        job=service.create_job(
            repository_url=request.repository_url,
            base_ref=request.base_ref,
            target_ref=request.target_ref
        )
        use_job_queue=os.getenv("USE_JOB_QUEUE","true").lower()=="true"
        if use_job_queue:
            queue=get_analysis_queue()
            queue.enqueue(
                execute_analysis_job,
                str(job.id),
                job_timeout=1800,
                result_ttl=3600,
                failure_ttl=86400
            )
        else:
            background_tasks.add_task(execute_analysis_job,str(job.id))
        return job
    except Exception as error:
        raise HTTPException(status_code=500,detail=str(error)) from error
@router.get("",response_model=JobListResponse)
def list_jobs(limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0),status:Optional[str]=Query(None),session:Session=Depends(get_session)):
    service=AnalysisJobService(session)
    jobs=service.list_jobs(limit=limit,offset=offset,status=status)
    total=service.count_jobs(status=status)
    return{
        "total":total,
        "limit":limit,
        "offset":offset,
        "jobs":jobs
    }
@router.get("/{job_id}",response_model=JobResponse)
def get_job(job_id:uuid.UUID,session:Session=Depends(get_session)):
    service=AnalysisJobService(session)
    job=service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404,detail="Analysis job not found")
    return job
@router.delete("/{job_id}")
def delete_job(job_id:uuid.UUID,session:Session=Depends(get_session)):
    try:
        service=AnalysisJobService(session)
        service.delete_job(job_id)
        return{"status":"deleted"}
    except ValueError as error:
        raise HTTPException(status_code=404,detail=str(error)) from error