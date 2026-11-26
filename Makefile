# Makefile for managing Vulnerability Labs

# Case-tolerant LAB parameter (accepts LAB, lab, lAB, Lab)
TARGET_LAB ?= $(or $(LAB),$(lab),$(lAB),$(Lab))

.PHONY: help up down logs restart reset test

help:
	@echo "Available commands:"
	@echo "  make up LAB=<lab-name>       Start a specific lab (e.g. make up LAB=wcd-01 or make up LAB=wcd-02)"
	@echo "  make down LAB=<lab-name>     Stop a specific lab"
	@echo "  make logs LAB=<lab-name>     View logs of a lab"
	@echo "  make test LAB=<lab-name>     Run exploit test against the running lab"
	@echo "  make reset LAB=<lab-name>    Rebuild containers and reset cache/database"

up:
	@if [ -z "$(TARGET_LAB)" ]; then \
		echo "Error: LAB argument required. Example: make up LAB=wcd-02"; exit 1; \
	fi
	docker compose --profile $(TARGET_LAB) up --build -d
	@echo "Lab $(TARGET_LAB) is running! Accessible at http://127.0.0.1:8081"

down:
	@if [ -z "$(TARGET_LAB)" ]; then \
		echo "Error: LAB argument required. Example: make down LAB=wcd-02"; exit 1; \
	fi
	docker compose --profile $(TARGET_LAB) down

logs:
	@if [ -z "$(TARGET_LAB)" ]; then \
		echo "Error: LAB argument required. Example: make logs LAB=wcd-02"; exit 1; \
	fi
	docker compose --profile $(TARGET_LAB) logs -f

test:
	@if [ -z "$(TARGET_LAB)" ]; then \
		echo "Error: LAB argument required. Example: make test LAB=wcd-02"; exit 1; \
	elif [ "$(TARGET_LAB)" = "wcd-01" ]; then \
		python labs/01-web-cache-deception/wcd-01-path-mapping/exploit.py --url http://127.0.0.1:8081; \
	elif [ "$(TARGET_LAB)" = "wcd-02" ]; then \
		python labs/01-web-cache-deception/wcd-02-delimiter/exploit.py --url http://127.0.0.1:8081; \
	else \
		echo "Unknown lab: $(TARGET_LAB)"; exit 1; \
	fi

reset:
	@if [ -z "$(TARGET_LAB)" ]; then \
		echo "Error: LAB argument required. Example: make reset LAB=wcd-02"; exit 1; \
	fi
	docker compose --profile $(TARGET_LAB) down -v
	docker compose --profile $(TARGET_LAB) up --build -d
