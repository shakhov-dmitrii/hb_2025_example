"""Скрипт для формирования докстроки к тестам."""

import sys
import ast
import re
import argparse
from pathlib import Path
from typing import List, Union, Optional

RED_COLOR = "\033[1;31m"
CONTEXT = ":short_summary:"
TAB = "    "
ANCHOR = f"\n{TAB}Шаги:\n{TAB}________"
Q3 = '"""'
STEP_TYPES = [
    "step",
    "precondition_test_steps",
    "skipped_step",
    "check_step",
    "soft_check_step",
    "teardown_test_steps",
    "check_1c_step",
]

SKIPPED_TESTS: List[tuple] = []
UNDESCRIPTED_STEPS: List[str] = []


def format_string(string: str, tab: str, array: Optional[List[str]] = None) -> str:
    """Форматирование строки с учетом длины."""
    if array is None:
        array = []

    if len(full_str := tab + string) > 120:
        str_line, remainder = re.search(r"(.{0,120}\s)(.+)", full_str).groups()
        array.append(f"{str_line}\n")
        format_string(remainder, tab, array)
    else:
        array.append(full_str)

    return "".join(array)


def get_obj_value(obj: Union[ast.Constant, ast.JoinedStr]) -> str:
    """Получение значения объекта."""
    result = ""

    match obj:
        case ast.Constant():
            result = obj.value

        case ast.JoinedStr():
            for value in obj.values:
                match value:
                    case ast.Constant():
                        result += value.value
                    case ast.FormattedValue():
                        result += ast.unparse(value)

    return result


def check_with_its_step(node_with: ast.With) -> Union[bool, str]:
    """Проверка типа шага в блоке with."""
    node_context = node_with.items[0].context_expr

    if isinstance(node_context, ast.Call):
        func = node_context.func
    elif isinstance(node_context, ast.Attribute):
        func = node_context
    else:
        return False

    if (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id == "report"
        and func.attr in STEP_TYPES
    ):
        return func.attr

    return False


def get_steps(
    ast_node: ast.AST, tab_count: int = 1, array: Optional[List[str]] = None
) -> str:
    """Сбор шагов теста."""
    if array is None:
        array = []

    for sub_node in ast_node.body:
        if isinstance(sub_node, ast.With):
            if step_type := check_with_its_step(sub_node):
                sub_node_context = sub_node.items[0].context_expr
                obj_value = ""

                if isinstance(sub_node_context, ast.Call):
                    if args := sub_node_context.args:
                        obj_value = get_obj_value(args[0])
                    elif keywords := sub_node_context.keywords:
                        for keyword in keywords:
                            if keyword.arg == "title":
                                obj_value = get_obj_value(keyword.value)
                                break

                    if step_type == "skipped_step" and obj_value != "":
                        obj_value = f"{obj_value} - (skipped)"

                if obj_value == "":
                    UNDESCRIPTED_STEPS.append(str(sub_node.lineno))
                else:
                    array.append(format_string(obj_value, TAB * tab_count))

                get_steps(sub_node, tab_count + 1, array)
            else:
                get_steps(sub_node, tab_count, array)

        elif isinstance(sub_node, ast.For):
            if any(
                isinstance(item, ast.With) and check_with_its_step(item)
                for item in sub_node.body
            ):
                array.append(format_string("Шаги обёрнутые в цикл:", TAB * tab_count))

            get_steps(sub_node, tab_count, array)

    return "\n".join(array) if array else f"{TAB}:steps:"


def process_file(file_path: Path) -> None:
    """Обработка файла с тестами."""
    SKIPPED_TESTS.clear()
    UNDESCRIPTED_STEPS.clear()

    try:
        file_data = file_path.read_text()
    except FileNotFoundError:
        print(f"{RED_COLOR}Файл {file_path} не найден.")
        sys.exit()
    except Exception as e:
        print(f"{RED_COLOR}Ошибка при чтении файла: {e}")
        sys.exit()

    try:
        ast_obj = ast.parse(source=file_data)
    except IndentationError:
        print(f"{RED_COLOR}Тест пустой, напишите что-нибудь в тело функции.")
        sys.exit()

    for node in ast_obj.body:
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node, clean=False)

            if docstring:
                continue
            else:
                start_point, empty_docstring = re.findall(
                    rf'({node.name}[^:]+:\n)(\s*"*\s*)', file_data
                )[0]
                new_docstring = f"{start_point}{TAB}{Q3}{CONTEXT}\n{ANCHOR}\n{get_steps(node)}\n{TAB}{Q3}\n{TAB}"
                file_data = file_data.replace(
                    start_point + empty_docstring, new_docstring
                )

    try:
        file_path.write_text(file_data)
    except Exception as e:
        print(f"{RED_COLOR}Ошибка при записи файла: {e}")
        sys.exit()


def main() -> None:
    """Основная функция скрипта."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rp", required=True, type=Path, help="Relative Path of file with tests."
    )
    file_path = parser.parse_args().rp

    for _ in range(2):
        process_file(file_path)

    if SKIPPED_TESTS:
        skipped_tests = "\n".join(
            [
                f"{i + 1}. {el[0]} - {file_path.name}:{el[1]}"
                for i, el in enumerate(SKIPPED_TESTS)
            ]
        )
        print(
            f"{RED_COLOR}Следующие тесты были пропущены, т.к. отсутствует якорь:\n"
            f"{skipped_tests}\n\n"
            f"Подробности в README.md:347\n\n"
        )

    if UNDESCRIPTED_STEPS:
        undescribed_steps = "\n".join(
            [
                f"{i + 1}. {file_path.name}:{line}"
                for i, line in enumerate(UNDESCRIPTED_STEPS)
            ]
        )
        print(
            f"{RED_COLOR}В следующих шагах пропущено описание:\n{undescribed_steps}\n"
        )


if __name__ == "__main__":
    main()
