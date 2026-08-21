from dataclasses import dataclass,field
from pathlib import Path
from typing import List
from git import Repo
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.analyzers.signature_analyzer import SignatureAnalyzer
from app.analyzers.call_compatibility_analyzer import CallCompatibilityAnalyzer,CallCompatibilityResult
@dataclass
class BreakingChangeResult:
    symbol:str
    change_type:str
    breaking:bool
    reasons:List[str]=field(default_factory=list)
    affected_callers:List[str]=field(default_factory=list)
    compatible_callers:List[CallCompatibilityResult]=field(default_factory=list)
    incompatible_callers:List[CallCompatibilityResult]=field(default_factory=list)
    affected_count:int=0
    potential_runtime_failures:int=0
class BreakingChangeAnalyzer:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
        self.repo=Repo(str(self.repository_path))
        self.signature_analyzer=SignatureAnalyzer()
        self.compatibility_analyzer=CallCompatibilityAnalyzer()
    def analyze(self,base_ref:str="main",target_ref:str="HEAD")->List[BreakingChangeResult]:
        repository_analyzer=RepositoryAnalyzer(str(self.repository_path))
        repository_result=repository_analyzer.analyze()
        results=[]
        changed_python_files=self._get_changed_python_files(base_ref,target_ref)
        for file_path in changed_python_files:
            old_source=self._read_file_at_ref(base_ref,file_path)
            new_source=self._read_file_at_ref(target_ref,file_path)
            module_name=self._module_name(file_path)
            old_signatures=self.signature_analyzer.extract_from_source(old_source,file_path,module_name) if old_source else {}
            new_signatures=self.signature_analyzer.extract_from_source(new_source,file_path,module_name) if new_source else {}
            changes=self.signature_analyzer.compare(old_signatures,new_signatures)
            for change in changes:
                if not change.breaking:
                    continue
                node_id=f"symbol:{change.qualified_name}"
                affected=[]
                if repository_result.graph.get_node(node_id):
                    impacted=repository_result.graph.get_transitive_impact(node_id)
                    affected=[node.name for node,depth in impacted if node.node_type in {"function","method"}]
                compatible=[]
                incompatible=[]
                if change.new_signature:
                    target_name=change.qualified_name.rsplit(".",1)[-1]
                    calls=self.compatibility_analyzer.find_calls(str(self.repository_path),target_name)
                    compatibility_results=self.compatibility_analyzer.analyze(change.new_signature,calls)
                    compatible=[result for result in compatibility_results if result.compatible]
                    incompatible=[result for result in compatibility_results if not result.compatible]
                results.append(
                    BreakingChangeResult(
                        symbol=change.qualified_name,
                        change_type=change.change_type,
                        breaking=True,
                        reasons=change.reasons,
                        affected_callers=affected,
                        compatible_callers=compatible,
                        incompatible_callers=incompatible,
                        affected_count=len(affected),
                        potential_runtime_failures=len(incompatible)
                    )
                )
        return results
    def _get_changed_python_files(self,base_ref:str,target_ref:str)->List[str]:
        diff=self.repo.commit(base_ref).diff(self.repo.commit(target_ref))
        files=[]
        for item in diff:
            path=item.b_path or item.a_path
            if path and path.endswith(".py"):
                files.append(path)
        return files
    def _read_file_at_ref(self,ref:str,file_path:str)->str:
        try:
            blob=self.repo.commit(ref).tree/file_path
            return blob.data_stream.read().decode("utf-8",errors="ignore")
        except Exception:
            return ""
    def _module_name(self,file_path:str)->str:
        path=Path(file_path)
        parts=list(path.with_suffix("").parts)
        if parts and parts[0]=="backend":
            parts=parts[1:]
        if parts and parts[-1]=="__init__":
            parts=parts[:-1]
        return ".".join(parts)