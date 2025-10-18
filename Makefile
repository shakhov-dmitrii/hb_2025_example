test:
	uv run pytest --alluredir allure-results


format:
	uv run ruff format .