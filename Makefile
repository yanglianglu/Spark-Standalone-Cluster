COMPOSE ?= docker compose
BASE_FILES = -f compose.base.yml -f compose.spark.yml
DEV_FILES = $(BASE_FILES) -f compose.dev.yml
FULL_FILES = $(BASE_FILES) -f compose.history.yml -f compose.scale-2w.yml
FILES ?= $(BASE_FILES)
PYTHON ?= python
SERVICE ?=

.PHONY: up up-dev up-full down down-full logs ps reset smoke

up:
	$(COMPOSE) $(BASE_FILES) up -d

up-dev:
	$(COMPOSE) $(DEV_FILES) up -d

up-full:
	$(COMPOSE) $(FULL_FILES) up -d

down:
	$(COMPOSE) $(FILES) down

down-full:
	$(COMPOSE) $(FULL_FILES) down

logs:
	$(COMPOSE) $(FILES) logs -f $(SERVICE)

ps:
	$(COMPOSE) $(FILES) ps

reset:
	$(COMPOSE) $(FILES) down -v
	$(PYTHON) scripts/reset_data.py

smoke:
	$(PYTHON) scripts/smoke.py
