import sys
from pathlib import Path
from app.analyzers.removed_symbol_impact_analyzer import RemovedSymbolImpactAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python removed_symbol_impact.py <repository_path> [base_ref] [target_ref]")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    base_ref=sys.argv[2] if len(sys.argv)>2 else "main"
    target_ref=sys.argv[3] if len(sys.argv)>3 else "HEAD"
    print()
    print("BlastScope")
    print("Deleted & Renamed Symbol Impact Analysis")
    print()
    print(f"Base: {base_ref}")
    print(f"Target: {target_ref}")
    print()
    try:
        analyzer=RemovedSymbolImpactAnalyzer(str(repository_path))
        results=analyzer.analyze(base_ref,target_ref)
    except Exception as error:
        print(f"Analysis failed: {error}")
        sys.exit(1)
    if not results:
        print("No deleted or renamed breaking symbols detected")
        return
    print(f"Breaking symbol changes: {len(results)}")
    print()
    for result in results:
        print("="*70)
        print()
        print(f"Change: {result.change_type.upper()}")
        print(f"Severity: {result.severity}")
        print(f"Confidence: {result.confidence}%")
        print()
        print(f"Old symbol: {result.old_symbol.qualified_name}")
        print(f"Old file: {result.old_symbol.file_path}")
        if result.new_symbol:
            print(f"New symbol: {result.new_symbol.qualified_name}")
            print(f"New file: {result.new_symbol.file_path}")
        print()
        print(f"Total affected components: {result.total_affected}")
        print(f"Direct callers: {len(result.direct_callers)}")
        print(f"Transitive callers: {len(result.transitive_callers)}")
        print(f"Affected API endpoints: {len(result.affected_api_endpoints)}")
        print()
        print("WHY")
        print()
        for reason in result.reasons:
            print(f"- {reason}")
        if result.direct_callers:
            print()
            print("DIRECTLY BROKEN CALLERS")
            print()
            for caller in result.direct_callers:
                print(f"- {caller.node_type}: {caller.name}")
                print(f"  File: {caller.file_path}")
        if result.transitive_callers:
            print()
            print("TRANSITIVE IMPACT")
            print()
            for caller in result.transitive_callers:
                print(f"- Depth {caller.depth}: {caller.name}")
        if result.affected_api_endpoints:
            print()
            print("AFFECTED PUBLIC API ENDPOINTS")
            print()
            for endpoint in result.affected_api_endpoints:
                print(f"- {endpoint.name}")
        print()
if __name__=="__main__":
    main()