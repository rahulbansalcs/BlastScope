import sys
from pathlib import Path
from app.analyzers.repository_analyzer import RepositoryAnalyzer
from app.git.diff_analyzer import GitDiffAnalyzer
from app.git.change_mapper import ChangeMapper
def main():
    if len(sys.argv)<2:
        print("Usage: python changed_symbols.py <repository_path> [base_ref] [target_ref]")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    base_ref=sys.argv[2] if len(sys.argv)>2 else "main"
    target_ref=sys.argv[3] if len(sys.argv)>3 else "HEAD"
    print()
    print("BlastScope")
    print("Git Symbol Change Detection")
    print()
    try:
        repository_analyzer=RepositoryAnalyzer(str(repository_path))
        repository_result=repository_analyzer.analyze()
        git_analyzer=GitDiffAnalyzer(str(repository_path))
        diff_result=git_analyzer.analyze(base_ref,target_ref)
        mapper=ChangeMapper(str(repository_path))
        mapping=mapper.map_changes(diff_result,repository_result.parsed_files)
    except Exception as error:
        print(f"Analysis failed: {error}")
        sys.exit(1)
    print(f"Base: {base_ref}")
    print(f"Target: {target_ref}")
    print()
    print(f"Changed files: {len(diff_result.changed_files)}")
    print(f"Changed symbols: {len(mapping.changed_symbols)}")
    print()
    if mapping.changed_symbols:
        print("CHANGED SYMBOLS")
        print()
        for symbol in mapping.changed_symbols:
            print(f"{symbol.symbol_type.upper()}: {symbol.qualified_name}")
            print(f"Lines: {symbol.line_start}-{symbol.line_end}")
            print(f"Change: {symbol.change_type}")
            print()
    if mapping.unmapped_files:
        print("UNMAPPED FILES")
        print()
        for file_path in mapping.unmapped_files:
            print(file_path)
if __name__=="__main__":
    main()