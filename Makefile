test:
	X_CG_DEMO_API_KEY=$(X_CG_DEMO_API_KEY) uv run pytest --alluredir allure-results

send_report:
	TG_BOT_TOKEN=$(TG_BOT_TOKEN) uv run ./scripts/send_allure_results.py

format:
	uv run ruff format .