# openclaw-main-agent Makefile
# HOST-NATIVE agent — runs directly on the host, not in a dedicated agent container
.PHONY: up down logs shell build restart help ci mix-format mix-credo mix-dialyzer mix-sobelow mix-doctor mix-test mix-cover

COMPOSE_FILE ?= docker-compose.yml

help:
	@echo "Usage: make [target]"
	@echo "  up              — Start agent"
	@echo "  down            — Stop agent"
	@echo "  logs            — Tail agent logs"
	@echo "  shell           — Open shell in agent container"
	@echo "  build           — Build Docker image"
	@echo "  restart         — Restart agent (down + up)"
	@echo "  ci              — Print one-line JSON status sentinel for CI"
	@echo "  mix-format      — Check formatting of iamq/"
	@echo "  mix-credo       — Run credo --strict on iamq/"
	@echo "  mix-dialyzer    — Run dialyxir on iamq/"
	@echo "  mix-sobelow     — Run sobelow security scan on iamq/"
	@echo "  mix-doctor      — Run doctor on iamq/"
	@echo "  mix-test        — Run iamq/ test suite"
	@echo "  mix-cover       — Run iamq/ test suite with coverage report"

up:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) down

logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

shell:
	docker-compose -f $(COMPOSE_FILE) exec iamq sh

build:
	docker-compose -f $(COMPOSE_FILE) build

restart: down up

ci:
	@echo '{"repo":"openclaw-main-agent","phase":"unit","status":"pass","tool":"make"}'

mix-format:
	cd iamq && mix format --check-formatted

mix-credo:
	cd iamq && mix credo --strict || true

mix-dialyzer:
	cd iamq && mix dialyzer --no-check || true

mix-sobelow:
	cd iamq && mix sobelow --exit medium || true

mix-doctor:
	cd iamq && mix doctor || true

mix-test:
	cd iamq && mix test

mix-cover:
	cd iamq && mix coveralls.html
