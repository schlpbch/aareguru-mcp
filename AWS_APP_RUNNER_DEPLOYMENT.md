# AWS App Runner Deployment Plan for Aareguru MCP Server

This guide provides step-by-step instructions for deploying the Aareguru MCP server to AWS App Runner.

## Overview

**Why App Runner?**
- ✅ Fully managed container service - no infrastructure to manage
- ✅ Supports long-lived SSE connections (required for MCP protocol)
- ✅ Automatic HTTPS with AWS-managed certificates
- ✅ Auto-scaling (including scale-to-zero option)
- ✅ Built-in load balancing
- ✅ Direct deployment from ECR
- ✅ ~$20-50/month for typical usage

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                               │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │   Route 53  │───▶│  App Runner  │───▶│  Aareguru API    │   │
│  │  (optional) │    │   Service    │    │  (external)      │   │
│  └─────────────┘    └──────────────┘    └──────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │     ECR     │    │   Secrets    │    │   CloudWatch     │   │
│  │  Registry   │    │   Manager    │    │   Logs/Metrics   │   │
│  └─────────────┘    └──────────────┘    └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### 1. AWS Account Setup

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure credentials
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Region (e.g., eu-central-1)
```

### 2. Required Tools

```bash
# Docker (already installed based on your docker-compose build)
docker --version

# AWS CLI
aws --version

# jq (for parsing JSON responses)
sudo apt-get install jq
```

### 3. IAM Permissions

Your AWS user/role needs these permissions:
- `ecr:*` - ECR repository management
- `apprunner:*` - App Runner service management
- `secretsmanager:*` - Secrets Manager access
- `iam:CreateServiceLinkedRole` - For App Runner service role
- `iam:PassRole` - To assign roles to App Runner

---

## Step 1: Create ECR Repository

```bash
# Set variables
export AWS_REGION="eu-central-1"  # Change to your preferred region
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REPO_NAME="aareguru-mcp"

# Create ECR repository
aws ecr create-repository \
    --repository-name ${ECR_REPO_NAME} \
    --region ${AWS_REGION} \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256

# Get repository URI
export ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
echo "ECR Repository: ${ECR_REPO_URI}"
```

---

## Step 2: Build and Push Docker Image

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build the image (from project root)
cd /home/schlpbch/code/aareguru-mcp
docker build -t ${ECR_REPO_NAME}:latest .

# Tag for ECR
docker tag ${ECR_REPO_NAME}:latest ${ECR_REPO_URI}:latest
docker tag ${ECR_REPO_NAME}:latest ${ECR_REPO_URI}:$(git rev-parse --short HEAD)

# Push to ECR
docker push ${ECR_REPO_URI}:latest
docker push ${ECR_REPO_URI}:$(git rev-parse --short HEAD)

# Verify
aws ecr describe-images --repository-name ${ECR_REPO_NAME} --region ${AWS_REGION}
```

---

## Step 3: Create Secrets in AWS Secrets Manager

```bash
# Create secret for API keys (if using authentication)
aws secretsmanager create-secret \
    --name "aareguru-mcp/api-keys" \
    --description "API keys for Aareguru MCP server authentication" \
    --secret-string '{"API_KEYS":"your-secure-api-key-1,your-secure-api-key-2"}' \
    --region ${AWS_REGION}

# Get secret ARN for later use
export SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id "aareguru-mcp/api-keys" \
    --query 'ARN' --output text --region ${AWS_REGION})
echo "Secret ARN: ${SECRET_ARN}"
```

---

## Step 4: Create IAM Roles for App Runner

### 4a. ECR Access Role (for pulling images)

