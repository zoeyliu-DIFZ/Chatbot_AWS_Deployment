# AI Chat Assistant - MVP

A minimal viable product for an AI chat assistant using AWS SAM, Lambda, and Claude 3.5 Sonnet.

## 📁 Project Structure

```
├── src/                    # Lambda function source code
│   ├── lambda_function.py  # Main Lambda handler
│   ├── agent.py           # ChatAgent implementation
│   ├── default_prompt.txt # System prompt
│   └── requirements.txt   # Python dependencies
├── frontend/              # Static website files
│   ├── index.html        # Production frontend
│   └── index-local.html  # Local development frontend
├── update-frontend/       # Custom resource for frontend deployment
│   ├── index.py          # Lambda function to update frontend
│   └── requirements.txt  # Dependencies
├── template.yaml         # SAM infrastructure template
├── samconfig.toml        # SAM configuration
├── deploy-config.yaml    # YAML deployment configuration
├── deploy.py            # Python deployment script
├── Makefile             # Easy deployment commands
└── requirements-deploy.txt # Deployment script dependencies
```

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **SAM CLI** installed (`brew install aws-sam-cli`)
3. **Python 3.9+** with pip

### Installation

```bash
# Install deployment dependencies
make install

# Or manually:
pip install -r requirements-deploy.txt
```

### Deployment

```bash
# Deploy to production (default)
make deploy

# Deploy to specific environment
make deploy-dev
make deploy-staging
make deploy-prod

# Or use the Python script directly
python deploy.py prod
python deploy.py dev
```

## 🛠️ Development

### Local Testing

```bash
# Validate SAM template
make validate

# Start local API
make local-start
```

### Build

```bash
# Build the application
make build
```

### Clean Up

```bash
# Remove build artifacts
make clean
```

## 📊 Monitoring

```bash
# Check deployment status
make status ENV=prod

# View logs
make logs ENV=prod
```

## ⚙️ Configuration

Edit `deploy-config.yaml` to customize:

- Environment-specific settings
- AWS regions
- Claude model versions
- Resource configurations

## 🏗️ Architecture

- **Lambda Function**: Handles chat API requests using Claude 3.5 Sonnet
- **API Gateway**: REST API with CORS enabled
- **S3 Bucket**: Hosts static frontend website
- **Custom Resource**: Updates frontend with API endpoint URL

## 📝 Environment Variables

The application uses these environment variables (set via SAM parameters):

- `ENVIRONMENT`: Deployment environment (dev/staging/prod)
- `CLAUDE_MODEL_ID`: Claude model identifier

## 🔧 Available Commands

Run `make help` to see all available commands:

```bash
make help
```

## 📋 Notes

- This is a minimal viable product focused on core functionality
- All duplicate files and unnecessary complexity have been removed
- Uses YAML configuration for clean, maintainable deployments
- Supports multiple environments (dev, staging, prod) 