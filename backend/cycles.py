import sys
from pathlib import Path
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.analyzers.cycle_analyzer import CycleAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python cycles.py <repository_path>")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    try:
        repository_analyzer=RepositoryAnalyzer(str(repository_path))
        repository_result=repository_analyzer.analyze()
        analyzer=CycleAnalyzer()
        result=analyzer.analyze(repository_result.graph)
    except Exception as error:
        print(f"Cycle analysis failed: {error}")
        sys.exit(1)
    print()
    print("BlastScope")
    print("Dependency Cycle Analysis")
    print()
    print(f"Repository: {repository_path}")
    print(f"Cycles detected: {result.cycle_count}")
    print(f"Nodes involved in cycles: {len(result.affected_nodes)}")
    print()
    if not result.cycles:
        print("No dependency cycles detected")
        return
    for index,cycle in enumerate(result.cycles,1):
        print("="*70)
        print()
        print(f"Cycle #{index}")
        print(f"Cycle size: {cycle.size}")
        print()
        for node in cycle.nodes:
            print(f"- {node}")
        print()
        if cycle.edge_types:
            print(f"Edge types: {', '.join(cycle.edge_types)}")
        print()
if __name__=="__main__":
    main()