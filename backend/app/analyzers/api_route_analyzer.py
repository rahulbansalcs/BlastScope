import ast
from dataclasses import dataclass,field
from pathlib import Path
from typing import List
@dataclass
class ApiRoute:
    framework:str
    method:str
    path:str
    qualified_handler:str
    file_path:str
    line:int
@dataclass
class ApiRouteAnalysis:
    routes:List[ApiRoute]=field(default_factory=list)
class ApiRouteAnalyzer:
    def analyze_repository(self,repository_path:str)->ApiRouteAnalysis:
        repository=Path(repository_path).resolve()
        routes=[]
        for file_path in repository.rglob("*.py"):
            if self._excluded(file_path):
                continue
            try:
                source=file_path.read_text(encoding="utf-8",errors="ignore")
                tree=ast.parse(source,filename=str(file_path))
            except SyntaxError:
                continue
            module_name=self._module_name(repository,file_path)
            routes.extend(self._extract_routes(tree,module_name,str(file_path)))
        return ApiRouteAnalysis(routes=routes)
    def _extract_routes(self,tree:ast.AST,module_name:str,file_path:str)->List[ApiRoute]:
        routes=[]
        for node in ast.walk(tree):
            if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                continue
            handler=f"{module_name}.{node.name}"
            for decorator in node.decorator_list:
                fastapi_route=self._parse_fastapi_route(decorator,handler,file_path,node.lineno)
                if fastapi_route:
                    routes.append(fastapi_route)
                    continue
                flask_routes=self._parse_flask_route(decorator,handler,file_path,node.lineno)
                if flask_routes:
                    routes.extend(flask_routes)
        return routes
    def _parse_fastapi_route(self,decorator:ast.AST,handler:str,file_path:str,line:int):
        if not isinstance(decorator,ast.Call):
            return None
        if not isinstance(decorator.func,ast.Attribute):
            return None
        method=decorator.func.attr.lower()
        allowed={"get","post","put","patch","delete","options","head"}
        if method not in allowed:
            return None
        if not decorator.args:
            return None
        path=self._string_value(decorator.args[0])
        if not path:
            return None
        return ApiRoute(
            framework="fastapi",
            method=method.upper(),
            path=path,
            qualified_handler=handler,
            file_path=file_path,
            line=line
        )
    def _parse_flask_route(self,decorator:ast.AST,handler:str,file_path:str,line:int):
        if not isinstance(decorator,ast.Call):
            return None
        if not isinstance(decorator.func,ast.Attribute):
            return None
        if decorator.func.attr!="route":
            return None
        if not decorator.args:
            return None
        path=self._string_value(decorator.args[0])
        if not path:
            return None
        methods=["GET"]
        for keyword in decorator.keywords:
            if keyword.arg=="methods" and isinstance(keyword.value,(ast.List,ast.Tuple)):
                parsed=[]
                for item in keyword.value.elts:
                    value=self._string_value(item)
                    if value:
                        parsed.append(value.upper())
                if parsed:
                    methods=parsed
        return [
            ApiRoute(
                framework="flask",
                method=method,
                path=path,
                qualified_handler=handler,
                file_path=file_path,
                line=line
            )
            for method in methods
        ]
    def _string_value(self,node:ast.AST)->str:
        if isinstance(node,ast.Constant) and isinstance(node.value,str):
            return node.value
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