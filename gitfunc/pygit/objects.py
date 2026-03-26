from __future__ import annotations
import hashlib
import zlib
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from .constants import OBJECTS_DIR, GIT_OBJECT_TREE_HASH_OFFSET


class GitObject(ABC):
    """
    Абстрактный класс для объектов гита
    """
    @abstractmethod
    def serialize(self) -> bytes:
        """
        Преобразовывает объект в байты

        :return bytes: байтовое представление объекта
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def deserialize(cls, data: bytes) -> GitObject:
        """
        Собирает объект из байтов

        :param data: байты
        :return GitObject: экземляр GitObject
        """
        raise NotImplementedError


@dataclass
class Blob(GitObject):
    data: bytes

    def serialize(self) -> bytes:
        """
        Возвращает то же, ибо блоб без мета

        :return bytes: содержимое блоба в байтах
        """
        return self.data

    @classmethod
    def deserialize(cls, data: bytes) -> Blob:
        """
        Делает блоб из байтов

        :param data: содержимое файла в байтах
        :return Blob: объект Blob
        """
        return cls(data)


@dataclass
class TreeNode:
    """
    То, что лежит внутри директории

    :mode: права
    :path: путь
    :sha: хеш
    """
    mode: str
    path: str
    sha: bytes


@dataclass
class Tree(GitObject):
    """
    Директория
    """
    nodes: list[TreeNode] = field(default_factory=list)

    def serialize(self) -> bytes:
        """
        Собирает директорию в бинарный формат

        :return bytes: бинарный формат объекта tree
        """
        return b''.join(
            f"{n.mode} {n.path}".encode('utf-8') + b'\x00' + n.sha
            for n in self.nodes
        )

    @classmethod
    def deserialize(cls, data: bytes) -> Tree:
        """
        Делает список (права, путь, хэш) из бинарной формы

        :data bytes: байты содержимого объекта tree
        :return Tree: объект Tree
        """
        tree = cls()
        i = 0
        while i < len(data):
            mode_index = data.find(b' ', i)
            if mode_index == -1:
                break
            mode = data[i:mode_index].decode('ascii')

            null_index = data.find(b'\x00', mode_index)
            if null_index == -1:
                break
            path = data[mode_index + 1:null_index].decode('utf-8')

            sha = data[null_index + 1:null_index + GIT_OBJECT_TREE_HASH_OFFSET]
            tree.nodes.append(TreeNode(mode, path, sha))
            i = null_index + GIT_OBJECT_TREE_HASH_OFFSET

        return tree


@dataclass
class CommitPerson:
    """
    Автор комита

    :name: имя
    :email: почта
    :time: unix временная метка
    :tx: время типа +0000
    """
    name: str
    email: str
    time: int
    tz: str


@dataclass
class Commit(GitObject):
    """
    Объект-комит

    :tree_sha: хеш корневой директории
    :parent_shas: список родителей
    :author: автор комита
    :committer: кто применил комит
    :message: сообщение
    """
    tree_sha: str = ""
    parent_shas: list[str] = field(default_factory=list)
    author: CommitPerson = field(
        default_factory=lambda: CommitPerson("", "", 0, "")
    )
    committer: CommitPerson = field(
        default_factory=lambda: CommitPerson("", "", 0, "")
    )
    message: str = ""

    @staticmethod
    def _format_tz_offset(offset_hours: int) -> str:
        """
        Смещение часового пояса
        (из 1 в +0100)

        :param offset_hours: смещение относительно utc
        :return str: строка +xxyy или -xxyy (xx-часы, yy-минуты)
        """
        sign = '+' if offset_hours >= 0 else '-'
        offset_hours = abs(offset_hours)
        return f"{sign}{offset_hours:02d}00"

    def serialize(self) -> bytes:
        """
        Собирает комит в текст

        :return bytes: байтовое представление комита
        """
        lines = [
            f"tree {self.tree_sha}"
        ] + [
            f"parent {parent}" for parent in self.parent_shas
        ] + [
            f"author {self.author.name} <{self.author.email}> "
            f"{self.author.time} {self.author.tz}",
            f"committer {self.committer.name} <{self.committer.email}> "
            f"{self.committer.time} {self.committer.tz}",
            "",
            self.message.rstrip('\n'),
        ]

        content = "\n".join(lines) + "\n"
        return content.encode('utf-8')

    @classmethod
    def deserialize(cls, data: bytes) -> Commit:
        """
        Из байтов собирает комит

        :data bytes: байтовое представление комита
        :return Commit: объект Commit с полями
        """
        text = data.decode('utf-8')
        lines = text.split('\n')

        try:
            blank_index = lines.index('')
        except ValueError:
            blank_index = len(lines)
            message = ''
        else:
            message = '\n'.join(lines[blank_index + 1:])

        tree_sha = ""
        parent_shas = []
        author_line = ""
        committer_line = ""

        for line in lines[:blank_index]:
            if line.startswith('tree '):
                tree_sha = line[5:]
            elif line.startswith('parent '):
                parent_shas.append(line[7:])
            elif line.startswith('author '):
                author_line = line[7:]
            elif line.startswith('committer '):
                committer_line = line[10:]

        def parse(s: str) -> CommitPerson:
            """
            Парсим строку с автором комита

            :param s: инфа о создателе комита
            :return CommitPerson: объект CommitPerson
            """
            parts = s.rsplit(' ', 2)
            name_email = parts[0]
            timestamp = int(parts[1])
            tz = parts[2]

            less = name_email.rfind('<')
            greater = name_email.rfind('>')
            if less != -1 and greater != -1 and less < greater:
                name = name_email[:less].rstrip()
                email = name_email[less + 1:greater]
            else:
                name = name_email
                email = ""

            return CommitPerson(name=name, email=email, time=timestamp, tz=tz)

        author = (
            parse(author_line)
            if author_line
            else CommitPerson("", "", 0, "")
        )
        committer = (
            parse(committer_line)
            if committer_line
            else CommitPerson("", "", 0, "")
        )

        return cls(
            tree_sha=tree_sha,
            parent_shas=parent_shas,
            author=author,
            committer=committer,
            message=message
        )


# Здесь добавила параметр obj_dir, потому что в функцию лучше
# передать директорию извне, чем городить импорты констант
def hash_object(
        data: bytes, obj_type: str, objects_dir: Path | None = None
) -> str:
    """
    Создание объекта гита

    :param data: результат serialize
    :param obj_type: тип объекта
    :param objects_dir: директория с объектами, None - .pygit/objects
    :return: строка sha-1
    """
    if objects_dir is None:
        objects_dir = OBJECTS_DIR

    header = f"{obj_type} {len(data)}\x00".encode("ascii")
    final_data = header + data

    sha = hashlib.sha1(final_data).hexdigest()
    compressed = zlib.compress(final_data)

    obj_dir = objects_dir / sha[:2]
    obj_file = obj_dir / sha[2:]

    obj_dir.mkdir(parents=True, exist_ok=True)
    with open(obj_file, "wb") as f:
        f.write(compressed)

    return sha


def read_object(sha: str, objects_dir: Path) -> tuple[str, bytes]:
    """
    Считывание объекта из /objects по sha

    :param sha: sha-1
    :param objects_dir: директория, None - .pygit/objects
    :return: кортеж (тип объекта, его содержимое в байтах)
    """
    obj_dir = objects_dir / sha[:2]
    obj_file = obj_dir / sha[2:]

    with obj_file.open("rb") as f:
        compressed = f.read()

    data = zlib.decompress(compressed)
    nul_index = data.index(b"\0")
    header = data[:nul_index].decode("utf-8")
    obj_type, _ = header.split(" ", 1)
    body = data[nul_index + 1:]
    return obj_type, body


class CommitHistoryIterator:
    """
    Итератор по истории комитов
    """
    def __init__(self, start_sha: str, objects_dir: Path) -> None:
        """
        Создает итератор начиная с определенного sha
        :param start_sha: sha-1 последнего комита
        :param objects_dir: директория objects, None - .pygit/objects
        """
        self._current_sha = start_sha
        self._objects_dir = objects_dir

    def __iter__(self) -> "CommitHistoryIterator":
        """
        Возвращает итератор
        """
        return self

    def __next__(self) -> tuple[str, Commit]:
        """
        Возвращает комит в истории

        :return: кортеж (его sha, объект комита)
        """
        if not self._current_sha:
            raise StopIteration

        sha = self._current_sha
        obj_type, body = read_object(sha, self._objects_dir)
        if obj_type != "commit":
            raise ValueError(f"{sha} not a commit, type is {obj_type}")

        commit = Commit.deserialize(body)
        self._current_sha = commit.parent_shas[0] if commit.parent_shas else ""
        return sha, commit
