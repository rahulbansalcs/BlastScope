from datetime import datetime,timezone
from pathlib import Path
from typing import Optional,List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.analysis import AnalysisRecord
class AnalysisJobService:
    def __init__(self,session:Session):
        self.session=session
    def create_job(self,repository_url:str,base_ref:str="main",target_ref:str="HEAD")->AnalysisRecord:
        repository_name=self._repository_name(repository_url)
        job=AnalysisRecord(
            repository_url=repository_url,
            repository_name=repository_name,
            base_ref=base_ref,
            target_ref=target_ref,
            status="queued",
            progress=0,
            current_stage="queued"
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job
    def get_job(self,job_id)->Optional[AnalysisRecord]:
        return self.session.get(AnalysisRecord,job_id)
    def list_jobs(self,limit:int=20,offset:int=0,status:Optional[str]=None)->List[AnalysisRecord]:
        query=select(AnalysisRecord)
        if status:
            query=query.where(AnalysisRecord.status==status)
        query=query.order_by(AnalysisRecord.created_at.desc()).offset(offset).limit(limit)
        return list(self.session.scalars(query).all())
    def count_jobs(self,status:Optional[str]=None)->int:
        jobs=self.list_jobs(limit=100000,offset=0,status=status)
        return len(jobs)
    def mark_started(self,job_id,commit_sha:Optional[str]=None)->AnalysisRecord:
        job=self._require_job(job_id)
        job.status="running"
        job.progress=5
        job.current_stage="starting"
        job.started_at=datetime.now(timezone.utc)
        if commit_sha:
            job.commit_sha=commit_sha
        self._save(job)
        return job
    def update_progress(self,job_id,progress:int,stage:str)->AnalysisRecord:
        job=self._require_job(job_id)
        job.status="running"
        job.progress=max(0,min(100,progress))
        job.current_stage=stage
        self._save(job)
        return job
    def mark_completed(self,job_id,result:dict,risk_score:Optional[int]=None,risk_level:Optional[str]=None)->AnalysisRecord:
        job=self._require_job(job_id)
        job.status="completed"
        job.progress=100
        job.current_stage="completed"
        job.result=result
        job.overall_risk_score=risk_score
        job.overall_risk_level=risk_level
        job.completed_at=datetime.now(timezone.utc)
        job.error_message=None
        self._save(job)
        return job
    def mark_failed(self,job_id,error_message:str)->AnalysisRecord:
        job=self._require_job(job_id)
        job.status="failed"
        job.current_stage="failed"
        job.error_message=error_message
        job.completed_at=datetime.now(timezone.utc)
        self._save(job)
        return job
    def delete_job(self,job_id)->None:
        job=self._require_job(job_id)
        self.session.delete(job)
        self.session.commit()
    def _require_job(self,job_id)->AnalysisRecord:
        job=self.get_job(job_id)
        if not job:
            raise ValueError(f"Analysis job not found: {job_id}")
        return job
    def _save(self,job:AnalysisRecord)->None:
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
    def _repository_name(self,repository_url:str)->str:
        value=repository_url.rstrip("/")
        name=Path(value).name
        if name.endswith(".git"):
            name=name[:-4]
        return name or "repository"