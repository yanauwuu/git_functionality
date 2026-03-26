from collections import defaultdict
import os
import sys
from datetime import datetime
import time
from typing import Dict, List, Iterator

from pygit.utils.command_decorator import (  # type: ignore[import-not-found]
    Commands,
)

from pygit.objects import (  # type: ignore[import-not-found]
    hash_object,
    TreeNode,
    Tree,
    Commit,
    CommitPerson,
    CommitHistoryIterator,
)

from pygit.index import (  # type: ignore[import-not-found]
    read_index,
    write_index,
    clear_index,
)

from pygit.constants import (  # type: ignore[import-not-found]
    REPO_DIR,
    OBJECTS_DIR,
    REFS_HEADS_DIR,
    HEAD_FILE,
    INDEX_FILE,
    INITIAL_HEAD_CONTENT,
    DEFAULT_FILE_MODE,
)


command = Commands()


def ensure_repo() -> None:
    """
    Проверка, есть ли в директории pygit репо
    """
    if not REPO_DIR.exists():
        raise RuntimeError('.pygit dont exist, write "pygit init"')


def read_head_branch() -> str:
    """
    Чтение имени текущей ведки
    """
    if not HEAD_FILE.exists():
        raise RuntimeError("HEAD don't exist")

    content: str = HEAD_FILE.read_text(encoding="utf-8").strip()
    prefix = "ref: refs/heads/"
    if content.startswith(prefix):
        branch: str = content[len(prefix):]
        return branch

    raise RuntimeError("HEAD's wrong format")


@command("init")  # type: ignore[misc]
def init() -> None:
    """
    Инициализация нового репо
    """
    if os.path.exists(f"./{REPO_DIR}"):
        return

    os.makedirs(f"./{OBJECTS_DIR}")
    os.makedirs(f"./{REFS_HEADS_DIR}")
    with open(f"./{HEAD_FILE}", "w") as f:
        f.write(INITIAL_HEAD_CONTENT)

    INDEX_FILE.touch()


@command("add")  # type: ignore[misc]
def add(filename: str) -> None:
    """
    Добавляет файл в индекс

    :param filename: путь к файлу
    """
    with open(filename, "rb") as f:
        contents = f.read()

    blob = hash_object(contents, "blob", OBJECTS_DIR)
    write_index(
        INDEX_FILE,
        TreeNode(DEFAULT_FILE_MODE, filename, bytes.fromhex(blob)),
    )


@command("write-tree")  # type: ignore[misc]
def write_tree() -> str:
    """
    Строит дерево на основе индекса (рекурсивно)
    """
    index = read_index(INDEX_FILE)

    dir_entries: Dict[str, List[TreeNode]] = defaultdict(list)
    all_dirs: set[str] = set()

    for node in index:
        dirname = os.path.dirname(node.path)
        dir_entries[dirname].append(node)
        parts = dirname.split('/')
        for i in range(1, len(parts) + 1):
            all_dirs.add('/'.join(parts[:i]))

    if '' not in all_dirs:
        all_dirs.add('')

    tree_cache: dict[str, str] = {}

    def generate_dir_trees(
        dir_path: str,
    ) -> Iterator[tuple[str, list[TreeNode]]]:
        """
        Обходит директории (начало c dir_path) рекурсивно

        :param dir_path: путь
        :return: (путь директории, список TreeNode)
        """
        subdirs = []
        for candidate in all_dirs:
            # не считаем текущую директорию своей под директорией
            if candidate == dir_path:
                continue
            if os.path.dirname(candidate) == dir_path:
                subdirs.append(candidate)

        for subdir in subdirs:
            yield from generate_dir_trees(subdir)

        entries = []
        for node in dir_entries[dir_path]:
            basename = os.path.basename(node.path)
            entries.append(TreeNode(node.mode, basename, node.sha))

        for subdir in subdirs:
            basename = os.path.basename(subdir)
            if subdir in tree_cache:
                entries.append(
                    TreeNode("040000",
                             basename,
                             bytes.fromhex(tree_cache[subdir]))
                )

        entries.sort(key=lambda x: x.path)

        yield (dir_path, entries)

    for dir_path, entries in generate_dir_trees(""):
        tree = Tree(entries)
        serialized = tree.serialize()
        tree_sha = hash_object(serialized, "tree", OBJECTS_DIR)
        tree_cache[dir_path] = tree_sha

    print(tree_cache.get('', ''))
    return tree_cache.get('', '')


@command("commit")  # type: ignore[misc]
def commit(
    message: str | list[str] | None = None, *, m: str | None = None
) -> None:
    """
    Создание комита
    :param message: сообщение комита
    :param m: флаг -m
    :return: None
    """
    if m is not None:
        msg = m
    elif isinstance(message, list):
        msg = message[0] if message else ""
    elif isinstance(message, str):
        msg = message
    else:
        msg = ""

    tree_sha = write_tree()

    branch = read_head_branch()

    branch_ref = REFS_HEADS_DIR / branch
    if os.path.exists(branch_ref):
        with open(branch_ref, "r", encoding="utf-8") as f:
            parent_shas = [f.read().strip()]
    else:
        parent_shas = []

    author_name = os.getenv("GIT_AUTHOR_NAME", "default")
    author_email = os.getenv("GIT_AUTHOR_EMAIL", "default@yandex.ru")
    committer_name = os.getenv("GIT_COMMITTER_NAME", author_name)
    committer_email = os.getenv("GIT_COMMITTER_EMAIL", author_email)

    now = int(time.time())

    offset = datetime.now().astimezone().utcoffset()
    if offset is None:
        tz_offset = Commit._format_tz_offset(0)
    else:
        offset_hours = int(offset.total_seconds() // 3600)
        tz_offset = Commit._format_tz_offset(offset_hours)

    commit = Commit(
        tree_sha=tree_sha,
        parent_shas=parent_shas,
        author=CommitPerson(
            name=author_name,
            email=author_email,
            time=now,
            tz=tz_offset,
        ),
        committer=CommitPerson(
            name=committer_name,
            email=committer_email,
            time=now,
            tz=tz_offset,
        ),
        message=msg,
    )

    commit_sha = hash_object(commit.serialize(), "commit", OBJECTS_DIR)

    with open(branch_ref, "w", encoding="utf-8") as f:
        f.write(commit_sha)

    clear_index(INDEX_FILE)


@command("log")  # type: ignore[misc]
def log() -> None:
    """
    Выводит историю комитов ветки
    """
    ensure_repo()

    branch = read_head_branch()
    branch_ref = REFS_HEADS_DIR / branch

    if not branch_ref.exists():
        print("No commits")
        return

    start_sha = branch_ref.read_text(encoding="utf-8").strip()
    if not start_sha:
        print("No commits")
        return

    for sha, commit in CommitHistoryIterator(start_sha, OBJECTS_DIR):
        print(f"commit {sha}")
        print(f"Author: {commit.author.name} <{commit.author.email}>")
        print()
        for line in commit.message.splitlines():
            print(f"  {line}")
        print()


def main() -> None:
    """
    Берем имя команды, оставшиеся аргументы в dispatch
    происходит вызов функции с пометкой-декоратором
    """
    _, cmd, *args = sys.argv
    command.dispatch(cmd, args)
