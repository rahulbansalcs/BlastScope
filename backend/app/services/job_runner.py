from dataclasses import asdict
from app.db.database import initialize_database,SessionLocal
from app.services.analysis_job_service import AnalysisJobService
from app.services.remote_analysis_service import RemoteAnalysisService
def run_analysis_job(job_id):
    initialize_database()
    session=SessionLocal()
    try:
        job_service=AnalysisJobService(session)
        job=job_service.get_job(job_id)
        if not job:
            return
        job_service.mark_started(job_id)
        job_service.update_progress(job_id,10,"cloning")
        remote_service=RemoteAnalysisService()
        result=remote_service.analyze(
            repository_url=job.repository_url,
            base_ref=job.base_ref,
            target_ref=job.target_ref
        )
        job_service.update_progress(job_id,85,"finalizing")
        analysis=result.analysis
        summary=analysis.get("summary",{})
        risk_score=summary.get("overall_risk_score")
        risk_level=summary.get("overall_risk_level")
        job.commit_sha=result.commit
        session.commit()
        job_service.mark_completed(
            job_id,
            analysis,
            risk_score,
            risk_level
        )
    except Exception as error:
        try:
            AnalysisJobService(session).mark_failed(
                job_id,
                str(error)
            )
        except Exception:
            pass
    finally:
        session.close()