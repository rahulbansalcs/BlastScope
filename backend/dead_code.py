import sys
from pathlib import Path
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.analyzers.dead_code_analyzer import DeadCodeAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python dead_code.py <repository_path>")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    try:
        repository_analyzer=RepositoryAnalyzer(str(repository_path))
        repository_result=repository_analyzer.analyze()
        analyzer=DeadCodeAnalyzer()
        result=analyzer.analyze(repository_result.graph)
    except Exception as error:
        print(f"Dead-code analysis failed: {error}")
        sys.exit(1)
    print()
    print("BlastScope")
    print("Dead Code & Orphan Analysis")
    print()
    print(f"Repository: {repository_path}")
    print(f"Potential candidates: {result.total_candidates}")
    print()
    if not result.candidates:
        print("No potential dead code detected")
        return
    for candidate in result.candidates:
        print("="*70)
        print()
        print(f"{candidate.confidence} CONFIDENCE")
        print(f"Type: {candidate.node_type}")
        print(f"Symbol: {candidate.name}")
        print(f"File: {candidate.file_path}")
        print(f"Incoming dependencies: {candidate.incoming_dependencies}")
        print(f"Outgoing dependencies: {candidate.outgoing_dependencies}")
        print()
        print("Reasons:")
        for reason in candidate.reasons:
            print(f"- {reason}")
        print()
if __name__=="__main__":
    main()