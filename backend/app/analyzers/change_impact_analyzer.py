from dataclasses import dataclass,field
from pathlib import Path
from typing import List
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.git.diff_analyzer import GitDiffAnalyzer,ChangedFile
from app.git.change_mapper import ChangeMapper,ChangedSymbol
from app.impact.impact_engine import ImpactEngine,ImpactAnalysis
from app.risk.risk_engine import RiskEngine,RiskResult
@dataclass
class SymbolImpactResult:
    changed_symbol:ChangedSymbol
    impact:ImpactAnalysis
    risk:RiskResult
@dataclass
class ChangeImpactReport:
    repository_path:str
    base_ref:str
    target_ref:str
    changed_files:List[ChangedFile]=field(default_factory=list)
    changed_symbols:List[ChangedSymbol]=field(default_factory=list)
    symbol_impacts:List[SymbolImpactResult]=field(default_factory=list)
    unmapped_files:List[str]=field(default_factory=list)
    overall_risk_score:int=0
    overall_risk_level:str="LOW"
class ChangeImpactAnalyzer:
    def __init__(self,repository_path:str):
        self.repository_path=Path(repository_path).resolve()
    def analyze(self,base_ref:str="main",target_ref:str="HEAD")->ChangeImpactReport:
        repository_analyzer=RepositoryAnalyzer(str(self.repository_path))
        repository_result=repository_analyzer.analyze()
        git_analyzer=GitDiffAnalyzer(str(self.repository_path))
        diff_result=git_analyzer.analyze(base_ref,target_ref)
        mapper=ChangeMapper(str(self.repository_path))
        mapping_result=mapper.map_changes(
            diff_result,
            repository_result.parsed_files
        )
        impact_engine=ImpactEngine(repository_result.graph)
        risk_engine=RiskEngine(repository_result.graph)
        symbol_impacts=[]
        for changed_symbol in mapping_result.changed_symbols:
            node_id=f"symbol:{changed_symbol.qualified_name}"
            if repository_result.graph.get_node(node_id) is None:
                continue
            impact=impact_engine.analyze(node_id)
            risk=risk_engine.calculate(impact)
            symbol_impacts.append(
                SymbolImpactResult(
                    changed_symbol=changed_symbol,
                    impact=impact,
                    risk=risk
                )
            )
        overall_score=self._calculate_overall_risk(symbol_impacts)
        overall_level=self._risk_level(overall_score)
        return ChangeImpactReport(
            repository_path=str(self.repository_path),
            base_ref=base_ref,
            target_ref=target_ref,
            changed_files=diff_result.changed_files,
            changed_symbols=mapping_result.changed_symbols,
            symbol_impacts=symbol_impacts,
            unmapped_files=mapping_result.unmapped_files,
            overall_risk_score=overall_score,
            overall_risk_level=overall_level
        )
    def _calculate_overall_risk(self,results:List[SymbolImpactResult])->int:
        if not results:
            return 0
        scores=[result.risk.score for result in results]
        highest=max(scores)
        average=sum(scores)/len(scores)
        combined=(highest*0.7)+(average*0.3)
        return min(100,round(combined))
    def _risk_level(self,score:int)->str:
        if score<=30:
            return "LOW"
        if score<=60:
            return "MEDIUM"
        if score<=80:
            return "HIGH"
        return "CRITICAL"