# AWS Infrastructure as Code

This directory contains Terraform configurations for deploying CryptoOrchestrator on AWS.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- AWS account with necessary permissions

## Architecture

- **VPC**: Custom VPC with public and private subnets across 3 availability zones
- **EKS**: Managed Kubernetes cluster for container orchestration
- **RDS PostgreSQL**: Managed PostgreSQL database with automated backups
- **ElastiCache Redis**: Managed Redis cluster for caching and Celery
- **Application Load Balancer**: For routing traffic to EKS
- **S3**: For database backups and artifacts

## Setup

1. **Configure variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

2. **Initialize Terraform**:
   ```bash
   terraform init
   ```

3. **Plan deployment**:
   ```bash
   terraform plan
   ```

4. **Apply configuration**:
   ```bash
   terraform apply
   ```

## Variables

- `aws_region`: AWS region (default: us-east-1)
- `environment`: Environment name (default: production)
- `db_password`: PostgreSQL password (sensitive)
- `redis_password`: Redis password (sensitive)
- `domain_name`: Domain name (default: cryptoorchestrator.com)

## Outputs

After deployment, Terraform outputs:
- VPC ID
- EKS cluster endpoint
- RDS endpoint
- Redis endpoint
- ALB DNS name
- S3 backup bucket name

## Cost Estimation

Estimated monthly costs (us-east-1):
- EKS Cluster: ~$73/month
- EKS Node Group (3x t3.medium): ~$90/month
- RDS PostgreSQL (db.t3.medium): ~$100/month
- ElastiCache Redis (2x cache.t3.medium): ~$60/month
- ALB: ~$20/month
- Data Transfer: Variable
- **Total**: ~$343/month + data transfer

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

**Warning**: This will delete all resources including databases. Ensure you have backups!
