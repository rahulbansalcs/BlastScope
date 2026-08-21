from dataclasses import dataclass,field
from typing import List,Set
from app.impact.impact_engine import ImpactAnalysis
from app.tests.test_mapper import TestMapper,TestReference
@dataclass
class UntestedComponent:
    name:str
    component_type:str
@dataclass
class TestCoverageAnalysis:
    total_components:int
    covered_components:int
    untested_components:int
    confidence_score:float
    matched_tests:List[TestReference]=field(default_factory=list)
    uncovered:List[UntestedComponent]=field(default_factory=list)
class TestCoverageAnalyzer:
    def __init__(self,test_mapper:TestMapper):
        self.test_mapper=test_mapper
    def analyze(self,repository_path:str,impact:ImpactAnalysis)->TestCoverageAnalysis:
        symbols=self._impact_symbols(impact)
        matched_tests=self.test_mapper.find_tests_for_symbols(repository_path,symbols)
        covered_symbols=self._covered_symbols(matched_tests,symbols)
        uncovered_names=[symbol for symbol in symbols if symbol not in covered_symbols]
        total=len(symbols)
        covered=len(covered_symbols)
        confidence=(covered/total*100) if total else 100.0
        uncovered=[
            UntestedComponent(
                name=name,
                component_type=self._component_type(name,impact)
            )
            for name in uncovered_names
        ]
        return TestCoverageAnalysis(
            total_components=total,
            covered_components=covered,
            untested_components=len(uncovered),
            confidence_score=round(confidence,2),
            matched_tests=matched_tests,
            uncovered=uncovered
        )
    def _impact_symbols(self,impact:ImpactAnalysis)->List[str]:
        symbols=[impact.target_name]
        symbols.extend(impact.affected_functions)
        unique=[]
        seen:Set[str]=set()
        for symbol in symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique.append(symbol)
        return unique
    def _covered_symbols(self,tests:List[TestReference],symbols:List[str])->Set[str]:
        symbol_set=set(symbols)
        covered=set()
        for test in tests:
            for referenced in test.referenced_symbols:
                if referenced in symbol_set:
                    covered.add(referenced)
        return covered
    def _component_type(self,name:str,impact:ImpactAnalysis)->str:
        if name==impact.target_name:
            return "target"
        if name in impact.affected_functions:
            return "function"
        return "unknown"