from dataclasses import dataclass,field
from pathlib import Path
from typing import List,Optional
from app.analyzers.symbol_change_analyzer import SymbolChangeAnalyzer,SymbolSnapshot
from app.analyzers.base_revision_analyzer import BaseRevisionAnalyzer
@dataclass
class BrokenCaller:
    name:str
    node_type:str
    file_path:str
    depth:int
@dataclass
class RemovedSymbolImpact:
    change_type:str
    old_symbol:SymbolSnapshot
    new_symbol:Optional[SymbolSnapshot]
    confidence:float
    direct_callers:List[BrokenCaller]=field(default_factory=list)
    transitive_callers:List[BrokenCaller]=field(default_factory=list)
    affected_api_endpoints:List[BrokenCaller]=field(default_factory=list)
    total_affected:int=0
    severity:str="HIGH"
    reasons:List[str]=field(default_factory=list)
class RemovedSymbolImpactAnalyzer:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
    def analyze(self,base_ref:str="main",target_ref:str="HEAD")->List[RemovedSymbolImpact]:
        symbol_analyzer=SymbolChangeAnalyzer(str(self.repository_path))
        symbol_changes=symbol_analyzer.analyze(base_ref,target_ref)
        relevant=[
            change
            for change in symbol_changes.changes
            if change.breaking and change.change_type in {"deleted","renamed"} and change.old_symbol
        ]
        if not relevant:
            return []
        base_analyzer=BaseRevisionAnalyzer(str(self.repository_path))
        base_result=base_analyzer.analyze(base_ref)
        results=[]
        for change in relevant:
            old_symbol=change.old_symbol
            if old_symbol is None:
                continue
            node_id=f"symbol:{old_symbol.qualified_name}"
            node=base_result.graph.get_node(node_id)
            if not node:
                results.append(
                    RemovedSymbolImpact(
                        change_type=change.change_type,
                        old_symbol=old_symbol,
                        new_symbol=change.new_symbol,
                        confidence=change.confidence,
                        severity="HIGH",
                        reasons=change.reasons+["Old symbol was not found in the reconstructed base dependency graph"]
                    )
                )
                continue
            impacted=base_result.graph.get_transitive_impact(node_id)
            direct=[]
            transitive=[]
            endpoints=[]
            for impacted_node,depth in impacted:
                caller=BrokenCaller(
                    name=impacted_node.name,
                    node_type=impacted_node.node_type,
                    file_path=impacted_node.file_path,
                    depth=depth
                )
                if impacted_node.node_type=="api_endpoint":
                    endpoints.append(caller)
                elif depth==1:
                    direct.append(caller)
                else:
                    transitive.append(caller)
            severity=self._severity(
                len(direct),
                len(transitive),
                len(endpoints),
                change.change_type
            )
            reasons=list(change.reasons)
            if direct:
                reasons.append(f"{len(direct)} direct caller(s) referenced the old symbol")
            if transitive:
                reasons.append(f"{len(transitive)} transitive component(s) depended on the old symbol")
            if endpoints:
                reasons.append(f"{len(endpoints)} public API endpoint(s) depended on the old symbol")
            results.append(
                RemovedSymbolImpact(
                    change_type=change.change_type,
                    old_symbol=old_symbol,
                    new_symbol=change.new_symbol,
                    confidence=change.confidence,
                    direct_callers=direct,
                    transitive_callers=transitive,
                    affected_api_endpoints=endpoints,
                    total_affected=len(impacted),
                    severity=severity,
                    reasons=reasons
                )
            )
        return results
    def _severity(self,direct:int,transitive:int,endpoints:int,change_type:str)->str:
        score=0
        score+=direct*20
        score+=transitive*5
        score+=endpoints*25
        if change_type=="deleted":
            score+=30
        elif change_type=="renamed":
            score+=20
        if score>=80:
            return "CRITICAL"
        if score>=50:
            return "HIGH"
        if score>=20:
            return "MEDIUM"
        return "LOW"