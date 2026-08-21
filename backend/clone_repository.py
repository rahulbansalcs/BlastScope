import sys
from app.workspace.repository_workspace import RepositoryWorkspace
def main():
    if len(sys.argv)<2:
        print("Usage: python clone_repository.py <repository_url> [branch]")
        sys.exit(1)
    repository_url=sys.argv[1]
    branch=sys.argv[2] if len(sys.argv)>2 else None
    print()
    print("BlastScope")
    print("Repository Workspace Test")
    print()
    try:
        with RepositoryWorkspace(repository_url,branch) as workspace:
            print("Repository cloned successfully")
            print()
            print(f"URL: {workspace.repository_url}")
            print(f"Branch: {workspace.branch}")
            print(f"Commit: {workspace.commit}")
            print(f"Temporary path: {workspace.local_path}")
            print()
            print("Repository will be deleted automatically after analysis")
    except Exception as error:
        print(f"Clone failed: {error}")
        sys.exit(1)
if __name__=="__main__":
    main()