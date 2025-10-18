from contextlib import contextmanager
from enum import Enum
from functools import cached_property, wraps
from typing import Any, Callable, Dict, Optional, Type, Union

import pytest
from allure_pytest.listener import AllureListener, AllureReporter
import allure
from allure_commons._allure import _TFunc
from allure_commons._core import plugin_manager
from allure_commons.model2 import Parameter, Status, TestResult
from allure_commons.types import ParameterMode
from allure_commons.utils import func_parameters, uuid4

attach_type = allure.attachment_type
TEXT = attach_type.TEXT
URI = attach_type.URI_LIST
JSON = attach_type.JSON
DUTY_PARAMETER_NAME = "duty"


class StepType(Enum):
    """Тип шага для автотестов."""

    DEFAULT = ""
    PRECONDITION = "Precondition steps: "


class StepContext:
    def __init__(
        self,
        title: str,
        params: Dict[str, Any],
        type_: StepType = StepType.DEFAULT,
        duty: Optional[str] = None,
    ) -> None:
        """Инициализация контекстного менеджера шага."""
        self.uuid = uuid4()
        self.title = title
        self.params = params
        self.type_ = type_
        self.duty = duty

    def __enter__(self) -> None:
        if self.duty:
            self.params.update({DUTY_PARAMETER_NAME: self.duty})
        plugin_manager.hook.start_step(
            uuid=self.uuid, title=self.step_title, params=self.step_params
        )

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Any, exc_tb: Any
    ) -> None:
        if (
            self.step_status(exc_type=exc_type) in (Status.FAILED, Status.BROKEN)
            and self.duty
        ):
            if not self.existing_duty_override:
                plugin_manager.hook.add_parameter(
                    name="duty_override",
                    value=self.duty,
                    excluded="false",
                    mode=ParameterMode.HIDDEN,
                )
        plugin_manager.hook.stop_step(
            uuid=self.uuid,
            title=self.step_title,
            exc_type=exc_type,
            exc_val=exc_val,
            exc_tb=exc_tb,
        )

    def __call__(self, func: _TFunc) -> _TFunc:
        """Для случая, когда степ используется как декоратор."""

        @wraps(func)
        def impl(*args: Any, **kwargs: Any) -> Any:
            __tracebackhide__ = True
            params = func_parameters(func, *args, **kwargs)
            formatted_title = (
                self.title.format(*args, **params)
                if self.title
                else func.__name__.replace("_", " ").capitalize()
            )
            with StepContext(
                title=formatted_title,
                params=params,
                type_=self.type_,
                duty=self.duty,
            ):
                response = func(*args, **kwargs)
                if response:
                    self.attach_response(response)
                return response

        return impl

    def attach_response(self, response: Any) -> None:
        """Прикрепляет ответ к шагу."""
        if isinstance(response, dict):
            attach_json(response, name="Response JSON")
        elif isinstance(response, str):
            attach_text(response, name="Response Text")
        else:
            attach(str(response), name="Response", attachment_type=TEXT)

    @property
    def step_title(self) -> str:
        """Добавляет префикс типа шага к его названию."""
        title = self.title
        if self.type_ is StepType.PRECONDITION:
            title = self.type_.value + self.title
        return title

    @property
    def step_params(self) -> Dict[str, Any]:
        """Скрывает параметры для соответствующего шага."""
        return self.params

    @staticmethod
    def step_status(exc_type: Optional[Type[BaseException]]) -> str:
        """Определяет статус шага на основе типа исключения."""
        if exc_type:
            status = exc_type.__name__
            if status in (AssertionError.__name__, pytest.fail.Exception.__name__):
                return Status.FAILED
            elif status == pytest.skip.Exception.__name__:
                return Status.SKIPPED
            return Status.BROKEN
        return Status.PASSED

    @cached_property
    def _get_allure_logger(self) -> Optional[AllureReporter]:
        """Получает текущий логгер Allure."""
        for plugin in plugin_manager.get_plugin_manager().get_plugins():
            if isinstance(plugin, AllureListener):
                return plugin.allure_logger
        return None

    @property
    def existing_duty_override(self) -> Optional[Parameter]:
        """Проверяет, была ли уже замена дежурного для теста."""
        last_item = (
            self._get_allure_logger.get_last_item(item_type=TestResult)
            if self._get_allure_logger
            else None
        )
        if last_item:
            return next(
                (
                    param
                    for param in last_item.parameters
                    if param.name == "duty_override"
                ),
                None,
            )
        return None


@contextmanager
def _empty_step() -> None:
    yield


def _base_step(
    title: Union[str, Callable],
    params: Optional[Dict[str, Any]] = None,
    type_: StepType = StepType.DEFAULT,
    context_manager_only: bool = False,
    duty: Optional[str] = None,
) -> Any:
    """Базовая функция для создания шага."""
    if params is None:
        params = {}
    if callable(title):
        if context_manager_only:
            raise NotImplementedError(
                "Нельзя использовать данный шаг как декоратор! Используйте как контекстный менеджер."
            )
        return StepContext(title="", params=params, type_=type_, duty=duty)(title)
    return StepContext(title=title, params=params, type_=type_, duty=duty)


def precondition_test_steps(
    title: Union[str, Callable] = "",
    params: Optional[Dict[str, Any]] = None,
    duty: Optional[str] = None,
) -> Any:
    """Создает предусловия для шага теста."""
    return _base_step(
        title=title,
        params=params,
        type_=StepType.PRECONDITION,
        duty=duty,
        context_manager_only=True,
    )


def step(
    title: Union[str, Callable] = "",
    params: Optional[Dict[str, Any]] = None,
    duty: Optional[str] = None,
    step_type: StepType = StepType.DEFAULT,
) -> Any:
    """Создает шаг теста."""
    return _base_step(title=title, params=params, type_=step_type, duty=duty)


def attach(
    message: str,
    name: str,
    attachment_type: attach_type,
    **kwargs: str,
) -> None:
    """Прикрепляет сообщение к отчету Allure."""
    try:
        allure.attach(
            body=message, name=name, attachment_type=attachment_type, **kwargs
        )
    except KeyError as e:
        print(f"Ошибка прикрепления файла: {e}")


def attach_uri(message: str, name: str) -> None:
    """Прикрепляет URI к отчету Allure."""
    attach(message=message, name=name, attachment_type=URI)


def attach_text(message: str, name: str, **kwargs: str) -> None:
    """Прикрепляет текстовое сообщение к отчету Allure."""
    attach(message=message, name=name, attachment_type=TEXT, **kwargs)


def attach_json(data: Dict[str, Any], name: str) -> None:
    """Прикрепляет JSON данные к отчету Allure."""
    attach(message=str(data), name=name, attachment_type=JSON)
