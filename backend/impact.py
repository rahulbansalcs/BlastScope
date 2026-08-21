import sys
from pathlib import Path
from app.git.change_severity_analyzer import ChangeSeverityAnalyzer
from app.tests.coverage_analyzer import TestCoverageAnalyzer
from app.analyzers.architecture_analyzer import ArchitectureAnalyzer
from app.analyzers.cycle_analyzer import CycleAnalyzer
from app.git.history_analyzer import GitHistoryAnalyzer
from app.git.coupling_analyzer import CouplingAnalyzer
from app.tests.test_mapper import TestMapper
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
        cycle_analyzer=CycleAnalyzer()
        target_cycles=cycle_analyzer.cycles_for_node(repository_result.graph,node_id)
        cycle_count=len(target_cycles)
        architecture_analyzer=ArchitectureAnalyzer()
        target_architecture_violations=architecture_analyzer.violations_for_node(repository_result.graph,node_id)
        architecture_violation_count=len(target_architecture_violations)
        target_node=repository_result.graph.get_node(node_id)
        file_history=None
        coupling_result=None
        change_severity_result=None
        change_severity_score=0
        git_root=repository_path
        while git_root!=git_root.parent and not (git_root/".git").exists():
            git_root=git_root.parent
        if target_node and target_node.file_path and (git_root/".git").exists():
            try:
                target_path=Path(target_node.file_path).resolve()
                relative_path=str(target_path.relative_to(git_root))
                history_analyzer=GitHistoryAnalyzer(str(git_root))
                file_history=history_analyzer.analyze_file(relative_path)
                coupling_analyzer=CouplingAnalyzer(str(git_root))
                coupling_result=coupling_analyzer.analyze_file(relative_path)
                severity_analyzer=ChangeSeverityAnalyzer(str(git_root))
                change_severity_result=severity_analyzer.analyze_file(relative_path,"main","HEAD")
                if change_severity_result:
                    change_severity_score=change_severity_result.severity_score
            except Exception:
                file_history=None
                coupling_result=None
                change_severity_result=None
                change_severity_score=0
        test_mapper=TestMapper()
        coverage_analyzer=TestCoverageAnalyzer(test_mapper)
        coverage_result=coverage_analyzer.analyze(str(repository_path),impact_result)
        test_symbols=[impact_result.target_name]+impact_result.affected_functions
        recommended_tests=test_mapper.find_tests_for_symbols(str(repository_path),test_symbols)
        risk_engine=RiskEngine(repository_result.graph)
        risk_result=risk_engine.calculate(
            impact_result,
            file_history,
            cycle_count,
            architecture_violation_count,
            coverage_result.confidence_score,
            change_severity_score
        )
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
    print(f"Historical instability: {risk_result.breakdown.historical_instability_score}")
    print(f"Cycle risk: {risk_result.breakdown.cycle_risk_score}")
    print(f"Architecture risk: {risk_result.breakdown.architecture_risk_score}")
    print(f"Test gap risk: {risk_result.breakdown.test_gap_risk_score}")
    print(f"Change severity: {risk_result.breakdown.change_severity_score}")
    print()
    print("WHY")
    print()
    for reason in risk_result.reasons:
        print(f"- {reason}")
    if file_history:
        print()
        print("GIT HISTORY")
        print()
        print(f"Commits touching file: {file_history.commit_count}")
        print(f"Contributors: {file_history.contributors}")
        print(f"Bug-fix commits: {file_history.bugfix_commits}")
        print(f"Reverts: {file_history.revert_commits}")
        print(f"Historical instability: {file_history.instability_score}/100")
    if change_severity_result:
        print()
        print("CHANGE SIZE & DIFF SEVERITY")
        print()
        print(f"File: {change_severity_result.file_path}")
        print(f"Added lines: {change_severity_result.additions}")
        print(f"Deleted lines: {change_severity_result.deletions}")
        print(f"Total changed lines: {change_severity_result.total_changed_lines}")
        print(f"File change ratio: {change_severity_result.change_ratio}%")
        print(f"Severity: {change_severity_result.severity_score}/100")
        print(f"Severity level: {change_severity_result.severity_level}")
        print()
        print("Change reasons:")
        for reason in change_severity_result.reasons:
            print(f"- {reason}")
    if coupling_result:
        print()
        print("HIDDEN CHANGE COUPLING")
        print()
        if not coupling_result.coupled_files:
            print("No meaningful evolutionary coupling detected")
        else:
            for coupled in coupling_result.coupled_files[:10]:
                print(f"- {coupled.file_path}")
                print(f"  Shared commits: {coupled.shared_commits}")
                print(f"  Coupling score: {coupled.coupling_score}%")
    if target_cycles:
        print()
        print("CIRCULAR DEPENDENCY RISK")
        print()
        print(f"Cycles involving target: {len(target_cycles)}")
        for index,cycle in enumerate(target_cycles,1):
            print()
            print(f"Cycle #{index}")
            for cycle_node in cycle.nodes:
                print(f"- {cycle_node}")
    if target_architecture_violations:
        print()
        print("ARCHITECTURE VIOLATIONS")
        print()
        for index,violation in enumerate(target_architecture_violations,1):
            print(f"Violation #{index}")
            print(f"- Source: {violation.source_node}")
            print(f"- Target: {violation.target_node}")
            print(f"- Rule: {violation.source_layer} -> {violation.target_layer}")
            print(f"- Reason: {violation.reason}")
            print()
    print()
    print("BLAST RADIUS")
    print()
    print(f"Total affected components: {impact_result.total_affected}")
    print(f"Maximum dependency depth: {impact_result.maximum_depth}")
    print(f"Affected files: {len(impact_result.affected_files)}")
    print(f"Affected functions/methods: {len(impact_result.affected_functions)}")
    print(f"Affected classes: {len(impact_result.affected_classes)}")
    print(f"Affected API endpoints: {len(impact_result.affected_endpoints)}")
    if impact_result.affected_endpoints:
        print()
        print("AFFECTED PUBLIC API ENDPOINTS")
        print()
        for endpoint in impact_result.affected_endpoints:
            print(f"- {endpoint}")
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
    print()
    print("TEST COVERAGE CONFIDENCE")
    print()
    print(f"Components requiring validation: {coverage_result.total_components}")
    print(f"Covered components: {coverage_result.covered_components}")
    print(f"Untested components: {coverage_result.untested_components}")
    print(f"Confidence score: {coverage_result.confidence_score}%")
    if coverage_result.uncovered:
        print()
        print("UNTESTED BLAST RADIUS")
        print()
        for component in coverage_result.uncovered:
            print(f"- {component.name}")
            print(f"  Type: {component.component_type}")
    print()
    print("RECOMMENDED REGRESSION TESTS")
    print()
    if not recommended_tests:
        print("No related tests detected")
    else:
        for test in recommended_tests:
            print(f"- {test.qualified_name}")
            print(f"  {test.file_path}:{test.line}")
if __name__=="__main__":
    main()