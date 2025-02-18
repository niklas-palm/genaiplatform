.ONESHELL:
SHELL := /bin/bash

# Help function to display available commands
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Default target when just running 'make'
.DEFAULT_GOAL := help

# Environment variables with default values
export STACKNAME ?= genaiplatform
export REGION ?= eu-west-1
export PROJECT ?= genaiplatform
export ENVIRONMENT ?= dev
export NAMESPACE ?= genaiplatform

# Mark targets that don't create files as .PHONY
.PHONY: build deploy delete validate go

validate: ## Validates and lints the SAM template
	@echo "Validating SAM template..."
	sam validate --lint

build: ## Downloads all dependencies and builds resources
	@echo "Building SAM application..."
	sam build --use-container

deploy: ## Deploys the artifacts from the previous build
	@echo "Deploying stack $(STACKNAME) to region $(REGION)..."
	sam deploy \
		--stack-name $(STACKNAME) \
		--resolve-s3 \
		--capabilities CAPABILITY_IAM \
		--region $(REGION) \
		--no-fail-on-empty-changeset \
		--tags project=$(PROJECT) service=$(STACKNAME) environment=$(ENVIRONMENT) \
		--parameter-overrides \
			ENVIRONMENT=$(ENVIRONMENT) \
			NAMESPACE=$(NAMESPACE)

delete: ## Deletes the CloudFormation stack
	@echo "Deleting stack $(STACKNAME) from region $(REGION)..."
	sam delete \
		--stack-name $(STACKNAME) \
		--region $(REGION) \
		--no-prompts

go: build deploy ## Build and deploys the stack
