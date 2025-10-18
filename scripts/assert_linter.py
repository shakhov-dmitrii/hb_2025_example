import ast
import sys
from pathlib import Path
from typing import List, Dict, Any


def find_asserts_in_function(node: ast.FunctionDef) -> dict:
    """
    Ищет assert в тестовой функции.

    Args:
        node: Узел AST с определением функции

    Returns:
        Словарь с информацией о функции и найденных assert
    """
    assert_count = 0
    assert_lines = []

    for stmt in ast.walk(node):
        if isinstance(stmt, ast.Assert):
            assert_count += 1
            assert_lines.append(stmt.lineno)

    is_async = isinstance(node, ast.AsyncFunctionDef)

    return {
        "name": node.name,
        "line": node.lineno,
        "assert_count": assert_count,
        "assert_lines": assert_lines,
        "has_assert": assert_count > 0,
        "async": is_async,
    }


def find_test_functions(tree: ast.AST) -> list:
    """
    Находит все тестовые функции в AST дереве.

    Args:
        tree: AST дерево

    Returns:
        Список с информацией о каждой тестовой функции
    """
    test_functions = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                func_info = find_asserts_in_function(node)
                test_functions.append(func_info)

    return test_functions


def parse_source_code(file_path: str) -> ast.AST:
    """
    Парсит исходный код в AST дерево.

    Args:
        file_path: Путь к файлу

    Returns:
        AST дерево

    Raises:
        SyntaxError: Если в коде есть синтаксические ошибки
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()
    return ast.parse(source_code, filename=file_path)


def lint_file(file_path: str) -> dict:
    """
    Анализирует один файл на наличие assert в тестах.

    Args:
        file_path: Путь к файлу

    Returns:
        Словарь с результатами анализа
    """
    try:
        tree = parse_source_code(file_path)
        test_functions = find_test_functions(tree)
        tests_without_assert = [
            test for test in test_functions if not test["has_assert"]
        ]
        return {
            "file": file_path,
            "success": True,
            "total_tests": len(test_functions),
            "tests_without_assert": tests_without_assert,
            "all_tests": test_functions,
        }
    except SyntaxError as e:
        return {
            "file": file_path,
            "success": False,
            "error": f"Ошибка синтаксиса в строке {e.lineno}: {e.msg}",
        }
    except Exception as e:
        return {"file": file_path, "success": False, "error": str(e)}


def lint_directory(directory: str) -> list:
    """
    Анализирует все тестовые файлы в директории.

    Args:
        directory: Путь к директории

    Returns:
        Список результатов для каждого файла
    """
    results = []
    path = Path(directory)
    patterns = ["test_*.py", "*_test.py"]
    files_found = set()

    for pattern in patterns:
        for file_path in path.rglob(pattern):
            if file_path not in files_found:
                files_found.add(file_path)
                result = lint_file(str(file_path))
                results.append(result)

    return results


def print_report(results: List[Dict[str, Any]]):
    """
    Выводит отчет о результатах проверки.

    Args:
        results: Список результатов анализа
    """
    total_files = len(results)
    total_tests = 0
    total_without_assert = 0
    files_with_issues = 0

    for result in results:
        if result.get("success", False):
            total_tests += result["total_tests"]
            total_without_assert += len(result["tests_without_assert"])
            if result["tests_without_assert"]:
                files_with_issues += 1

    print("\n" + "=" * 70)
    print("ОТЧЕТ ASSERT LINTER")
    print("=" * 70)

    print(f"\n📁 Проверено файлов: {total_files}")
    print(f"🧪 Всего тестов: {total_tests}")
    print(f"⚠️  Тестов без assert: {total_without_assert}")
    print(f"📂 Файлов с проблемами: {files_with_issues}")

    print("\n" + "=" * 70)
    print("ДЕТАЛЬНАЯ ИНФОРМАЦИЯ")
    print("=" * 70)

    for result in results:
        if not result.get("success", False):
            print(f"\n❌ {result['file']}")
            print(f"   Ошибка: {result['error']}")
            continue

        if result["tests_without_assert"]:
            print(f"\n⚠️  {result['file']}")
            print(f"   Найдено тестов: {result['total_tests']}")
            print(f"   Тестов без assert: {len(result['tests_without_assert'])}")
            print("   Проблемные тесты:")
            for test in result["tests_without_assert"]:
                async_mark = " [async]" if test["async"] else ""
                print(f"      • {test['name']}{async_mark} (строка {test['line']})")
        else:
            if result["total_tests"] > 0:
                print(f"\n✅ {result['file']}")
                print(f"   Все тесты ({result['total_tests']}) содержат assert")

    print("\n" + "=" * 70)


def validate_path(path: Path) -> None:
    """
    Проверяет существование пути и выводит ошибку, если путь некорректен.

    Args:
        path: Путь для проверки

    Raises:
        SystemExit: Если путь некорректен
    """
    if not path.exists():
        print(f"❌ Ошибка: путь '{path}' не существует")
        sys.exit(1)


def main():
    """Точка входа в программу."""
    if len(sys.argv) < 2:
        print("Использование: python assert_linter.py <путь>")
        print("\nПримеры:")
        print("  python assert_linter.py tests/")
        print("  python assert_linter.py test_example.py")
        sys.exit(1)

    path_arg = sys.argv[1]
    path = Path(path_arg)

    validate_path(path)

    if path.is_file():
        results = [lint_file(str(path))]
    elif path.is_dir():
        results = lint_directory(str(path))
    else:
        print(f"❌ Ошибка: '{path_arg}' не является файлом или директорией")
        sys.exit(1)

    if not results:
        print(f"⚠️  Тестовые файлы не найдены в '{path_arg}'")
        sys.exit(0)

    print_report(results)

    has_issues = any(
        result.get("success", False) and result["tests_without_assert"]
        for result in results
    )

    if has_issues:
        print("\n❌ Найдены тесты без assert")
        print("Код возврата: 1")
        sys.exit(1)
    else:
        print("\n✅ Все тесты содержат assert")
        print("Код возврата: 0")
        sys.exit(0)


if __name__ == "__main__":
    main()
