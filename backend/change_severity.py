import sys
from pathlib import Path
from app.git.change_severity_analyzer import ChangeSeverityAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python change_severity.py <repository_path> [base_ref] [target_ref]")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    base_ref=sys.argv[2] if len(sys.argv)>2 else "main"
    target_ref=sys.argv[3] if len(sys.argv)>3 else "HEAD"
    try:
        analyzer=ChangeSeverityAnalyzer(str(repository_path))
        result=analyzer.analyze(base_ref,target_ref)
    except Exception as error:
        print(f"Change severity analysis failed: {error}")
        sys.exit(1)
    print()
    print("BlastScope")
    print("Change Size & Diff Severity")
    print()
    print(f"Base: {base_ref}")
    print(f"Target: {target_ref}")
    print(f"Changed files: {len(result.files)}")
    print()
    if not result.files:
        print("No changed files detected")
        return
    for item in result.files:
        print("="*70)
        print()
        print(item.file_path)
        print(f"Added lines: {item.additions}")
        print(f"Deleted lines: {item.deletions}")
        print(f"Total changed lines: {item.total_changed_lines}")
        print(f"File change ratio: {item.change_ratio}%")
        print(f"Severity: {item.severity_score}/100 {item.severity_level}")
        print()
        print("Reasons:")
        for reason in item.reasons:
            print(f"- {reason}")
        print()
if __name__=="__main__":
    main()