```bash
# Create trust policy
cat > /tmp/apprunner-trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "build.apprunner.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Create the role
aws iam create-role \
    --role-name AareguruMCPAppRunnerECRAccess \
    --assume-role-policy-document file:///tmp/apprunner-trust-policy.json

# Attach ECR read policy
aws iam attach-role-policy \
    --role-name AareguruMCPAppRunnerECRAccess \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess

# Get role ARN
export ECR_ACCESS_ROLE_ARN=$(aws iam get-role \
    --role-name AareguruMCPAppRunnerECRAccess \
    --query 'Role.Arn' --output text)
echo "ECR Access Role ARN: ${ECR_ACCESS_ROLE_ARN}"
```

### 4b. Instance Role (for runtime permissions)

```bash
# Create trust policy for instance role
cat > /tmp/apprunner-instance-trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "tasks.apprunner.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Create instance role
aws iam create-role \
    --role-name AareguruMCPAppRunnerInstanceRole \
    --assume-role-policy-document file:///tmp/apprunner-instance-trust-policy.json

# Create policy for Secrets Manager access
cat > /tmp/secrets-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "${SECRET_ARN}"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name AareguruMCPAppRunnerInstanceRole \
    --policy-name SecretsManagerAccess \
    --policy-document file:///tmp/secrets-policy.json

# Get instance role ARN
export INSTANCE_ROLE_ARN=$(aws iam get-role \
    --role-name AareguruMCPAppRunnerInstanceRole \
    --query 'Role.Arn' --output text)
echo "Instance Role ARN: ${INSTANCE_ROLE_ARN}"
```

---

## Step 5: Create App Runner Service

### Option A: Using AWS CLI

```bash
# Create service configuration
cat > /tmp/apprunner-service.json << EOF
{
    "ServiceName": "aareguru-mcp",
    "SourceConfiguration": {
        "AuthenticationConfiguration": {
            "AccessRoleArn": "${ECR_ACCESS_ROLE_ARN}"
        },
        "AutoDeploymentsEnabled": true,
        "ImageRepository": {
            "ImageIdentifier": "${ECR_REPO_URI}:latest",
            "ImageRepositoryType": "ECR",
            "ImageConfiguration": {
                "Port": "8000",
                "RuntimeEnvironmentVariables": {
                    "LOG_LEVEL": "INFO",
                    "LOG_FORMAT": "json",
                    "API_KEY_REQUIRED": "true",
                    "CORS_ORIGINS": "*",
                    "RATE_LIMIT_PER_MINUTE": "60",
                    "CACHE_TTL_SECONDS": "120",
                    "SSE_SESSION_TIMEOUT_SECONDS": "3600"
                },
                "RuntimeEnvironmentSecrets": {
                    "API_KEYS": "${SECRET_ARN}:API_KEYS::"
                }
            }
        }
    },
    "InstanceConfiguration": {
        "Cpu": "1024",
        "Memory": "2048",
        "InstanceRoleArn": "${INSTANCE_ROLE_ARN}"
    },
    "HealthCheckConfiguration": {
        "Protocol": "HTTP",
        "Path": "/health",
        "Interval": 10,
        "Timeout": 5,
        "HealthyThreshold": 1,
        "UnhealthyThreshold": 5
    },
    "AutoScalingConfigurationArn": "arn:aws:apprunner:${AWS_REGION}:${AWS_ACCOUNT_ID}:autoscalingconfiguration/DefaultConfiguration/1/00000000000000000000000000000001",
    "NetworkConfiguration": {
        "EgressConfiguration": {
            "EgressType": "DEFAULT"
        },
        "IngressConfiguration": {
            "IsPubliclyAccessible": true
        }
    },
    "ObservabilityConfiguration": {
        "ObservabilityEnabled": true
    }
}
EOF

# Create the service
aws apprunner create-service \
    --cli-input-json file:///tmp/apprunner-service.json \
    --region ${AWS_REGION}

# Wait for service to be running (takes 3-5 minutes)
echo "Waiting for service to be ready..."
aws apprunner wait service-running \
    --service-arn $(aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='aareguru-mcp'].ServiceArn" --output text --region ${AWS_REGION}) \
    --region ${AWS_REGION}
```

