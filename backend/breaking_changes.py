import sys
from pathlib import Path
from app.analyzers.breaking_change_analyzer import BreakingChangeAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python breaking_changes.py <repository_path> [base_ref] [target_ref]")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    base_ref=sys.argv[2] if len(sys.argv)>2 else "main"
    target_ref=sys.argv[3] if len(sys.argv)>3 else "HEAD"
    print()
    print("BlastScope")
    print("Breaking Change Analysis")
    print()
    try:
        analyzer=BreakingChangeAnalyzer(str(repository_path))
        results=analyzer.analyze(base_ref,target_ref)
    except Exception as error:
        print(f"Analysis failed: {error}")
        sys.exit(1)
    if not results:
        print("No breaking signature changes detected")
        return
    print(f"Breaking changes detected: {len(results)}")
    print()
    for result in results:
        print("="*70)
        print()
        print(f"Symbol: {result.symbol}")
        print(f"Change: {result.change_type}")
        print("Severity: BREAKING")
        print()
        print("Reasons:")
        for reason in result.reasons:
            print(f"- {reason}")
        print()
        print(f"Dependency callers: {result.affected_count}")
        for caller in result.affected_callers:
            print(f"- {caller}")
        print()
        print(f"Compatible callers: {len(result.compatible_callers)}")
        for caller in result.compatible_callers:
            print(f"- {caller.caller} at line {caller.line}")
        print()
        print(f"Incompatible callers: {len(result.incompatible_callers)}")
        for caller in result.incompatible_callers:
            print(f"- {caller.caller}")
            print(f"  File: {caller.file_path}")
            print(f"  Line: {caller.line}")
            print(f"  Provided arguments: {caller.provided_positional}")
            print(f"  Expected required arguments: {caller.expected_required}")
            for reason in caller.reasons:
                print(f"  Reason: {reason}")
        print()
        print(f"Potential runtime failures: {result.potential_runtime_failures}")
        print()
if __name__=="__main__":
    main()