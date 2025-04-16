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

### Prerequisites

- **LiteLLM Service**: Must be deployed first, as this service references the LiteLLM endpoint via an SSM parameter.
- **Route53 Hosted Zone**: A valid Route53 hosted zone for the domain must exist before deployment. The template creates:
  - An SSL certificate with DNS validation
  - DNS records pointing to the application load balancer
  
### Configuration

The deployment uses these parameters:
- `DomainName`: The full domain for the service (default: platform.genai.enpalm.se)
- `HostedZoneName`: The Route53 hosted zone name with trailing dot (default: genai.enpalm.se.)

If you're using a different domain, update these parameters in the CloudFormation deployment.