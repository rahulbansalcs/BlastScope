import sys
from pathlib import Path
from app.analyzers.symbol_change_analyzer import SymbolChangeAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python symbol_changes.py <repository_path> [base_ref] [target_ref]")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    base_ref=sys.argv[2] if len(sys.argv)>2 else "main"
    target_ref=sys.argv[3] if len(sys.argv)>3 else "HEAD"
    try:
        analyzer=SymbolChangeAnalyzer(str(repository_path))
        result=analyzer.analyze(base_ref,target_ref)
    except Exception as error:
        print(f"Symbol change analysis failed: {error}")
        sys.exit(1)
    print()
    print("BlastScope")
    print("Deleted & Renamed Symbol Analysis")
    print()
    print(f"Base: {result.base_ref}")
    print(f"Target: {result.target_ref}")
    print(f"Symbol changes: {len(result.changes)}")
    print()
    if not result.changes:
        print("No added, deleted, or renamed symbols detected")
        return
    for change in result.changes:
        print("="*70)
        print()
        print(f"Change: {change.change_type.upper()}")
        print(f"Breaking: {change.breaking}")
        print(f"Confidence: {change.confidence}%")
        if change.old_symbol:
            print(f"Old symbol: {change.old_symbol.qualified_name}")
            print(f"Old file: {change.old_symbol.file_path}")
        if change.new_symbol:
            print(f"New symbol: {change.new_symbol.qualified_name}")
            print(f"New file: {change.new_symbol.file_path}")
        if change.reasons:
            print()
            print("Reasons:")
            for reason in change.reasons:
                print(f"- {reason}")
        print()
if __name__=="__main__":
    main()