### Option B: Using AWS Console (Alternative)

1. Go to **AWS Console** → **App Runner**
2. Click **Create service**
3. **Source**: Container registry → Amazon ECR
4. **Container image URI**: `{your-account}.dkr.ecr.{region}.amazonaws.com/aareguru-mcp:latest`
5. **ECR access role**: Select `AareguruMCPAppRunnerECRAccess`
6. **Deployment trigger**: Automatic
7. **Service settings**:
   - Service name: `aareguru-mcp`
   - CPU: 1 vCPU
   - Memory: 2 GB
   - Port: 8000
8. **Environment variables**: Add from table below
9. **Health check**: HTTP, Path: `/health`
10. Click **Create & deploy**

---

## Step 6: Configure Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `LOG_FORMAT` | `json` | JSON format for CloudWatch |
| `API_KEY_REQUIRED` | `true` | Enable API key authentication |
| `API_KEYS` | (from Secrets Manager) | Comma-separated API keys |
| `CORS_ORIGINS` | `*` or specific domains | CORS allowed origins |
| `RATE_LIMIT_PER_MINUTE` | `60` | Rate limit per IP |
| `CACHE_TTL_SECONDS` | `120` | Cache duration |
| `SSE_SESSION_TIMEOUT_SECONDS` | `3600` | SSE session timeout |

---

## Step 7: Verify Deployment

```bash
# Get service URL
export SERVICE_URL=$(aws apprunner describe-service \
    --service-arn $(aws apprunner list-services \
        --query "ServiceSummaryList[?ServiceName=='aareguru-mcp'].ServiceArn" \
        --output text --region ${AWS_REGION}) \
    --query 'Service.ServiceUrl' --output text --region ${AWS_REGION})

echo "Service URL: https://${SERVICE_URL}"

# Test health endpoint
curl -s "https://${SERVICE_URL}/health" | jq .

# Test with API key (if authentication enabled)
curl -s -H "X-API-Key: your-secure-api-key-1" "https://${SERVICE_URL}/health" | jq .

# Test SSE connection
curl -N -H "X-API-Key: your-secure-api-key-1" "https://${SERVICE_URL}/sse"

# Test metrics endpoint
curl -s -H "X-API-Key: your-secure-api-key-1" "https://${SERVICE_URL}/metrics"
```

---

## Step 8: Set Up Custom Domain (Optional)

### Using Route 53

```bash
# Create custom domain association
aws apprunner associate-custom-domain \
    --service-arn $(aws apprunner list-services \
        --query "ServiceSummaryList[?ServiceName=='aareguru-mcp'].ServiceArn" \
        --output text --region ${AWS_REGION}) \
    --domain-name "aare-mcp.yourdomain.com" \
    --region ${AWS_REGION}

# Get DNS validation records
aws apprunner describe-custom-domains \
    --service-arn $(aws apprunner list-services \
        --query "ServiceSummaryList[?ServiceName=='aareguru-mcp'].ServiceArn" \
        --output text --region ${AWS_REGION}) \
    --region ${AWS_REGION}

# Add the CNAME records to your DNS provider
# App Runner will automatically provision SSL certificate
```

---

## Step 9: Set Up CI/CD with GitHub Actions

Create `.github/workflows/deploy-aws.yml`:

