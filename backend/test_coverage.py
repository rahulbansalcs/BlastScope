import sys
from pathlib import Path
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.impact.impact_engine import ImpactEngine
from app.tests.test_mapper import TestMapper
from app.tests.coverage_analyzer import TestCoverageAnalyzer
def main():
    if len(sys.argv)<3:
        print("Usage: python test_coverage.py <repository_path> <node_id>")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    node_id=sys.argv[2]
    try:
        repository_analyzer=RepositoryAnalyzer(str(repository_path))
        repository_result=repository_analyzer.analyze()
        impact_engine=ImpactEngine(repository_result.graph)
        impact_result=impact_engine.analyze(node_id)
        test_mapper=TestMapper()
        analyzer=TestCoverageAnalyzer(test_mapper)
        result=analyzer.analyze(str(repository_path),impact_result)
    except Exception as error:
        print(f"Test coverage analysis failed: {error}")
        sys.exit(1)
    print()
    print("BlastScope")
    print("Test Coverage Confidence")
    print()
    print(f"Target: {impact_result.target_name}")
    print(f"Components requiring validation: {result.total_components}")
    print(f"Covered components: {result.covered_components}")
    print(f"Untested components: {result.untested_components}")
    print(f"Test confidence: {result.confidence_score}%")
    print()
    if result.matched_tests:
        print("RELATED TESTS")
        print()
        for test in result.matched_tests:
            print(f"- {test.qualified_name}")
            print(f"  {test.file_path}:{test.line}")
    if result.uncovered:
        print()
        print("UNTESTED BLAST RADIUS")
        print()
        for component in result.uncovered:
            print(f"- {component.name}")
            print(f"  Type: {component.component_type}")
if __name__=="__main__":
    main()