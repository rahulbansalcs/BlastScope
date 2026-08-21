import sys
from pathlib import Path
from app.tests.test_mapper import TestMapper
def main():
    if len(sys.argv)<3:
        print("Usage: python test_impact.py <repository_path> <symbol>")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    symbol=sys.argv[2]
    mapper=TestMapper()
    tests=mapper.find_tests_for_symbol(str(repository_path),symbol)
    print()
    print("BlastScope")
    print("Test Impact Analysis")
    print()
    print(f"Changed symbol: {symbol}")
    print(f"Recommended tests: {len(tests)}")
    print()
    if not tests:
        print("No related tests detected")
        return
    for test in tests:
        print(f"- {test.qualified_name}")
        print(f"  File: {test.file_path}")
        print(f"  Line: {test.line}")
if __name__=="__main__":
    main()