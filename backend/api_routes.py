import sys
from pathlib import Path
from app.analyzers.api_route_analyzer import ApiRouteAnalyzer
def main():
    if len(sys.argv)<2:
        print("Usage: python api_routes.py <repository_path>")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    analyzer=ApiRouteAnalyzer()
    result=analyzer.analyze_repository(str(repository_path))
    print()
    print("BlastScope")
    print("API Route Analysis")
    print()
    print(f"Repository: {repository_path}")
    print(f"Routes found: {len(result.routes)}")
    print()
    for route in result.routes:
        print(f"{route.method} {route.path}")
        print(f"Framework: {route.framework}")
        print(f"Handler: {route.qualified_handler}")
        print(f"File: {route.file_path}")
        print(f"Line: {route.line}")
        print()
if __name__=="__main__":
    main()