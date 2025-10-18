from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import TypeVar, Union

import pytest
from _pytest.mark import Mark, MarkDecorator


T = TypeVar("T", bound=Union[type, "Epic"])


class Duty(str, Enum):
    qa_duty_1 = ("qa_duty_1", pytest.mark.qa_duty_1)

    def __new__(cls, name: str, mark: MarkDecorator) -> "Duty":
        obj = str.__new__(cls, name)
        obj._value_ = name
        obj.mark = mark
        return obj


class LabelType:
    EPIC = "epic"
    STORY = "story"
    FEATURE = "feature"

    ALL = [EPIC, STORY, FEATURE]


def epic(*args: str) -> MarkDecorator:
    return pytest.mark.allure_label(*args, label_type=LabelType.EPIC)


def story(*args: str) -> MarkDecorator:
    return pytest.mark.allure_label(*args, label_type=LabelType.STORY)


def service(*args: str) -> MarkDecorator:
    return pytest.mark.allure_label(*args, label_type="service")


class Epic:
    name = ""
    duty = ""
    base_duty = pytest.mark.base_qa_duty

    class story:  # noqa: N801
        """Story class."""

    @classmethod
    @lru_cache(maxsize=None)
    def get_duty(cls: T, label_name: str) -> Mark:
        for subclass in cls.__subclasses__():
            return subclass.duty

    @classmethod
    @lru_cache(maxsize=None)
    def get_epic_name(cls: T, mark_name: str) -> str:
        for child in cls.__subclasses__():
            if mark_name in child.stories():
                return child.name.args[0]
        return ""

    @classmethod
    @lru_cache
    def stories(cls: T) -> list:
        story_names = [
            getattr(cls.story, story_name).args
            for story_name in dir(cls.story)
            if story_name.isupper()
        ]
        story_names = sum(story_names, ())  # unpacking [[1,2], [3,4]]->[1,2,3,4]
        return story_names

    @classmethod
    def marks(cls: T) -> tuple:
        story_names = cls.stories()
        return *cls.name.args, *story_names

    def __contains__(self, mark: str) -> bool:
        return mark in self.marks()

    @classmethod
    def get_epic(cls: T, epic_name: str) -> T:
        for child in cls.__subclasses__():
            if epic_name in [*child.name.args]:
                return child()
        return False


class SuperEpic(Epic):
    name = epic("Super Epic")
    duty = Duty.qa_duty_1.mark

    class story:
        EpicStory = story('Моя супер "история"')
