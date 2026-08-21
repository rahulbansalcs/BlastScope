from dataclasses import dataclass,field
from pathlib import Path
from typing import Any,Dict,List
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.analyzers.cycle_analyzer import CycleAnalyzer
from app.analyzers.architecture_analyzer import ArchitectureAnalyzer
from app.analyzers.criticality_analyzer import CriticalityAnalyzer
from app.analyzers.dead_code_analyzer import DeadCodeAnalyzer
from app.analyzers.breaking_change_analyzer import BreakingChangeAnalyzer
from app.analyzers.symbol_change_analyzer import SymbolChangeAnalyzer
from app.analyzers.removed_symbol_impact_analyzer import RemovedSymbolImpactAnalyzer
from app.analyzers.refactor_validation_analyzer import RefactorValidationAnalyzer
from app.git.diff_analyzer import GitDiffAnalyzer
from app.git.change_severity_analyzer import ChangeSeverityAnalyzer
from app.services.graph_serializer import GraphSerializer
@dataclass
class RepositorySummary:
    path:str
    total_files:int
    python_files:int
    total_lines:int
    symbols:int
    graph_nodes:int
    graph_edges:int
    api_routes:int
    syntax_errors:int
@dataclass
class AnalysisSummary:
    repository:RepositorySummary
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
@dataclass
class FullAnalysisResult:
    summary:AnalysisSummary
    changed_files:List[Dict[str,Any]]=field(default_factory=list)
    breaking_changes:List[Dict[str,Any]]=field(default_factory=list)
    symbol_changes:List[Dict[str,Any]]=field(default_factory=list)
    removed_symbol_impacts:List[Dict[str,Any]]=field(default_factory=list)
    refactor_validations:List[Dict[str,Any]]=field(default_factory=list)
    architecture_violations:List[Dict[str,Any]]=field(default_factory=list)
    cycles:List[Dict[str,Any]]=field(default_factory=list)
    dead_code:List[Dict[str,Any]]=field(default_factory=list)
    critical_components:List[Dict[str,Any]]=field(default_factory=list)
    file_severity:List[Dict[str,Any]]=field(default_factory=list)
    dependency_graph:Dict[str,Any]=field(default_factory=dict)
