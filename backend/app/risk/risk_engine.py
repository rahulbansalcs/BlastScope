from dataclasses import dataclass,field
from typing import Optional
from app.graph.dependency_graph import DependencyGraph
from app.impact.impact_engine import ImpactAnalysis
from app.git.history_analyzer import FileHistory
@dataclass
class RiskBreakdown:
    dependency_score:float
    depth_score:float
    file_impact_score:float
    function_impact_score:float
    centrality_score:float
    historical_instability_score:float
    cycle_risk_score:float
    architecture_risk_score:float
    test_gap_risk_score:float
    change_severity_score:float
    total_score:float
@dataclass
class RiskResult:
    score:int
    level:str
    breakdown:RiskBreakdown
    reasons:list[str]=field(default_factory=list)
class RiskEngine:
    def __init__(self,graph:DependencyGraph):
        self.graph=graph
    def calculate(self,impact:ImpactAnalysis,file_history:Optional[FileHistory]=None,cycle_count:int=0,architecture_violations:int=0,test_confidence:float=100.0,change_severity:float=0.0)->RiskResult:
        dependency_score=self._dependency_score(impact.total_affected)
        depth_score=self._depth_score(impact.maximum_depth)
        file_impact_score=self._file_score(len(impact.affected_files))
        function_impact_score=self._function_score(len(impact.affected_functions))
        centrality_score=self._centrality_score(impact.target_id)
        historical_score=file_history.instability_score if file_history else 0
        cycle_score=self._cycle_score(cycle_count)
        architecture_score=self._architecture_score(architecture_violations)
        test_gap_score=max(0,min(100,100-test_confidence))
        change_severity_score=max(0,min(100,change_severity))
        total=(dependency_score*0.16)+(depth_score*0.09)+(file_impact_score*0.09)+(function_impact_score*0.09)+(centrality_score*0.11)+(historical_score*0.09)+(cycle_score*0.09)+(architecture_score*0.09)+(test_gap_score*0.09)+(change_severity_score*0.10)
        final_score=min(100,max(0,round(total)))
        level=self._risk_level(final_score)
        breakdown=RiskBreakdown(
            dependency_score=round(dependency_score,2),
            depth_score=round(depth_score,2),
            file_impact_score=round(file_impact_score,2),
            function_impact_score=round(function_impact_score,2),
            centrality_score=round(centrality_score,2),
            historical_instability_score=round(historical_score,2),
            cycle_risk_score=round(cycle_score,2),
            architecture_risk_score=round(architecture_score,2),
            test_gap_risk_score=round(test_gap_score,2),
            change_severity_score=round(change_severity_score,2),
            total_score=final_score
        )
        reasons=self._build_reasons(impact,centrality_score,file_history,cycle_count,architecture_violations,test_confidence,change_severity_score)
        return RiskResult(
            score=final_score,
            level=level,
            breakdown=breakdown,
            reasons=reasons
        )
    def _dependency_score(self,count:int)->float:
        if count==0:
            return 0
        if count<=3:
            return 25
        if count<=10:
            return 50
        if count<=25:
            return 75
        return 100
    def _depth_score(self,depth:int)->float:
        if depth==0:
            return 0
        if depth==1:
            return 25
        if depth==2:
            return 50
        if depth<=4:
            return 75
        return 100
    def _file_score(self,count:int)->float:
        if count==0:
            return 0
        if count<=2:
            return 25
        if count<=5:
            return 50
        if count<=10:
            return 75
        return 100
    def _function_score(self,count:int)->float:
        if count==0:
            return 0
        if count<=3:
            return 25
        if count<=8:
            return 50
        if count<=15:
            return 75
        return 100
    def _centrality_score(self,node_id:str)->float:
        if node_id not in self.graph.nodes:
            return 0
        incoming=len(self.graph.incoming.get(node_id,[]))
        outgoing=len(self.graph.outgoing.get(node_id,[]))
        degree=incoming+outgoing
        if degree==0:
            return 0
        if degree<=2:
            return 25
        if degree<=5:
            return 50
        if degree<=10:
            return 75
        return 100
    def _cycle_score(self,cycle_count:int)->float:
        if cycle_count==0:
            return 0
        if cycle_count==1:
            return 50
        if cycle_count<=3:
            return 75
        return 100
    def _architecture_score(self,violations:int)->float:
        if violations==0:
            return 0
        if violations==1:
            return 50
        if violations<=3:
            return 75
        return 100
    def _risk_level(self,score:int)->str:
        if score<=30:
            return "LOW"
        if score<=60:
            return "MEDIUM"
        if score<=80:
            return "HIGH"
        return "CRITICAL"
    def _build_reasons(self,impact:ImpactAnalysis,centrality_score:float,file_history:Optional[FileHistory],cycle_count:int,architecture_violations:int,test_confidence:float,change_severity:float)->list[str]:
        reasons=[]
        if impact.total_affected>=5:
            reasons.append(f"{impact.total_affected} downstream components may be affected")
        if impact.maximum_depth>=2:
            reasons.append(f"Impact propagates across {impact.maximum_depth} dependency levels")
        if len(impact.affected_files)>=4:
            reasons.append(f"{len(impact.affected_files)} files are inside the blast radius")
        if len(impact.affected_functions)>=4:
            reasons.append(f"{len(impact.affected_functions)} functions or methods may be affected")
        if impact.affected_endpoints:
            reasons.append(f"{len(impact.affected_endpoints)} public API endpoint(s) may be affected")
        if centrality_score>=75:
            reasons.append("Target component has high dependency centrality")
        if cycle_count>0:
            reasons.append(f"Target participates in {cycle_count} circular dependency cycle(s)")
        if architecture_violations>0:
            reasons.append(f"Target participates in {architecture_violations} architecture violation(s)")
        if test_confidence<50:
            reasons.append(f"Only {round(test_confidence,2)}% of affected symbols have related regression tests")
        elif test_confidence<80:
            reasons.append(f"Test coverage confidence is moderate at {round(test_confidence,2)}%")
        if change_severity>=75:
            reasons.append(f"Change size is high risk with severity {round(change_severity,2)}/100")
        elif change_severity>=50:
            reasons.append(f"Change size is moderately large with severity {round(change_severity,2)}/100")
        if file_history:
            if file_history.instability_score>=60:
                reasons.append(f"File has high historical instability ({file_history.instability_score}/100)")
            if file_history.bugfix_commits>0:
                reasons.append(f"File appears in {file_history.bugfix_commits} bug-fix commit(s)")
            if file_history.revert_commits>0:
                reasons.append(f"File appears in {file_history.revert_commits} revert or rollback commit(s)")
        if not reasons:
            reasons.append("Change has a low observed dependency and historical risk")
        return reasons