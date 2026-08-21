from dataclasses import dataclass,field
from pathlib import Path
from typing import Dict,List,Tuple
from collections import defaultdict
from git import Repo
@dataclass
class CoupledFile:
    file_path:str
    shared_commits:int
    target_commits:int
    coupling_score:float
@dataclass
class CouplingAnalysis:
    target_file:str
    total_target_commits:int
    coupled_files:List[CoupledFile]=field(default_factory=list)
class CouplingAnalyzer:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
        self.repo=Repo(str(self.repository_path))
    def analyze_file(self,file_path:str,max_commits:int=300,min_shared_commits:int=2)->CouplingAnalysis:
        target_commits=list(
            self.repo.iter_commits(
                paths=file_path,
                max_count=max_commits
            )
        )
        if not target_commits:
            return CouplingAnalysis(
                target_file=file_path,
                total_target_commits=0,
                coupled_files=[]
            )
        cochange_counts:Dict[str,int]=defaultdict(int)
        for commit in target_commits:
            changed_files=self._changed_files(commit)
            for changed_file in changed_files:
                if changed_file==file_path:
                    continue
                cochange_counts[changed_file]+=1
        coupled_files=[]
        target_commit_count=len(target_commits)
        for coupled_file,shared_count in cochange_counts.items():
            if shared_count<min_shared_commits:
                continue
            score=(shared_count/target_commit_count)*100
            coupled_files.append(
                CoupledFile(
                    file_path=coupled_file,
                    shared_commits=shared_count,
                    target_commits=target_commit_count,
                    coupling_score=round(score,2)
                )
            )
        coupled_files.sort(
            key=lambda item:(item.coupling_score,item.shared_commits),
            reverse=True
        )
        return CouplingAnalysis(
            target_file=file_path,
            total_target_commits=target_commit_count,
            coupled_files=coupled_files
        )
    def analyze_repository(self,max_commits:int=300,min_shared_commits:int=2)->Dict[str,CouplingAnalysis]:
        files=self._repository_files()
        results={}
        for file_path in files:
            analysis=self.analyze_file(
                file_path,
                max_commits=max_commits,
                min_shared_commits=min_shared_commits
            )
            if analysis.coupled_files:
                results[file_path]=analysis
        return results
    def _changed_files(self,commit)->List[str]:
        if not commit.parents:
            return [
                item.a_path
                for item in commit.diff(None)
                if item.a_path
            ]
        parent=commit.parents[0]
        diff=parent.diff(commit)
        files=set()
        for item in diff:
            if item.a_path:
                files.add(item.a_path)
            if item.b_path:
                files.add(item.b_path)
        return sorted(files)
    def _repository_files(self)->List[str]:
        files=[]
        for item in self.repo.tree().traverse():
            if item.type=="blob":
                files.append(item.path)
        return files