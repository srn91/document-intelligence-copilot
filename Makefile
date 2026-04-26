.PHONY: review serve test lint verify clean

review:
	python3 -m app.cli review

serve:
	uvicorn app.main:app --host 127.0.0.1 --port 8000

test:
	pytest -q

lint:
	ruff check app tests

verify: lint test review

clean:
	rm -rf generated
