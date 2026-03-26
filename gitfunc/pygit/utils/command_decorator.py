from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any, Dict, List, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class Commands:
    """
    Класс команд
    """
    _dispatchers: Dict[str, Callable[..., Any]] = field(default_factory=dict)

    def __call__(self, name: str) -> "CommandDecorator":
        """
        Возвращает декоратор для реги команд

        :param name: имя команды
        :return: объект CommandDecorator
        """
        return CommandDecorator(name, self)

    def dispatch(self, command: str, arguments: List[str]) -> None:
        """
        Находит команду через имя и вызызвает

        :param command: имя команды (ключ словаря)
        :param arguments: строковые аргументы
        :return: None
        """
        handler = self._dispatchers.get(command)
        if not handler:
            raise ValueError(f"Invalid command: {command}")

        kwargs: dict[str, str] = {}
        i = 0
        while i < len(arguments):
            if arguments[i].startswith("-"):
                if i + 1 >= len(arguments):
                    raise ValueError(f"{arguments[i]!r} needs a value")
                flag_name = arguments[i][1:]
                flag_value = arguments[i + 1]
                kwargs[flag_name] = flag_value
                del arguments[i:i + 2]
            else:
                i += 1

        handler(*arguments, **kwargs)


@dataclass
class CommandDecorator:
    """
    Декоратор, регистрирует функцию как команду
    """
    _name: str
    _commands: Commands

    def __call__(self, command: F) -> F:
        """
        Кладет функцию в словарь под _name

        :param command: функция-команда
        """
        self._commands._dispatchers[self._name] = command
        return command