```yaml
name: Deploy to AWS App Runner

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: eu-central-1
  ECR_REPOSITORY: aareguru-mcp
  APP_RUNNER_SERVICE: aareguru-mcp

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Install dependencies
        run: uv sync --frozen
      
      - name: Run tests
        run: uv run pytest -v --cov

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    permissions:
      id-token: write
      contents: read
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build, tag, and push image to Amazon ECR
        id: build-image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
          echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT
      
      - name: Trigger App Runner deployment
        run: |
          SERVICE_ARN=$(aws apprunner list-services \
            --query "ServiceSummaryList[?ServiceName=='${{ env.APP_RUNNER_SERVICE }}'].ServiceArn" \
            --output text)
          
          aws apprunner start-deployment --service-arn $SERVICE_ARN
          
          echo "Deployment triggered. App Runner will auto-deploy from ECR."
      
      - name: Wait for deployment
        run: |
          SERVICE_ARN=$(aws apprunner list-services \
            --query "ServiceSummaryList[?ServiceName=='${{ env.APP_RUNNER_SERVICE }}'].ServiceArn" \
            --output text)
          
          echo "Waiting for deployment to complete..."
          aws apprunner wait service-running --service-arn $SERVICE_ARN
          
          SERVICE_URL=$(aws apprunner describe-service \
            --service-arn $SERVICE_ARN \
            --query 'Service.ServiceUrl' --output text)
          
          echo "✅ Deployed to: https://$SERVICE_URL"
      
      - name: Smoke test
        run: |
          SERVICE_URL=$(aws apprunner describe-service \
            --service-arn $(aws apprunner list-services \
              --query "ServiceSummaryList[?ServiceName=='${{ env.APP_RUNNER_SERVICE }}'].ServiceArn" \
              --output text) \
            --query 'Service.ServiceUrl' --output text)
          
          # Test health endpoint
          curl -f "https://$SERVICE_URL/health" || exit 1
          echo "✅ Health check passed"
```

### Set Up GitHub OIDC for AWS

```bash
# Create OIDC provider for GitHub Actions
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# Create deploy role trust policy
cat > /tmp/github-actions-trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:schlpbch/aareguru-mcp:*"
                }
            }
        }
    ]
}
EOF

# Create the role
aws iam create-role \
    --role-name GitHubActionsAareguruMCPDeploy \
    --assume-role-policy-document file:///tmp/github-actions-trust-policy.json

# Attach required policies
aws iam attach-role-policy \
    --role-name GitHubActionsAareguruMCPDeploy \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

# Create App Runner policy
cat > /tmp/apprunner-deploy-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "apprunner:ListServices",
                "apprunner:DescribeService",
                "apprunner:StartDeployment",
                "apprunner:UpdateService"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name GitHubActionsAareguruMCPDeploy \
    --policy-name AppRunnerDeploy \
    --policy-document file:///tmp/apprunner-deploy-policy.json

# Get role ARN - add this to GitHub Secrets as AWS_DEPLOY_ROLE_ARN
aws iam get-role --role-name GitHubActionsAareguruMCPDeploy --query 'Role.Arn' --output text
```

---

## Step 10: Set Up Monitoring & Alerts

### CloudWatch Dashboard

```bash
# Create dashboard
cat > /tmp/dashboard.json << 'EOF'
{
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "title": "Request Count",
                "metrics": [
                    ["AWS/AppRunner", "RequestCount", "ServiceName", "aareguru-mcp"]
                ],
                "period": 60,
                "stat": "Sum"
            }
        },
        {
            "type": "metric",
            "properties": {
                "title": "Response Time (p95)",
                "metrics": [
                    ["AWS/AppRunner", "RequestLatency", "ServiceName", "aareguru-mcp"]
                ],
                "period": 60,
                "stat": "p95"
            }
        },
        {
            "type": "metric",
            "properties": {
                "title": "HTTP 4xx/5xx Errors",
                "metrics": [
                    ["AWS/AppRunner", "4xxStatusResponses", "ServiceName", "aareguru-mcp"],
                    ["AWS/AppRunner", "5xxStatusResponses", "ServiceName", "aareguru-mcp"]
                ],
                "period": 60,
                "stat": "Sum"
            }
        },
        {
            "type": "metric",
            "properties": {
                "title": "Active Instances",
                "metrics": [
                    ["AWS/AppRunner", "ActiveInstances", "ServiceName", "aareguru-mcp"]
                ],
                "period": 60,
                "stat": "Average"
            }
        },
        {
            "type": "metric",
            "properties": {
                "title": "CPU & Memory Utilization",
                "metrics": [
                    ["AWS/AppRunner", "CPUUtilization", "ServiceName", "aareguru-mcp"],
                    ["AWS/AppRunner", "MemoryUtilization", "ServiceName", "aareguru-mcp"]
                ],
                "period": 60,
                "stat": "Average"
            }
        }
    ]
}
EOF

aws cloudwatch put-dashboard \
    --dashboard-name "AareguruMCP" \
    --dashboard-body file:///tmp/dashboard.json \
    --region ${AWS_REGION}
```

