import sys
import json
from dataclasses import asdict
from app.services.remote_analysis_service import RemoteAnalysisService
def main():
    if len(sys.argv)<2:
        print("Usage: python remote_analysis.py <repository_url> [base_ref] [target_ref]")
        sys.exit(1)
    repository_url=sys.argv[1]
    base_ref=sys.argv[2] if len(sys.argv)>2 else "main"
    target_ref=sys.argv[3] if len(sys.argv)>3 else "HEAD"
    try:
        service=RemoteAnalysisService()
        result=service.analyze(
            repository_url,
            base_ref,
            target_ref
        )
    except Exception as error:
        print(f"Remote analysis failed: {error}")
        sys.exit(1)
    print(json.dumps(asdict(result),indent=2))
if __name__=="__main__":
    main()