test:
	X_CG_DEMO_API_KEY=$(X_CG_DEMO_API_KEY) TG_BOT_TOKEN=$(TG_BOT_TOKEN) uv run pytest --alluredir allure-results


format:
	uv run ruff format .