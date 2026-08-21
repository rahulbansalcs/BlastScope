import tempfile
from dataclasses import dataclass
from pathlib import Path
from git import Repo
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.graph.dependency_graph import DependencyGraph
@dataclass
class BaseRevisionResult:
    ref:str
    graph:DependencyGraph
    repository_path:str
class BaseRevisionAnalyzer:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
        self.repo=Repo(str(self.repository_path))
    def analyze(self,ref:str)->BaseRevisionResult:
        commit=self.repo.commit(ref)
        with tempfile.TemporaryDirectory(prefix="blastscope_base_") as temp_directory:
            root=Path(temp_directory)
            self._materialize_tree(commit.tree,root)
            backend_path=root/"backend"
            analysis_path=backend_path if backend_path.exists() else root
            analyzer=RepositoryAnalyzer(str(analysis_path))
            result=analyzer.analyze()
            return BaseRevisionResult(
                ref=ref,
                graph=result.graph,
                repository_path=str(analysis_path)
            )
    def _materialize_tree(self,tree,target_root:Path)->None:
        for item in tree.traverse():
            destination=target_root/item.path
            if item.type=="tree":
                destination.mkdir(parents=True,exist_ok=True)
                continue
            if item.type!="blob":
                continue
            destination.parent.mkdir(parents=True,exist_ok=True)
            try:
                data=item.data_stream.read()
                destination.write_bytes(data)
            except OSError:
                continue