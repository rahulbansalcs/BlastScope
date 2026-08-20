import sys
from pathlib import Path
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.impact.impact_engine import ImpactEngine
from app.risk.risk_engine import RiskEngine
def main():
    if len(sys.argv)<3:
        print("Usage: python impact.py <repository_path> <node_id>")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    node_id=sys.argv[2]
    print()
    print("BlastScope")
    print("Dependency Blast Radius Analyzer")
    print()
    print(f"Repository: {repository_path}")
    print(f"Target: {node_id}")
    print()
    try:
        repository_analyzer=RepositoryAnalyzer(str(repository_path))
        repository_result=repository_analyzer.analyze()
        impact_engine=ImpactEngine(repository_result.graph)
        impact_result=impact_engine.analyze(node_id)
        risk_engine=RiskEngine(repository_result.graph)
        risk_result=risk_engine.calculate(impact_result)
    except Exception as error:
        print(f"Analysis failed: {error}")
        sys.exit(1)
    print("Analysis complete")
    print()
    print("RISK ASSESSMENT")
    print()
    print(f"Risk Score: {risk_result.score}/100")
    print(f"Risk Level: {risk_result.level}")
    print()
    print("RISK BREAKDOWN")
    print()
    print(f"Dependency impact: {risk_result.breakdown.dependency_score}")
    print(f"Dependency depth: {risk_result.breakdown.depth_score}")
    print(f"File impact: {risk_result.breakdown.file_impact_score}")
    print(f"Function impact: {risk_result.breakdown.function_impact_score}")
    print(f"Centrality: {risk_result.breakdown.centrality_score}")
    print()
    print("WHY")
    print()
    for reason in risk_result.reasons:
        print(f"- {reason}")
    print()
    print("BLAST RADIUS")
    print()
    print(f"Total affected components: {impact_result.total_affected}")
    print(f"Maximum dependency depth: {impact_result.maximum_depth}")
    print(f"Affected files: {len(impact_result.affected_files)}")
    print(f"Affected functions/methods: {len(impact_result.affected_functions)}")
    print(f"Affected classes: {len(impact_result.affected_classes)}")
    print()
    print("DIRECT IMPACT")
    print()
    if not impact_result.direct_impact:
        print("No direct dependents detected")
    for component in impact_result.direct_impact:
        print(f"[Depth {component.depth}] {component.node_type}: {component.name}")
    print()
    print("INDIRECT IMPACT")
    print()
    if not impact_result.indirect_impact:
        print("No indirect dependents detected")
    for component in impact_result.indirect_impact:
        print(f"[Depth {component.depth}] {component.node_type}: {component.name}")
if __name__=="__main__":
    main()