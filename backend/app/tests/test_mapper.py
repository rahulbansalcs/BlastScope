import ast
from dataclasses import dataclass,field
from pathlib import Path
from typing import Dict,List,Set,Optional
@dataclass
class TestReference:
    test_name:str
    qualified_name:str
    file_path:str
    line:int
    referenced_symbols:List[str]=field(default_factory=list)
class TestMapper:
    def analyze_repository(self,repository_path:str)->List[TestReference]:
        repository=Path(repository_path).resolve()
        tests=[]
        for file_path in repository.rglob("*.py"):
            if self._excluded(file_path):
                continue
            if not self._is_test_file(file_path):
                continue
            try:
                source=file_path.read_text(encoding="utf-8",errors="ignore")
                tree=ast.parse(source,filename=str(file_path))
            except SyntaxError:
                continue
            module_name=self._module_name(repository,file_path)
            imports=self._build_import_map(tree,module_name)
            tests.extend(self._extract_tests(tree,module_name,str(file_path),imports))
        return tests
    def find_tests_for_symbol(self,repository_path:str,symbol_name:str)->List[TestReference]:
        return self.find_tests_for_symbols(repository_path,[symbol_name])
    def find_tests_for_symbols(self,repository_path:str,symbol_names:List[str])->List[TestReference]:
        targets=set(symbol_names)
        tests=self.analyze_repository(repository_path)
        matched=[]
        seen:Set[str]=set()
        for test in tests:
            if targets.intersection(test.referenced_symbols):
                key=f"{test.file_path}:{test.qualified_name}"
                if key not in seen:
                    seen.add(key)
                    matched.append(test)
        return matched
    def _extract_tests(self,tree:ast.AST,module_name:str,file_path:str,imports:Dict[str,str])->List[TestReference]:
        tests=[]
        for node in ast.walk(tree):
            if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            references=set()
            for child in ast.walk(node):
                if isinstance(child,ast.Call):
                    resolved=self._resolve_call(child.func,module_name,imports)
                    if resolved:
                        references.add(resolved)
            tests.append(
                TestReference(
                    test_name=node.name,
                    qualified_name=f"{module_name}.{node.name}",
                    file_path=file_path,
                    line=node.lineno,
                    referenced_symbols=sorted(references)
                )
            )
        return tests
    def _build_import_map(self,tree:ast.AST,module_name:str)->Dict[str,str]:
        imports={}
        for node in tree.body:
            if isinstance(node,ast.Import):
                for item in node.names:
                    visible=item.asname or item.name.split(".")[-1]
                    imports[visible]=item.name
            elif isinstance(node,ast.ImportFrom):
                module=self._resolve_relative_module(module_name,node.module or "",node.level)
                for item in node.names:
                    visible=item.asname or item.name
                    target=f"{module}.{item.name}" if module else item.name
                    imports[visible]=target
        return imports
    def _resolve_call(self,node:ast.AST,module_name:str,imports:Dict[str,str])->Optional[str]:
        if isinstance(node,ast.Name):
            if node.id in imports:
                return imports[node.id]
            return f"{module_name}.{node.id}"
        if isinstance(node,ast.Attribute):
            expression=self._call_name(node)
            if not expression:
                return None
            first,*rest=expression.split(".")
            if first in imports:
                return ".".join([imports[first],*rest])
            return f"{module_name}.{expression}"
        return None
    def _call_name(self,node:ast.AST)->str:
        if isinstance(node,ast.Name):
            return node.id
        if isinstance(node,ast.Attribute):
            parent=self._call_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""
    def _resolve_relative_module(self,current_module:str,import_module:str,level:int)->str:
        if level==0:
            return import_module
        parts=current_module.split(".")[:-1]
        remove=max(level-1,0)
        if remove:
            parts=parts[:-remove] if remove<=len(parts) else []
        if import_module:
            parts.extend(import_module.split("."))
        return ".".join(parts)
    def _is_test_file(self,path:Path)->bool:
        return path.name.startswith("test_") or "tests" in path.parts
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