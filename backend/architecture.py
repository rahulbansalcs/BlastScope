import sys
from pathlib import Path
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.analyzers.architecture_analyzer import ArchitectureAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python architecture.py <repository_path>")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    try:
        repository_analyzer=RepositoryAnalyzer(str(repository_path))
        repository_result=repository_analyzer.analyze()
        analyzer=ArchitectureAnalyzer()
        result=analyzer.analyze(repository_result.graph)
    except Exception as error:
        print(f"Architecture analysis failed: {error}")
        sys.exit(1)
    print()
    print("BlastScope")
    print("Architecture Violation Analysis")
    print()
    print(f"Repository: {repository_path}")
    print(f"Violations detected: {result.total_violations}")
    print()
    if not result.violations:
        print("No architecture violations detected")
        return
    for index,violation in enumerate(result.violations,1):
        print("="*70)
        print()
        print(f"Violation #{index}")
        print(f"Source: {violation.source_node}")
        print(f"Target: {violation.target_node}")
        print(f"Source layer: {violation.source_layer}")
        print(f"Target layer: {violation.target_layer}")
        print(f"Dependency type: {violation.edge_type}")
        print(f"File: {violation.file_path}")
        print(f"Reason: {violation.reason}")
        print()
if __name__=="__main__":
    main()