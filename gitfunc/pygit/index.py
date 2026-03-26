from pathlib import Path
from .objects import TreeNode
from typing import Iterator, Any
from .constants import INDEX_FILE


def read_index(index_path: Path | None = None) -> list[TreeNode]:
    """
    Читает index и возвращает содержимое списком

    :param index_path: путь к файлу, при None - '.pygit/index'
    :return: список [права, имя, хеш] файла в индексе
    """
    if index_path is None:
        index_path = INDEX_FILE

    if not index_path.exists():
        return []

    def iter_index() -> Iterator[TreeNode]:
        with open(index_path, "r") as f:
            for line in f.readlines():
                mode, path, sha_hex = line.split()
                sha = bytes.fromhex(sha_hex)
                yield TreeNode(mode, path, sha)

    return [*iter_index()]


def write_index(
        index_path: Path | Any, new_node: TreeNode | None = None
) -> None:
    """
    Обновляет файл в index

    :index_path: путь файла
    :param new_node: новый узел для добавления, при None - None (пустой файл)
    :return: None
    """
    if isinstance(index_path, (list, dict)) and new_node is None:
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        INDEX_FILE.touch()
        return

    if index_path is None:
        index_path = INDEX_FILE

    if new_node is None:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.touch()
        return

    index = read_index(index_path)
    index.append(new_node)

    index_dict: dict[str, TreeNode] = {}
    for node in index:
        index_dict[node.path] = node
    index = list(index_dict.values())

    with open(index_path, "w", encoding="utf-8") as f:
        for node in index:
            f.write(f"{node.mode} {node.path} {node.sha.hex()}\n")


def clear_index(index_path: Path) -> None:
    """
    Очищает index

    :param index_path: путь к файлу, при None - '.pygit/index'
    :return: None
    """
    index_path.write_text("")
