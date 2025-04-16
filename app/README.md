# Platform API Service

This service provides the client-facing API for the GenAI Platform.

## Overview

- FastAPI application serving as the frontend interface
- Handles client authentication via API keys
- Validates and processes incoming requests
- Proxies requests to the LiteLLM service
- Provides health checks and operational endpoints

## Key Files

- `image/` - Contains the Docker container configuration
  - `Dockerfile` - Container build instructions
  - `app.py` - Main FastAPI application code
  - `requirements.txt` - Python dependencies
- `template.yaml` - CloudFormation/SAM template for deploying the service
- `makefile` - Contains utility commands for local development

## Deployment

Deployment is handled automatically by GitHub Actions when changes are pushed to this directory.
The service requires the LiteLLM service to be deployed first, as it references the LiteLLM endpoint via an SSM parameter.