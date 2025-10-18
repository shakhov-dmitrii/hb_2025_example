from functools import reduce
from typing import Any, Callable, List, Optional, Tuple

import allure
import pytest
from pytest import MarkDecorator


# Класс для хранения и применения нескольких маркеров к функциям тестов
class CustomMarkDecorator:
    def __init__(self, marks: List[MarkDecorator]) -> None:
        self._marks = marks

    def __call__(self, func: Optional[Callable] = None) -> Any:
        # Проверяем, является ли переданный объект вызываемым (функцией)
        if callable(func):
            return _decorate_func_by_marks(func, self._marks)
        raise TypeError(
            "CustomMarkDecorator объект должен быть вызван с вызываемым объектом"
        )

    @property
    def marks(self) -> Tuple[MarkDecorator, ...]:
        # Возвращаем кортеж маркеров для доступа извне
        return tuple(self._marks)


# Функция для создания маркера ссылки на issue и добавления его в allure
def link(url: str) -> CustomMarkDecorator:
    marks = [_add_issue_mark(url), allure.link(url=url, name=url)]
    return CustomMarkDecorator(marks)


# Внутренняя функция для добавления маркера issue к pytest
def _add_issue_mark(issue: str) -> MarkDecorator:
    # Форматируем имя маркера для использования в pytest
    issue_formatted = issue.lower().replace("-", "_")
    # Добавляем новый маркер в pytest
    pytest.mark._markers.add(issue_formatted)
    # Возвращаем созданный маркер
    return getattr(pytest.mark, issue_formatted)


# Функция для последовательного применения нескольких маркеров к функции
def _decorate_func_by_marks(func: Callable, marks: List[MarkDecorator]) -> Callable:
    # Используем reduce для последовательного применения маркеров к функции
    return reduce(lambda x, y: y(x), marks, func)