### CloudWatch Alarms

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "AareguruMCP-HighErrorRate" \
    --alarm-description "High 5xx error rate on Aareguru MCP" \
    --metric-name "5xxStatusResponses" \
    --namespace "AWS/AppRunner" \
    --dimensions "Name=ServiceName,Value=aareguru-mcp" \
    --statistic Sum \
    --period 300 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --region ${AWS_REGION}

# High latency alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "AareguruMCP-HighLatency" \
    --alarm-description "High response latency on Aareguru MCP" \
    --metric-name "RequestLatency" \
    --namespace "AWS/AppRunner" \
    --dimensions "Name=ServiceName,Value=aareguru-mcp" \
    --extended-statistic p95 \
    --period 300 \
    --threshold 5000 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --region ${AWS_REGION}
```

---

## Cost Estimation

| Component | Monthly Cost (Estimate) |
|-----------|------------------------|
| App Runner (1 vCPU, 2GB, always-on) | ~$25 |
| App Runner (provisioned concurrency) | ~$5 per additional unit |
| ECR Storage | ~$1 (< 1GB images) |
| CloudWatch Logs (10GB/month) | ~$5 |
| Secrets Manager (1 secret) | ~$0.40 |
| Data Transfer (10GB out) | ~$0.90 |
| **Total** | **~$30-40/month** |

**Cost Optimization:**
- Enable "Pause when idle" for dev/staging environments
- Use smaller instance (0.25 vCPU, 0.5GB) for low traffic
- Set appropriate log retention periods

---

## Troubleshooting

### Common Issues

**1. Service fails to start**
```bash
# Check service logs
aws apprunner describe-service \
    --service-arn $(aws apprunner list-services \
        --query "ServiceSummaryList[?ServiceName=='aareguru-mcp'].ServiceArn" \
        --output text --region ${AWS_REGION}) \
    --region ${AWS_REGION}

# Check CloudWatch logs
aws logs tail /aws/apprunner/aareguru-mcp/service --follow --region ${AWS_REGION}
```

**2. ECR image pull fails**
```bash
# Verify ECR access role
aws iam get-role-policy \
    --role-name AareguruMCPAppRunnerECRAccess \
    --policy-name AWSAppRunnerServicePolicyForECRAccess

# Check image exists
aws ecr describe-images --repository-name aareguru-mcp --region ${AWS_REGION}
```

**3. Health check fails**
```bash
# Test locally first
docker run -p 8000:8000 aareguru-mcp:latest
curl http://localhost:8000/health

# Check container logs for startup errors
```

**4. SSE connections dropping**
- App Runner has a default request timeout; SSE connections should work
- Check if client is sending keep-alive pings
- Verify `SSE_SESSION_TIMEOUT_SECONDS` is set appropriately

**5. Secrets not loading**
```bash
# Verify secret exists
aws secretsmanager get-secret-value --secret-id "aareguru-mcp/api-keys" --region ${AWS_REGION}

# Check instance role has permissions
aws iam get-role-policy \
    --role-name AareguruMCPAppRunnerInstanceRole \
    --policy-name SecretsManagerAccess
