from pathlib import Path
from fastapi import APIRouter,HTTPException,Query
from pydantic import BaseModel
from app.analyzers.repository_analyzer import RepositoryAnalyzer
router=APIRouter(prefix="/api/repositories",tags=["repositories"])
class RepositorySummaryResponse(BaseModel):
    repository_path:str
    total_files:int
    python_files:int
    total_lines:int
    symbols:int
    graph_nodes:int
    graph_edges:int
    api_routes:int
    syntax_errors:int
@router.get("/summary",response_model=RepositorySummaryResponse)
def repository_summary(repository_path:str=Query(...,min_length=1)):
    path=Path(repository_path).resolve()
    if not path.exists():
        raise HTTPException(status_code=404,detail="Repository path does not exist")
    if not path.is_dir():
        raise HTTPException(status_code=400,detail="Repository path must be a directory")
    try:
        analyzer=RepositoryAnalyzer(str(path))
        result=analyzer.analyze()
        return {
            "repository_path":str(path),
            "total_files":result.repository.file_count,
            "python_files":result.repository.python_file_count,
            "total_lines":result.repository.total_lines,
            "symbols":result.symbol_count,
            "graph_nodes":result.graph_nodes,
            "graph_edges":result.graph_edges,
            "api_routes":result.api_route_count,
            "syntax_errors":result.syntax_error_count
        }
    except Exception as error:
        raise HTTPException(status_code=500,detail=f"Repository analysis failed: {error}") from error