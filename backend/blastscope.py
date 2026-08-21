import sys
from pathlib import Path
from app.analyzers.change_impact_analyzer import ChangeImpactAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python blastscope.py <repository_path> [base_ref] [target_ref]")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    base_ref=sys.argv[2] if len(sys.argv)>2 else "main"
    target_ref=sys.argv[3] if len(sys.argv)>3 else "HEAD"
    print()
    print("BlastScope")
    print("Automated Change Impact Analysis")
    print()
    print(f"Repository: {repository_path}")
    print(f"Base: {base_ref}")
    print(f"Target: {target_ref}")
    print()
    try:
        analyzer=ChangeImpactAnalyzer(str(repository_path))
        report=analyzer.analyze(base_ref,target_ref)
    except Exception as error:
        print(f"Analysis failed: {error}")
        sys.exit(1)
    print("ANALYSIS COMPLETE")
    print()
    print("OVERALL RISK")
    print()
    print(f"Risk Score: {report.overall_risk_score}/100")
    print(f"Risk Level: {report.overall_risk_level}")
    print()
    print("CHANGE SUMMARY")
    print()
    print(f"Changed files: {len(report.changed_files)}")
    print(f"Changed symbols: {len(report.changed_symbols)}")
    print(f"Analyzed symbols: {len(report.symbol_impacts)}")
    print(f"Unmapped files: {len(report.unmapped_files)}")
    print()
    if report.changed_files:
        print("CHANGED FILES")
        print()
        for changed_file in report.changed_files:
            print(f"{changed_file.change_type.upper()}: {changed_file.path}")
        print()
    if report.symbol_impacts:
        print("SYMBOL IMPACT ANALYSIS")
        print()
        for result in report.symbol_impacts:
            symbol=result.changed_symbol
            impact=result.impact
            risk=result.risk
            print("="*70)
            print()
            print(f"{symbol.symbol_type.upper()}: {symbol.qualified_name}")
            print(f"Lines: {symbol.line_start}-{symbol.line_end}")
            print(f"Risk: {risk.score}/100 {risk.level}")
            print()
            print(f"Total affected: {impact.total_affected}")
            print(f"Dependency depth: {impact.maximum_depth}")
            print(f"Affected files: {len(impact.affected_files)}")
            print(f"Affected functions: {len(impact.affected_functions)}")
            print()
            print("Reasons:")
            for reason in risk.reasons:
                print(f"- {reason}")
            if impact.direct_impact:
                print()
                print("Direct impact:")
                for component in impact.direct_impact:
                    print(f"- {component.node_type}: {component.name}")
            if impact.indirect_impact:
                print()
                print("Indirect impact:")
                for component in impact.indirect_impact:
                    print(f"- depth {component.depth}: {component.name}")
            print()
    if report.unmapped_files:
        print("UNMAPPED FILES")
        print()
        for file_path in report.unmapped_files:
            print(f"- {file_path}")
        print()
if __name__=="__main__":
    main()