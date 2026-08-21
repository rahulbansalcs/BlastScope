import sys
from pathlib import Path
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.analyzers.criticality_analyzer import CriticalityAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python criticality.py <repository_path> [limit]")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    limit=int(sys.argv[2]) if len(sys.argv)>2 else 10
    try:
        repository_analyzer=RepositoryAnalyzer(str(repository_path))
        repository_result=repository_analyzer.analyze()
        analyzer=CriticalityAnalyzer()
        result=analyzer.analyze(repository_result.graph,limit)
    except Exception as error:
        print(f"Criticality analysis failed: {error}")
        sys.exit(1)
    print()
    print("BlastScope")
    print("Critical Component Analysis")
    print()
    print(f"Repository: {repository_path}")
    print(f"Components ranked: {result.total_components}")
    print()
    if not result.components:
        print("No critical components detected")
        return
    for index,component in enumerate(result.components,1):
        print("="*70)
        print()
        print(f"#{index} {component.name}")
        print(f"Type: {component.node_type}")
        print(f"Criticality Score: {component.criticality_score}/100")
        print(f"File: {component.file_path}")
        print()
        print(f"Direct dependents: {component.direct_dependents}")
        print(f"Direct dependencies: {component.direct_dependencies}")
        print(f"Transitive dependents: {component.transitive_dependents}")
        print(f"API endpoints: {component.api_endpoints}")
        print(f"Maximum dependency depth: {component.dependency_depth}")
        print()
        print("Reasons:")
        for reason in component.reasons:
            print(f"- {reason}")
        print()
if __name__=="__main__":
    main()