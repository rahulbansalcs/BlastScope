from dataclasses import dataclass
from pathlib import Path
from typing import List
from app.scanner.repository_scanner import RepositoryScanner,RepositoryInfo
from app.parsers.python_parser import PythonParser,ParsedPythonFile
from app.symbols.symbol_table import SymbolTable
from app.graph.dependency_graph import DependencyGraph
from app.graph.graph_builder import GraphBuilder
@dataclass
class RepositoryAnalysisResult:
    repository:RepositoryInfo
    parsed_files:List[ParsedPythonFile]
    symbol_count:int
    graph_nodes:int
    graph_edges:int
    syntax_error_count:int
    graph:DependencyGraph
class RepositoryAnalyzer:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
        self.scanner=RepositoryScanner(str(self.repository_path))
        self.parser=PythonParser(str(self.repository_path))
        self.symbol_table=SymbolTable()
    def analyze(self)->RepositoryAnalysisResult:
        repository_info=self.scanner.scan()
        parsed_files=self._parse_files(repository_info.python_files)
        self._build_symbol_table(parsed_files)
        graph=self._build_graph(parsed_files)
        syntax_error_count=sum(1 for parsed_file in parsed_files if parsed_file.syntax_error)
        stats=graph.stats()
        return RepositoryAnalysisResult(
            repository=repository_info,
            parsed_files=parsed_files,
            symbol_count=len(self.symbol_table.get_all_symbols()),
            graph_nodes=stats["nodes"],
            graph_edges=stats["edges"],
            syntax_error_count=syntax_error_count,
            graph=graph
        )
    def _parse_files(self,relative_paths:List[str])->List[ParsedPythonFile]:
        parsed_files=[]
        for relative_path in relative_paths:
            full_path=self.repository_path/relative_path
            parsed_files.append(self.parser.parse_file(str(full_path)))
        return parsed_files
    def _build_symbol_table(self,parsed_files:List[ParsedPythonFile])->None:
        for parsed_file in parsed_files:
            if parsed_file.syntax_error:
                continue
            self.symbol_table.add_parsed_file(parsed_file)
    def _build_graph(self,parsed_files:List[ParsedPythonFile])->DependencyGraph:
        valid_files=[parsed_file for parsed_file in parsed_files if not parsed_file.syntax_error]
        builder=GraphBuilder(self.symbol_table)
        return builder.build(valid_files)