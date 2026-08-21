from dataclasses import dataclass,asdict
from typing import Any,Dict
from app.workspace.repository_workspace import RepositoryWorkspace
from app.services.analysis_service import AnalysisService
@dataclass
class RemoteAnalysisResult:
    repository_url:str
    branch:str|None
    commit:str
    analysis:Dict[str,Any]
class RemoteAnalysisService:
    def analyze(self,repository_url:str,base_ref:str="main",target_ref:str="HEAD",branch:str|None=None)->RemoteAnalysisResult:
        with RepositoryWorkspace(repository_url,branch) as workspace:
            service=AnalysisService(workspace.local_path)
            result=service.run(base_ref,target_ref)
            return RemoteAnalysisResult(
                repository_url=repository_url,
                branch=workspace.branch,
                commit=workspace.commit,
                analysis=asdict(result)
            )