from dataclasses import dataclass,field
from typing import Dict
from app.graph.dependency_graph import DependencyGraph
from app.impact.impact_engine import ImpactAnalysis
@dataclass
class RiskBreakdown:
    dependency_score:float
    depth_score:float
    file_impact_score:float
    function_impact_score:float
    centrality_score:float
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
    def calculate(self,impact:ImpactAnalysis)->RiskResult:
        dependency_score=self._dependency_score(impact.total_affected)
        depth_score=self._depth_score(impact.maximum_depth)
        file_impact_score=self._file_score(len(impact.affected_files))
        function_impact_score=self._function_score(len(impact.affected_functions))
        centrality_score=self._centrality_score(impact.target_id)
        total=(dependency_score*0.30)+(depth_score*0.15)+(file_impact_score*0.20)+(function_impact_score*0.20)+(centrality_score*0.15)
        final_score=min(100,max(0,round(total)))
        level=self._risk_level(final_score)
        breakdown=RiskBreakdown(
            dependency_score=round(dependency_score,2),
            depth_score=round(depth_score,2),
            file_impact_score=round(file_impact_score,2),
            function_impact_score=round(function_impact_score,2),
            centrality_score=round(centrality_score,2),
            total_score=final_score
        )
        reasons=self._build_reasons(impact,centrality_score)
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
    def _risk_level(self,score:int)->str:
        if score<=30:
            return "LOW"
        if score<=60:
            return "MEDIUM"
        if score<=80:
            return "HIGH"
        return "CRITICAL"
    def _build_reasons(self,impact:ImpactAnalysis,centrality_score:float)->list[str]:
        reasons=[]
        if impact.total_affected>10:
            reasons.append(f"{impact.total_affected} downstream components may be affected")
        if impact.maximum_depth>=3:
            reasons.append(f"Impact propagates across {impact.maximum_depth} dependency levels")
        if len(impact.affected_files)>=5:
            reasons.append(f"{len(impact.affected_files)} files are in the blast radius")
        if len(impact.affected_functions)>=5:
            reasons.append(f"{len(impact.affected_functions)} functions or methods may be affected")
        if centrality_score>=75:
            reasons.append("Target component has high dependency centrality")
        if not reasons:
            reasons.append("Change has a limited dependency blast radius")
        return reasons