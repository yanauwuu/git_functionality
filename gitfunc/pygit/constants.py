from pathlib import Path

REPO_DIR: Path = Path(".pygit")
OBJECTS_DIR: Path = REPO_DIR / "objects"
REFS_HEADS_DIR: Path = REPO_DIR / "refs" / "heads"
HEAD_FILE: Path = REPO_DIR / "HEAD"
INDEX_FILE: Path = REPO_DIR / "index"
INITIAL_HEAD_CONTENT: str = "ref: refs/heads/main"
DEFAULT_FILE_MODE: str = "100644"

GIT_OBJECT_TREE_HASH_OFFSET: int = 20
