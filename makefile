.ONESHELL:
SHELL := /bin/bash

# Help function to display available commands
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Default target when just running 'make'
.DEFAULT_GOAL := help

# Mark targets that don't create files as .PHONY
.PHONY: local local-stop

### Setting up local dev environment

local: ## Starts local dev environment
	@echo "Starting local development environment..."
	docker-compose up --build

local-stop: ## Stops the local dev environment
	@echo "Stopping local development environment..."
	docker-compose down