class AnalysisService:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
    def run(self,base_ref:str="main",target_ref:str="HEAD")->FullAnalysisResult:
        repository_analyzer=RepositoryAnalyzer(str(self.repository_path))
        repository_result=repository_analyzer.analyze()
        graph_serializer=GraphSerializer()
        graph_snapshot=graph_serializer.serialize(repository_result.graph)
        git_analyzer=GitDiffAnalyzer(str(self.repository_path))
        diff_result=git_analyzer.analyze(base_ref,target_ref)
        cycle_analyzer=CycleAnalyzer()
        cycle_result=cycle_analyzer.analyze(repository_result.graph)
        architecture_analyzer=ArchitectureAnalyzer()
        architecture_result=architecture_analyzer.analyze(repository_result.graph)
        dead_code_analyzer=DeadCodeAnalyzer()
        dead_code_result=dead_code_analyzer.analyze(repository_result.graph)
        criticality_analyzer=CriticalityAnalyzer()
        criticality_result=criticality_analyzer.analyze(repository_result.graph,20)
        breaking_analyzer=BreakingChangeAnalyzer(str(self.repository_path))
        breaking_result=breaking_analyzer.analyze(base_ref,target_ref)
        symbol_change_analyzer=SymbolChangeAnalyzer(str(self.repository_path))
        symbol_change_result=symbol_change_analyzer.analyze(base_ref,target_ref)
        removed_impact_analyzer=RemovedSymbolImpactAnalyzer(str(self.repository_path))
        removed_impact_result=removed_impact_analyzer.analyze(base_ref,target_ref)
        refactor_analyzer=RefactorValidationAnalyzer(str(self.repository_path))
        refactor_result=refactor_analyzer.analyze(base_ref,target_ref)
        severity_analyzer=ChangeSeverityAnalyzer(str(self.repository_path))
        severity_result=severity_analyzer.analyze(base_ref,target_ref)
        risk_score=self._overall_risk(
            breaking_result,
            architecture_result.total_violations,
            cycle_result.cycle_count,
            removed_impact_result,
            severity_result.files
        )
        risk_level=self._risk_level(risk_score)
        repository_summary=RepositorySummary(
            path=str(self.repository_path),
            total_files=repository_result.repository.file_count,
            python_files=repository_result.repository.python_file_count,
            total_lines=repository_result.repository.total_lines,
            symbols=repository_result.symbol_count,
            graph_nodes=repository_result.graph_nodes,
            graph_edges=repository_result.graph_edges,
            api_routes=repository_result.api_route_count,
            syntax_errors=repository_result.syntax_error_count
        )
        summary=AnalysisSummary(
            repository=repository_summary,
            base_ref=base_ref,
            target_ref=target_ref,
            changed_files=len(diff_result.changed_files),
            breaking_changes=len(breaking_result),
            renamed_or_deleted_symbols=len([
                change
                for change in symbol_change_result.changes
                if change.change_type in {"renamed","deleted"}
            ]),
            architecture_violations=architecture_result.total_violations,
            dependency_cycles=cycle_result.cycle_count,
            dead_code_candidates=dead_code_result.total_candidates,
            critical_components=criticality_result.total_components,
            overall_risk_score=risk_score,
            overall_risk_level=risk_level
        )
        return FullAnalysisResult(
            summary=summary,
            changed_files=[
                {
                    "path":item.path,
                    "change_type":item.change_type,
                    "old_path":item.old_path,
                    "changed_lines":[
                        {
                            "start":line.start,
                            "end":line.end
                        }
                        for line in item.changed_lines
                    ]
                }
                for item in diff_result.changed_files
            ],
            breaking_changes=[
                {
                    "symbol":item.symbol,
                    "change_type":item.change_type,
                    "reasons":item.reasons,
                    "affected_callers":item.affected_callers,
                    "potential_runtime_failures":item.potential_runtime_failures
                }
                for item in breaking_result
            ],
            symbol_changes=[
                {
                    "change_type":item.change_type,
                    "breaking":item.breaking,
                    "confidence":item.confidence,
                    "old_symbol":item.old_symbol.qualified_name if item.old_symbol else None,
                    "new_symbol":item.new_symbol.qualified_name if item.new_symbol else None,
                    "reasons":item.reasons
                }
                for item in symbol_change_result.changes
            ],
            removed_symbol_impacts=[
                {
                    "change_type":item.change_type,
                    "old_symbol":item.old_symbol.qualified_name,
                    "new_symbol":item.new_symbol.qualified_name if item.new_symbol else None,
                    "severity":item.severity,
                    "total_affected":item.total_affected,
                    "direct_callers":[caller.name for caller in item.direct_callers],
                    "transitive_callers":[caller.name for caller in item.transitive_callers],
                    "affected_api_endpoints":[caller.name for caller in item.affected_api_endpoints],
                    "reasons":item.reasons
                }
                for item in removed_impact_result
            ],
            refactor_validations=[
                {
                    "old_symbol":item.old_symbol,
                    "new_symbol":item.new_symbol,
                    "change_type":item.change_type,
                    "safe_refactor":item.safe_refactor,
                    "total_old_callers":item.total_old_callers,
                    "updated_callers":item.updated_callers,
                    "broken_callers":item.broken_callers
                }
                for item in refactor_result
            ],
            architecture_violations=[
                {
                    "source":item.source_node,
                    "target":item.target_node,
                    "source_layer":item.source_layer,
                    "target_layer":item.target_layer,
                    "edge_type":item.edge_type,
                    "reason":item.reason
                }
                for item in architecture_result.violations
            ],
            cycles=[
                {
                    "nodes":item.nodes,
                    "size":item.size,
                    "edge_types":item.edge_types
                }
                for item in cycle_result.cycles
            ],
            dead_code=[
                {
                    "name":item.name,
                    "node_type":item.node_type,
                    "file_path":item.file_path,
                    "confidence":item.confidence,
                    "reasons":item.reasons
                }
                for item in dead_code_result.candidates
            ],
            critical_components=[
                {
                    "name":item.name,
                    "node_type":item.node_type,
                    "file_path":item.file_path,
                    "criticality_score":item.criticality_score,
                    "direct_dependents":item.direct_dependents,
                    "transitive_dependents":item.transitive_dependents,
                    "api_endpoints":item.api_endpoints,
                    "dependency_depth":item.dependency_depth,
                    "reasons":item.reasons
                }
                for item in criticality_result.components
            ],
            file_severity=[
                {
                    "file_path":item.file_path,
                    "additions":item.additions,
                    "deletions":item.deletions,
                    "total_changed_lines":item.total_changed_lines,
                    "change_ratio":item.change_ratio,
                    "severity_score":item.severity_score,
                    "severity_level":item.severity_level
                }
                for item in severity_result.files
            ],
            dependency_graph={
                "nodes":graph_snapshot.nodes,
                "edges":graph_snapshot.edges
            }
        )
    def _overall_risk(self,breaking_changes,architecture_violations:int,cycles:int,removed_impacts,severity_files)->int:
        score=0
        if breaking_changes:
            score+=min(len(breaking_changes)*15,30)
        if architecture_violations:
            score+=min(architecture_violations*5,15)
        if cycles:
            score+=min(cycles*7,15)
        if removed_impacts:
            score+=min(len(removed_impacts)*15,25)
        if severity_files:
            highest=max(item.severity_score for item in severity_files)
            score+=round(highest*0.15)
        return min(100,score)
    def _risk_level(self,score:int)->str:
        if score<=30:
            return "LOW"
        if score<=60:
            return "MEDIUM"
        if score<=80:
            return "HIGH"
        return "CRITICAL"