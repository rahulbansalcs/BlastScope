import sys
from pathlib import Path
from app.git.history_analyzer import GitHistoryAnalyzer
def main():
    if len(sys.argv)<3:
        print("Usage: python history.py <repository_path> <file_path>")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    file_path=sys.argv[2]
    try:
        analyzer=GitHistoryAnalyzer(str(repository_path))
        result=analyzer.analyze_file(file_path)
    except Exception as error:
        print(f"History analysis failed: {error}")
        sys.exit(1)
    print()
    print("BlastScope")
    print("Git Historical Risk Analysis")
    print()
    print(f"File: {result.file_path}")
    print()
    print(f"Commits: {result.commit_count}")
    print(f"Contributors: {result.contributors}")
    print(f"Bug-fix commits: {result.bugfix_commits}")
    print(f"Reverts: {result.revert_commits}")
    print()
    print(f"Historical Instability Score: {result.instability_score}/100")
    print()
    print("RECENT COMMITS")
    print()
    if not result.recent_commits:
        print("No history found")
    else:
        for commit in result.recent_commits:
            print(f"- {commit}")
if __name__=="__main__":
    main()