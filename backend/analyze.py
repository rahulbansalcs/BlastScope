import sys
from pathlib import Path
from app.analyzers.repository_analyzer import RepositoryAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python analyze.py <repository_path>")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    print()
    print("BlastScope")
    print("Dependency Blast Radius Analyzer")
    print()
    print(f"Repository: {repository_path}")
    print("Analyzing...")
    print()
    try:
        analyzer=RepositoryAnalyzer(str(repository_path))
        result=analyzer.analyze()
    except Exception as error:
        print(f"Analysis failed: {error}")
        sys.exit(1)
    print("Analysis complete")
    print()
    print(f"Files: {result.repository.file_count}")
    print(f"Python files: {result.repository.python_file_count}")
    print(f"Python lines: {result.repository.total_lines}")
    print(f"Symbols: {result.symbol_count}")
    print(f"Graph nodes: {result.graph_nodes}")
    print(f"Graph edges: {result.graph_edges}")
    print(f"Syntax errors: {result.syntax_error_count}")
    print()
    print("Discovered dependencies")
    print()
    edges=result.graph.get_edges()
    if not edges:
        print("No dependencies discovered")
        return
    for edge in edges:
        print(f"{edge.source} --[{edge.edge_type}]--> {edge.target}")
if __name__=="__main__":
    main()