```

---

## Maintenance Tasks

### Update Docker Image

```bash
# Build and push new image
docker build -t ${ECR_REPO_NAME}:latest .
docker tag ${ECR_REPO_NAME}:latest ${ECR_REPO_URI}:latest
docker push ${ECR_REPO_URI}:latest

# App Runner will auto-deploy if AutoDeploymentsEnabled=true
# Or manually trigger:
aws apprunner start-deployment \
    --service-arn $(aws apprunner list-services \
        --query "ServiceSummaryList[?ServiceName=='aareguru-mcp'].ServiceArn" \
        --output text --region ${AWS_REGION}) \
    --region ${AWS_REGION}
```

### Rotate API Keys

```bash
# Update secret in Secrets Manager
aws secretsmanager update-secret \
    --secret-id "aareguru-mcp/api-keys" \
    --secret-string '{"API_KEYS":"new-key-1,new-key-2,old-key-1"}' \
    --region ${AWS_REGION}

# Restart App Runner service to pick up new secrets
aws apprunner start-deployment \
    --service-arn $(aws apprunner list-services \
        --query "ServiceSummaryList[?ServiceName=='aareguru-mcp'].ServiceArn" \
        --output text --region ${AWS_REGION}) \
    --region ${AWS_REGION}
```

### Scale Configuration

```bash
# Create custom auto-scaling configuration
aws apprunner create-auto-scaling-configuration \
    --auto-scaling-configuration-name "aareguru-mcp-scaling" \
    --max-concurrency 100 \
    --min-size 1 \
    --max-size 5 \
    --region ${AWS_REGION}

# Apply to service (requires service update)
```

---

## Cleanup (Delete Resources)

```bash
# Delete App Runner service
SERVICE_ARN=$(aws apprunner list-services \
    --query "ServiceSummaryList[?ServiceName=='aareguru-mcp'].ServiceArn" \
    --output text --region ${AWS_REGION})

aws apprunner delete-service --service-arn ${SERVICE_ARN} --region ${AWS_REGION}

# Delete ECR repository (and all images)
aws ecr delete-repository \
    --repository-name aareguru-mcp \
    --force \
    --region ${AWS_REGION}

# Delete secrets
aws secretsmanager delete-secret \
    --secret-id "aareguru-mcp/api-keys" \
    --force-delete-without-recovery \
    --region ${AWS_REGION}

# Delete IAM roles
aws iam delete-role-policy --role-name AareguruMCPAppRunnerInstanceRole --policy-name SecretsManagerAccess
aws iam detach-role-policy --role-name AareguruMCPAppRunnerECRAccess --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess
aws iam delete-role --role-name AareguruMCPAppRunnerInstanceRole
aws iam delete-role --role-name AareguruMCPAppRunnerECRAccess

# Delete CloudWatch dashboard and alarms
aws cloudwatch delete-dashboards --dashboard-names "AareguruMCP" --region ${AWS_REGION}
aws cloudwatch delete-alarms --alarm-names "AareguruMCP-HighErrorRate" "AareguruMCP-HighLatency" --region ${AWS_REGION}
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| View service status | `aws apprunner describe-service --service-arn $SERVICE_ARN` |
| View logs | `aws logs tail /aws/apprunner/aareguru-mcp/service --follow` |
| Trigger deployment | `aws apprunner start-deployment --service-arn $SERVICE_ARN` |
| Pause service | `aws apprunner pause-service --service-arn $SERVICE_ARN` |
| Resume service | `aws apprunner resume-service --service-arn $SERVICE_ARN` |
| List all services | `aws apprunner list-services` |

---

## Next Steps

1. ✅ Follow Steps 1-7 to deploy manually first
2. ✅ Verify health checks and SSE connections work
3. ✅ Set up CI/CD (Step 9) for automated deployments
4. ✅ Configure monitoring (Step 10)
5. 🔄 Optional: Custom domain, scaling optimization

---

*Last updated: December 2025*
