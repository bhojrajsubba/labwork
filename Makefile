# Makefile for managing Vulnerability Labs

.PHONY: help up down logs restart reset test-vuln test-sec

help:
	@echo "Available commands:"
	@echo "  make up LAB=<lab-name>       Start a specific lab (e.g. make up LAB=wcd-01)"
	@echo "  make down LAB=<lab-name>     Stop a specific lab"
	@echo "  make logs LAB=<lab-name>     View logs of a lab"
	@echo "  make test LAB=<lab-name>     Run exploit test against the running lab"
	@echo "  make reset LAB=<lab-name>    Rebuild containers and reset cache/database"

up:
	@if [ -z "$(LAB)" ]; then \
		echo "Error: LAB argument required. Example: make up LAB=wcd-01"; exit 1; \
	fi
	docker compose --profile $(LAB) up --build -d
	@echo "Lab $(LAB) is running! Check .env for the port (default: http://localhost:8080)."

down:
	@if [ -z "$(LAB)" ]; then \
		echo "Error: LAB argument required. Example: make down LAB=wcd-01"; exit 1; \
	fi
	docker compose --profile $(LAB) down

logs:
	@if [ -z "$(LAB)" ]; then \
		echo "Error: LAB argument required. Example: make logs LAB=wcd-01"; exit 1; \
	fi
	docker compose --profile $(LAB) logs -f

test:
	@if [ -z "$(LAB)" ]; then \
		echo "Error: LAB argument required. Example: make test LAB=wcd-01"; exit 1; \
	fi
	python labs/01-web-cache-deception/wcd-01-path-mapping/exploit.py

reset:
	@if [ -z "$(LAB)" ]; then \
		echo "Error: LAB argument required. Example: make reset LAB=wcd-01"; exit 1; \
	fi
	docker compose --profile $(LAB) down -v
	docker compose --profile $(LAB) up --build -d
