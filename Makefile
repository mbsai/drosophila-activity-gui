# Convenience targets for developing and running the app.
.PHONY: help setup run sample test lint docker-build docker-run dev clean

help:            ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup:           ## Install Python dependencies
	pip install -r requirements.txt -r requirements-dev.txt

run:             ## Run the app locally
	streamlit run app.py

sample:          ## Generate synthetic sample data in ./sample_data
	python make_sample_data.py

test:            ## Run the test suite
	pytest -q

docker-build:    ## Build the self-contained Docker image
	docker build -t dam-gui .

docker-run:      ## Run the Docker image (http://localhost:8501)
	docker run --rm -p 8501:8501 dam-gui

dev:             ## Live-reload dev container (edits reflect without rebuild)
	docker compose up --build

clean:           ## Remove caches and generated outputs
	rm -rf **/__pycache__ .pytest_cache sample_data *_plots dam_out_* *.xlsx
