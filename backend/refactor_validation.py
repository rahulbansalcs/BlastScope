import sys
from pathlib import Path
from app.analyzers.refactor_validation_analyzer import RefactorValidationAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python refactor_validation.py <repository_path> [base_ref] [target_ref]")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    base_ref=sys.argv[2] if len(sys.argv)>2 else "main"
    target_ref=sys.argv[3] if len(sys.argv)>3 else "HEAD"
    print()
    print("BlastScope")
    print("Refactor Caller Validation")
    print()
    try:
        analyzer=RefactorValidationAnalyzer(str(repository_path))
        results=analyzer.analyze(base_ref,target_ref)
    except Exception as error:
        print(f"Analysis failed: {error}")
        sys.exit(1)
    if not results:
        print("No deleted or renamed symbols detected")
        return
    for result in results:
        print("="*70)
        print()
        print(f"Change: {result.change_type.upper()}")
        print(f"Old symbol: {result.old_symbol}")
        if result.new_symbol:
            print(f"New symbol: {result.new_symbol}")
        print()
        print(f"Old callers: {result.total_old_callers}")
        print(f"Updated callers: {result.updated_callers}")
        print(f"Broken callers: {result.broken_callers}")
        print()
        if result.safe_refactor:
            print("Result: SAFE REFACTOR")
        else:
            print("Result: BREAKING CHANGE")
        print()
        for caller in result.callers:
            print(f"{caller.status}: {caller.caller_name}")
            print(f"File: {caller.caller_file}")
            print(f"Old reference: {caller.old_reference}")
            if caller.new_reference:
                print(f"Expected new reference: {caller.new_reference}")
            print()
if __name__=="__main__":
    main()