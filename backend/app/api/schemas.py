from typing import List,Optional
from pydantic import BaseModel
from typing import Any,Dict,List,Optional
class RepositorySummarySchema(BaseModel):
    path:str
    total_files:int
    python_files:int
    total_lines:int
    symbols:int
    graph_nodes:int
    graph_edges:int
    api_routes:int
    syntax_errors:int
class AnalysisSummarySchema(BaseModel):
    repository:RepositorySummarySchema
    base_ref:str
    target_ref:str
    changed_files:int
    breaking_changes:int
    renamed_or_deleted_symbols:int
    architecture_violations:int
    dependency_cycles:int
    dead_code_candidates:int
    critical_components:int
    overall_risk_score:int
    overall_risk_level:str
class ChangedLineSchema(BaseModel):
    start:int
    end:int
class ChangedFileSchema(BaseModel):
    path:str
    change_type:str
    old_path:Optional[str]=None
    changed_lines:List[ChangedLineSchema]
class BreakingChangeSchema(BaseModel):
    symbol:str
    change_type:str
    reasons:List[str]
    affected_callers:List[str]
    potential_runtime_failures:int
class SymbolChangeSchema(BaseModel):
    change_type:str
    breaking:bool
    confidence:float
    old_symbol:Optional[str]=None
    new_symbol:Optional[str]=None
    reasons:List[str]
class RemovedSymbolImpactSchema(BaseModel):
    change_type:str
    old_symbol:str
    new_symbol:Optional[str]=None
    severity:str
    total_affected:int
    direct_callers:List[str]
    transitive_callers:List[str]
    affected_api_endpoints:List[str]
    reasons:List[str]
class RefactorValidationSchema(BaseModel):
    old_symbol:str
    new_symbol:Optional[str]=None
    change_type:str
    safe_refactor:bool
    total_old_callers:int
    updated_callers:int
    broken_callers:int
class ArchitectureViolationSchema(BaseModel):
    source:str
    target:str
    source_layer:str
    target_layer:str
    edge_type:str
    reason:str
class CycleSchema(BaseModel):
    nodes:List[str]
    size:int
    edge_types:List[str]
class DeadCodeSchema(BaseModel):
    name:str
    node_type:str
    file_path:str
    confidence:str
    reasons:List[str]
class CriticalComponentSchema(BaseModel):
    name:str
    node_type:str
    file_path:str
    criticality_score:int
    direct_dependents:int
    transitive_dependents:int
    api_endpoints:int
    dependency_depth:int
    reasons:List[str]
class FileSeveritySchema(BaseModel):
    file_path:str
    additions:int
    deletions:int
    total_changed_lines:int
    change_ratio:float
    severity_score:int
    severity_level:str
class DependencyGraphNodeSchema(BaseModel):
    id:str
    name:str
    node_type:str
    file_path:str
    direct_dependents:int
    direct_dependencies:int
class DependencyGraphEdgeSchema(BaseModel):
    id:str
    source:str
    target:str
    edge_type:str
class DependencyGraphSchema(BaseModel):
    nodes:List[DependencyGraphNodeSchema]
    edges:List[DependencyGraphEdgeSchema]
class FullAnalysisResponseSchema(BaseModel):
    summary:AnalysisSummarySchema
    changed_files:List[ChangedFileSchema]
    breaking_changes:List[BreakingChangeSchema]
    symbol_changes:List[SymbolChangeSchema]
    removed_symbol_impacts:List[RemovedSymbolImpactSchema]
    refactor_validations:List[RefactorValidationSchema]
    architecture_violations:List[ArchitectureViolationSchema]
    cycles:List[CycleSchema]
    dead_code:List[DeadCodeSchema]
    critical_components:List[CriticalComponentSchema]
    file_severity:List[FileSeveritySchema]
    dependency_graph:DependencyGraphSchema
class AnalysisRequestSchema(BaseModel):
    repository_path:str
    base_ref:str="main"
    target_ref:str="HEAD"
class HealthResponseSchema(BaseModel):
    status:str
class RemoteAnalysisRequestSchema(BaseModel):
    repository_url:str
    base_ref:str="main"
    target_ref:str="HEAD"
    branch:Optional[str]=None
class RemoteAnalysisResponseSchema(BaseModel):
    repository_url:str
    branch:Optional[str]=None
    commit:str
    analysis:FullAnalysisResponseSchema
