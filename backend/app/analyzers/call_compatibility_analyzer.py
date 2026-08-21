import ast
from dataclasses import dataclass,field
from pathlib import Path
from typing import List,Optional
from app.analyzers.signature_analyzer import FunctionSignature
@dataclass
class CallSite:
    caller:str
    file_path:str
    line:int
    positional_count:int
    keyword_names:List[str]=field(default_factory=list)
@dataclass
class CallCompatibilityResult:
    caller:str
    file_path:str
    line:int
    compatible:bool
    expected_required:int
    provided_positional:int
    reasons:List[str]=field(default_factory=list)
class CallCompatibilityAnalyzer:
    def find_calls(self,repository_path:str,target_name:str)->List[CallSite]:
        repository=Path(repository_path).resolve()
        results=[]
        for file_path in repository.rglob("*.py"):
            if self._excluded(file_path):
                continue
            try:
                source=file_path.read_text(encoding="utf-8",errors="ignore")
                tree=ast.parse(source,filename=str(file_path))
            except SyntaxError:
                continue
            module_name=self._module_name(repository,file_path)
            for node in ast.walk(tree):
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    caller=f"{module_name}.{node.name}"
                    for child in ast.walk(node):
                        if isinstance(child,ast.Call):
                            call_name=self._call_name(child.func)
                            if call_name==target_name or call_name.endswith(f".{target_name}"):
                                results.append(
                                    CallSite(
                                        caller=caller,
                                        file_path=str(file_path),
                                        line=child.lineno,
                                        positional_count=len(child.args),
                                        keyword_names=[
                                            keyword.arg
                                            for keyword in child.keywords
                                            if keyword.arg is not None
                                        ]
                                    )
                                )
        return results
    def analyze(self,signature:FunctionSignature,calls:List[CallSite])->List[CallCompatibilityResult]:
        results=[]
        required=len(signature.positional_args)-signature.defaults_count
        if signature.positional_args and signature.positional_args[0] in {"self","cls"}:
            required-=1
        required=max(required,0)
        for call in calls:
            reasons=[]
            provided=call.positional_count
            if provided<required:
                reasons.append(
                    f"Expected at least {required} positional arguments but received {provided}"
                )
            maximum=None
            positional_total=len(signature.positional_args)
            if signature.positional_args and signature.positional_args[0] in {"self","cls"}:
                positional_total-=1
            if not signature.has_varargs:
                maximum=max(positional_total,0)
                if provided>maximum:
                    reasons.append(
                        f"Expected at most {maximum} positional arguments but received {provided}"
                    )
            results.append(
                CallCompatibilityResult(
                    caller=call.caller,
                    file_path=call.file_path,
                    line=call.line,
                    compatible=len(reasons)==0,
                    expected_required=required,
                    provided_positional=provided,
                    reasons=reasons
                )
            )
        return results
    def _call_name(self,node:ast.AST)->str:
        if isinstance(node,ast.Name):
            return node.id
        if isinstance(node,ast.Attribute):
            parent=self._call_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""
    def _module_name(self,repository:Path,file_path:Path)->str:
        try:
            relative=file_path.relative_to(repository)
        except ValueError:
            relative=file_path
        parts=list(relative.with_suffix("").parts)
        if parts and parts[-1]=="__init__":
            parts=parts[:-1]
        return ".".join(parts)
    def _excluded(self,path:Path)->bool:
        excluded={
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            "dist",
            "build"
        }
        return any(part in excluded for part in path.parts)