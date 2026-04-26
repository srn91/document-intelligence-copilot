.PHONY: review analyze-image serve test lint verify clean

review:
	python3 -m app.cli review

analyze-image:
	python3 -m app.cli analyze-image

serve:
	uvicorn app.main:app --host 127.0.0.1 --port 8000

test:
	pytest -q

lint:
	ruff check app tests

verify: lint test review analyze-image

clean:
	rm -rf generated
