import sys
from pathlib import Path
from app.analyzers.call_compatibility_analyzer import CallCompatibilityAnalyzer
from app.analyzers.signature_analyzer import SignatureAnalyzer
def main():
    if len(sys.argv)<4:
        print("Usage: python call_compatibility.py <repository_path> <file_path> <qualified_symbol>")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    file_path=Path(sys.argv[2]).resolve()
    qualified_symbol=sys.argv[3]
    module_name=qualified_symbol.rsplit(".",1)[0]
    target_name=qualified_symbol.rsplit(".",1)[1]
    signature_analyzer=SignatureAnalyzer()
    signatures=signature_analyzer.extract_from_file(str(file_path),module_name)
    signature=signatures.get(qualified_symbol)
    if not signature:
        print(f"Signature not found: {qualified_symbol}")
        sys.exit(1)
    analyzer=CallCompatibilityAnalyzer()
    calls=analyzer.find_calls(str(repository_path),target_name)
    results=analyzer.analyze(signature,calls)
    print()
    print("BlastScope")
    print("Call Compatibility Analysis")
    print()
    print(f"Target: {qualified_symbol}")
    print(f"Calls found: {len(results)}")
    print()
    incompatible=0
    for result in results:
        status="COMPATIBLE" if result.compatible else "INCOMPATIBLE"
        print(f"{status}: {result.caller}")
        print(f"File: {result.file_path}")
        print(f"Line: {result.line}")
        print(f"Expected required arguments: {result.expected_required}")
        print(f"Provided positional arguments: {result.provided_positional}")
        if result.reasons:
            for reason in result.reasons:
                print(f"- {reason}")
        print()
        if not result.compatible:
            incompatible+=1
    print(f"Potential runtime failures: {incompatible}")
if __name__=="__main__":
    main()