import allure
import pytest

from src.epics import Epic, LabelType


class PytestExitCode:
    INTERNAL_ERROR = None


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session: pytest.Session, items):
    items[:] = items.copy()

    for item in items:
        has_duty = False
        own_test_markers = [
            _mark
            for _mark in item.own_markers
            if _mark.kwargs.get("label_type") in LabelType.ALL
        ]
        markers = own_test_markers + item.parent.own_markers

        for marker in markers:
            for name in marker.args:
                if team_duty := Epic.get_duty(name):
                    item.add_marker(team_duty)
                    has_duty = True
                if epic_name := Epic.get_epic_name(name):
                    item.add_marker(allure.epic(epic_name))

        if not has_duty and Epic:
            item.add_marker(Epic.base_duty)
