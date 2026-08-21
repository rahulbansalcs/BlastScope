import sys
from pathlib import Path
from dataclasses import asdict
import json
from app.services.analysis_service import AnalysisService
def main():
    if len(sys.argv)<2:
        print("Usage: python full_analysis.py <repository_path> [base_ref] [target_ref]")
        sys.exit(1)
    repository_path=Path(sys.argv[1]).resolve()
    base_ref=sys.argv[2] if len(sys.argv)>2 else "main"
    target_ref=sys.argv[3] if len(sys.argv)>3 else "HEAD"
    try:
        service=AnalysisService(str(repository_path))
        result=service.run(base_ref,target_ref)
    except Exception as error:
        print(f"Analysis failed: {error}")
        sys.exit(1)
    print(json.dumps(asdict(result),indent=2))
if __name__=="__main__":
    main()