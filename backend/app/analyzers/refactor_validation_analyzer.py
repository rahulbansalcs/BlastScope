import ast
from dataclasses import dataclass,field
from pathlib import Path
from typing import List,Optional
from git import Repo
from app.analyzers.symbol_change_analyzer import SymbolChangeAnalyzer
from app.analyzers.base_revision_analyzer import BaseRevisionAnalyzer
@dataclass
class CallerValidation:
    caller_name:str
    caller_file:str
    old_reference:str
    new_reference:Optional[str]
    updated:bool
    status:str
@dataclass
class RefactorValidationResult:
    old_symbol:str
    new_symbol:Optional[str]
    change_type:str
    safe_refactor:bool
    total_old_callers:int
    updated_callers:int
    broken_callers:int
    callers:List[CallerValidation]=field(default_factory=list)
class RefactorValidationAnalyzer:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
        self.repo=Repo(str(self.repository_path))
    def analyze(self,base_ref:str="main",target_ref:str="HEAD")->List[RefactorValidationResult]:
        symbol_analyzer=SymbolChangeAnalyzer(str(self.repository_path))
        symbol_changes=symbol_analyzer.analyze(base_ref,target_ref)
        relevant=[
            change
            for change in symbol_changes.changes
            if change.change_type in {"renamed","deleted"} and change.old_symbol
        ]
        if not relevant:
            return []
        base_analyzer=BaseRevisionAnalyzer(str(self.repository_path))
        base_result=base_analyzer.analyze(base_ref)
        results=[]
        for change in relevant:
            old_symbol=change.old_symbol
            if old_symbol is None:
                continue
            node_id=f"symbol:{old_symbol.qualified_name}"
            old_callers=[]
            if base_result.graph.get_node(node_id):
                old_callers=[
                    node
                    for node,depth in base_result.graph.get_transitive_impact(node_id,max_depth=1)
                    if node.node_type in {"function","method"}
                ]
            validations=[]
            updated_count=0
            broken_count=0
            old_simple=old_symbol.name
            new_simple=change.new_symbol.name if change.new_symbol else None
            for caller in old_callers:
                relative_file=self._relative_file(caller.file_path,base_result.repository_path)
                target_source=self._read_target_file(target_ref,relative_file)
                updated,new_reference=self._validate_caller(
                    target_source,
                    old_simple,
                    new_simple
                )
                status="UPDATED" if updated else "BROKEN"
                if updated:
                    updated_count+=1
                else:
                    broken_count+=1
                validations.append(
                    CallerValidation(
                        caller_name=caller.name,
                        caller_file=relative_file,
                        old_reference=old_simple,
                        new_reference=new_reference,
                        updated=updated,
                        status=status
                    )
                )
            safe_refactor=broken_count==0 and len(old_callers)>0
            results.append(
                RefactorValidationResult(
                    old_symbol=old_symbol.qualified_name,
                    new_symbol=change.new_symbol.qualified_name if change.new_symbol else None,
                    change_type=change.change_type,
                    safe_refactor=safe_refactor,
                    total_old_callers=len(old_callers),
                    updated_callers=updated_count,
                    broken_callers=broken_count,
                    callers=validations
                )
            )
        return results
    def _validate_caller(self,source:str,old_name:str,new_name:Optional[str]):
        if not source:
            return False,None
        try:
            tree=ast.parse(source)
        except SyntaxError:
            return False,None
        old_found=False
        new_found=False
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                name=self._call_name(node.func).rsplit(".",1)[-1]
                if name==old_name:
                    old_found=True
                if new_name and name==new_name:
                    new_found=True
            elif isinstance(node,ast.ImportFrom):
                for item in node.names:
                    if item.name==old_name:
                        old_found=True
                    if new_name and item.name==new_name:
                        new_found=True
            elif isinstance(node,ast.Import):
                for item in node.names:
                    last=item.name.rsplit(".",1)[-1]
                    if last==old_name:
                        old_found=True
                    if new_name and last==new_name:
                        new_found=True
        if new_name:
            if new_found and not old_found:
                return True,new_name
            return False,new_name if new_found else None
        return not old_found,None
    def _read_target_file(self,ref:str,file_path:str)->str:
        candidates=[
            file_path,
            f"backend/{file_path}"
        ]
        for candidate in candidates:
            try:
                blob=self.repo.commit(ref).tree/candidate
                return blob.data_stream.read().decode("utf-8",errors="ignore")
            except Exception:
                continue
        return ""
    def _relative_file(self,file_path:str,base_repository_path:str)->str:
        path=Path(file_path).resolve()
        base=Path(base_repository_path).resolve()
        try:
            return str(path.relative_to(base))
        except ValueError:
            return str(path)
    def _call_name(self,node:ast.AST)->str:
        if isinstance(node,ast.Name):
            return node.id
        if isinstance(node,ast.Attribute):
            parent=self._call_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""