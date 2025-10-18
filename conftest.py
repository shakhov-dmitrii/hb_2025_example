from typing import Any

import pytest
import allure


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item: Any):
    print(f"========= Перед выполнением теста {item.name}")
    yield
    print(f"========= После выполнения теста {item.name}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: Any) -> None:
    _ = yield
    if hasattr(item, "_obj"):
        docstring = item._obj.__doc__
        if docstring:
            docstring = str(docstring).strip().replace("\n", "&#10;")
            description = (
                f'<div style="white-space: pre-line; padding: 10px;">{docstring}</div>'
            )
            allure.dynamic.description_html(description)
