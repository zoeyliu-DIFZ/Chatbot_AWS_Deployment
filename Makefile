# AI Chat Assistant - SAM Deployment Makefile

.PHONY: help install build deploy clean local-test local-interactive local-api local-invoke

# Default environment - changed from prod to dev for safety
ENV ?= dev

help: ## Show this help message
	@echo "AI Chat Assistant - SAM Deployment"
	@echo ""
	@echo "Usage:"
	@echo "  make <target> [ENV=environment]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Environments: dev, staging, prod (default: dev for safety)"

install: ## Install deployment dependencies
	@echo "📦 Installing deployment dependencies..."
	pip install -r requirements-deploy.txt

build: ## Build the SAM application
	@echo "🔨 Building SAM application..."
	sam build

deploy: ## Deploy to specified environment (default: dev)
	@echo "🚀 Deploying to $(ENV) environment..."
	python deploy.py $(ENV)

deploy-dev: ## Deploy to dev environment
	@$(MAKE) deploy ENV=dev

deploy-staging: ## Deploy to staging environment  
	@$(MAKE) deploy ENV=staging

deploy-prod: ## Deploy to prod environment
	@$(MAKE) deploy ENV=prod

clean: ## Clean build artifacts
	@echo "🧹 Cleaning build artifacts..."
	rm -rf .aws-sam/

validate: ## Validate SAM template
	@echo "✅ Validating SAM template..."
	sam validate

local-start: ## Start local API for testing
	@echo "🔧 Starting local API..."
	sam local start-api --port 3000

local-test: ## Run automated local tests
	@echo "🧪 Running local tests..."
	python local_test.py

local-interactive: ## Run interactive local testing
	@echo "🎯 Starting interactive testing..."
	python local_test.py --interactive

local-api: ## Start local API server for testing
	@echo "🔧 Starting local API server..."
	sam local start-api --port 3000 --host 0.0.0.0

local-invoke: ## Test Lambda function directly
	@echo "⚡ Testing Lambda function directly..."
	echo '{"message": "Hello, test message"}' | sam local invoke ChatFunction --event -

logs: ## View CloudFormation logs for the stack
	@echo "📋 Viewing logs for $(ENV) environment..."
	aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/ai-chat-assistant-$(ENV)"

status: ## Show deployment status
	@echo "📊 Deployment status for $(ENV) environment..."
	aws cloudformation describe-stacks --stack-name ai-chat-assistant-$(ENV) --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "Stack not found" 