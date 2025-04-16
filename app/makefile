.ONESHELL:
SHELL := /bin/bash

# Help function to display available commands
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Default target when just running 'make'
.DEFAULT_GOAL := help

# Environment variables with default values
export SERVICE_NAME ?= app
export STACKNAME ?= genaiplatform-$(SERVICE_NAME)
export REGION ?= eu-west-1
export PROJECT ?= genaiplatform
export NAMESPACE ?= genaiplatform
export ENVIRONMENT ?= dev
export IMAGE ?= temp # Will be replaced in CI/CD
export DOMAINNAME ?= platform.genai.enpalm.se
export HOSTEDZONENAME ?= genai.enpalm.se.
export HOSTEDZONEID ?= Z018169127SNH52IY4SRT 

# Mark targets that don't create files as .PHONY
.PHONY: validate build deploy delete go get-api-key

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
		--tags project=$(PROJECT) service=$(SERVICE_NAME) environment=$(ENVIRONMENT) \
		--parameter-overrides \
			IMAGE=$(IMAGE) \
			SERVICENAME=$(SERVICE_NAME) \
			ENVIRONMENT=$(ENVIRONMENT) \
			NAMESPACE=$(NAMESPACE) \
			DOMAINNAME=$(DOMAINNAME) \
			HOSTEDZONENAME=$(HOSTEDZONENAME) \
			HOSTEDZONEID=$(HOSTEDZONEID)

delete: ## Deletes the CloudFormation stack
	@echo "Deleting stack $(STACKNAME) from region $(REGION)..."
	sam delete \
		--stack-name $(STACKNAME) \
		--region $(REGION) \
		--no-prompts

get-api-key: ## Retrieves and prints the API key for the application
	@echo "Retrieving API key from AWS Secrets Manager..."
	@aws secretsmanager get-secret-value \
		--secret-id $(ENVIRONMENT)/$(NAMESPACE)/api \
		--region $(REGION) \
		--query 'SecretString' \
		--output text | jq -r '.apikey'

go: build deploy ## Build and deploys the stack