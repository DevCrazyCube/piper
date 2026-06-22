# Piper pipeline — common flows (ADR-0010: CLI + Make, no heavyweight orchestrator).
.PHONY: help init-env up down logs build migrate shell ingest ingest-pmdata ingest-uci-perf \
        ingest-uci-academics ingest-food lint test sast audit check

DC := docker compose
EXEC := $(DC) exec app

help:                ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-22s %s\n", $$1, $$2}'

init-env:            ## Create .env from .env.example with a generated master key (no-op if .env exists)
	@if [ -f .env ]; then \
		echo ".env already exists — leaving it untouched."; \
	else \
		cp .env.example .env; \
		KEY=$$(openssl rand -base64 32 2>/dev/null || python3 -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"); \
		sed -i.bak "s|^PIPER_MASTER_KEY=.*|PIPER_MASTER_KEY=$$KEY|" .env && rm -f .env.bak; \
		echo "Created .env from .env.example and generated PIPER_MASTER_KEY."; \
		echo "Default dev passwords are set — change them before any real deployment."; \
	fi

up: init-env         ## Start the stack (auto-creates .env on first run)
	$(DC) up -d --build

down:                ## Stop the stack
	$(DC) down

logs:                ## Tail logs
	$(DC) logs -f

migrate:             ## Apply DB migrations (schema, hypertables, RLS, roles)
	$(EXEC) alembic upgrade head

bootstrap:           ## Set the app-role password (run once, after migrate)
	$(EXEC) python -m pipeline bootstrap

setup: up migrate bootstrap  ## One-shot first-run: start + migrate + bootstrap

shell:               ## Open a shell in the app container
	$(EXEC) bash

ingest: ingest-pmdata ingest-uci-perf ingest-uci-academics ingest-food  ## Ingest all sources

ingest-pmdata:           ## Ingest PMData (Fitbit + wellness + meals)
	$(EXEC) python -m pipeline ingest pmdata

ingest-uci-perf:         ## Ingest UCI Student Performance (mat + por)
	$(EXEC) python -m pipeline ingest uci-performance

ingest-uci-academics:    ## Ingest UCI Student Academics (ARFF)
	$(EXEC) python -m pipeline ingest uci-academics

ingest-food:             ## Ingest Open Food Facts (minimised reference subset)
	$(EXEC) python -m pipeline ingest openfoodfacts

curate:              ## Curate raw -> curated (make curate D=all|health|academic|food)
	$(EXEC) python -m pipeline curate $(or $(D),all)

analyse:             ## Run the 5 aggregate analytics queries (make analyse Q=all|q1..q5)
	$(EXEC) python -m pipeline analyse $(or $(Q),all)

backup:              ## Encrypted logical backup (3-2-1)
	bash scripts/backup.sh

erase:               ## GDPR Art.17 erase: make erase PID=<uuid>
	$(EXEC) python -m pipeline erase $(PID)

lint:                ## ruff + mypy
	$(EXEC) ruff check src tests && $(EXEC) mypy src

test:                ## Run tests
	$(EXEC) pytest -q

sast:                ## Static security analysis (Week 5)
	$(EXEC) bandit -r src -q

audit:               ## Dependency CVE scan
	$(EXEC) pip-audit

check: lint test sast  ## Lint + test + SAST
