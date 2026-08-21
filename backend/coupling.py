import sys
from pathlib import Path
from app.git.coupling_analyzer import CouplingAnalyzer
def main():
    if len(sys.argv)<3:
        print("Usage: python coupling.py <repository_path> <file_path>")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    file_path=sys.argv[2]
    try:
        analyzer=CouplingAnalyzer(str(repository_path))
        result=analyzer.analyze_file(file_path)
    except Exception as error:
        print(f"Coupling analysis failed: {error}")
        sys.exit(1)
    print()
    print("BlastScope")
    print("Evolutionary Coupling Analysis")
    print()
    print(f"Target file: {result.target_file}")
    print(f"Target commits analyzed: {result.total_target_commits}")
    print()
    if not result.coupled_files:
        print("No meaningful evolutionary coupling detected")
        return
    print("COUPLED FILES")
    print()
    for item in result.coupled_files:
        print(f"{item.file_path}")
        print(f"Shared commits: {item.shared_commits}")
        print(f"Coupling score: {item.coupling_score}%")
        print()
if __name__=="__main__":
    main()