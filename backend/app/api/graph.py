from pathlib import Path
from fastapi import APIRouter,HTTPException,Query
from pydantic import BaseModel
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.services.graph_serializer import GraphSerializer
router=APIRouter(prefix="/api/graph",tags=["graph"])
class GraphNodeSchema(BaseModel):
    id:str
    name:str
    node_type:str
    file_path:str
    direct_dependents:int
    direct_dependencies:int
    is_target:bool|None=None
class GraphEdgeSchema(BaseModel):
    id:str
    source:str
    target:str
    edge_type:str
class GraphResponseSchema(BaseModel):
    nodes:list[GraphNodeSchema]
    edges:list[GraphEdgeSchema]
@router.get("/blast-radius",response_model=GraphResponseSchema)
def blast_radius(repository_path:str=Query(...,min_length=1),node_id:str=Query(...,min_length=1),max_depth:int=Query(5,ge=1,le=10)):
    path=Path(repository_path).resolve()
    if not path.exists():
        raise HTTPException(status_code=404,detail="Repository path does not exist")
    if not path.is_dir():
        raise HTTPException(status_code=400,detail="Repository path must be a directory")
    try:
        analyzer=RepositoryAnalyzer(str(path))
        result=analyzer.analyze()
        if node_id not in result.graph.nodes:
            raise HTTPException(status_code=404,detail="Graph node not found")
        serializer=GraphSerializer()
        snapshot=serializer.blast_radius(
            result.graph,
            node_id,
            max_depth=max_depth
        )
        return {
            "nodes":snapshot.nodes,
            "edges":snapshot.edges
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500,detail=f"Graph analysis failed: {error}") from error