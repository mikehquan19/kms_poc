format_check:
	ruff format --check .

format_fix:
	ruff format .

lint_check:
	ruff check

lint_fix:
	ruff check --fix

run:
	uvicorn app.main:app --reload

generate_test_keys:
	python loadtest/generate_api_keys.py

locust:
	locust \
		-f loadtest/locustfile.py \
		--host "https://gateway-for-the-kms-poc-e07hwaz1.uc.gateway.dev"
