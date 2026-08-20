import sys
from pathlib import Path
from app.git.diff_analyzer import GitDiffAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python git_diff.py <repository_path> [base_ref] [target_ref]")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    base_ref=sys.argv[2] if len(sys.argv)>2 else "main"
    target_ref=sys.argv[3] if len(sys.argv)>3 else "HEAD"
    try:
        analyzer=GitDiffAnalyzer(str(repository_path))
        result=analyzer.analyze(base_ref,target_ref)
    except Exception as error:
        print(f"Git analysis failed: {error}")
        sys.exit(1)
    print()
    print("BlastScope")
    print("Git Change Analysis")
    print()
    print(f"Repository: {repository_path}")
    print(f"Current branch: {analyzer.get_current_branch()}")
    print(f"Base: {result.base_ref}")
    print(f"Target: {result.target_ref}")
    print()
    print(f"Changed files: {len(result.changed_files)}")
    print()
    if not result.changed_files:
        print("No changes detected")
        return
    for changed_file in result.changed_files:
        print(f"{changed_file.change_type.upper()}: {changed_file.path}")
        if changed_file.old_path:
            print(f"Previous path: {changed_file.old_path}")
        if changed_file.changed_lines:
            print("Changed lines:")
            for line_range in changed_file.changed_lines:
                print(f"  {line_range.start}-{line_range.end}")
        print()
if __name__=="__main__":
    main()