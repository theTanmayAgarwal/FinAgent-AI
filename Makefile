.PHONY: install test lint run dashboard docker
install:
	python -m pip install -e '.[dev]'
test:
	pytest --cov=finagent --cov-report=term-missing
lint:
	ruff check finagent tests
run:
	uvicorn finagent.api.main:app --reload
dashboard:
	streamlit run finagent/ui/app.py
docker:
	docker compose up --build

