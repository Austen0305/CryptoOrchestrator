# Infrastructure as Code Guide

This guide covers deploying CryptoOrchestrator using infrastructure as code (IaC) tools.

## Overview

CryptoOrchestrator supports multiple deployment methods:
- **Kubernetes**: Production-ready container orchestration
- **Terraform**: Infrastructure provisioning for AWS, Azure, GCP
- **Docker Compose**: Simple single-server deployment

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- `kubectl` configured
- `kustomize` installed (optional, for advanced customization)

### Quick Start

1. **Create namespace and secrets**:
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/secrets.yaml
   # Edit secrets.yaml with your actual values before applying
   ```

2. **Deploy database and cache**:
   ```bash
   kubectl apply -f k8s/postgres.yaml
   kubectl apply -f k8s/redis.yaml
   ```

3. **Deploy application**:
   ```bash
   kubectl apply -f k8s/backend-deployment.yaml
   kubectl apply -f k8s/frontend-deployment.yaml
   kubectl apply -f k8s/celery-worker.yaml
   ```

4. **Configure ingress**:
   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```

### Using Kustomize

For environment-specific configurations:

```bash
kubectl apply -k k8s/
```

### Configuration

#### Secrets

Edit `k8s/secrets.yaml` with your actual values:
- Database credentials
- JWT secrets (generate strong random strings)
- API keys (Stripe, SMTP, etc.)

**Important**: Never commit secrets to git. Use sealed-secrets or external secret management.

#### ConfigMap

Edit `k8s/configmap.yaml` for non-sensitive configuration:
- Domain names
- Environment variables
- Feature flags

#### Resource Limits

Adjust resource requests/limits in deployment files based on your workload:
- Backend: Default 512Mi-2Gi memory, 500m-2000m CPU
- Frontend: Default 128Mi-256Mi memory, 100m-500m CPU
- Celery Worker: Default 512Mi-2Gi memory, 500m-2000m CPU

#### Scaling

HorizontalPodAutoscaler (HPA) is configured for:
- Backend: 3-10 replicas based on CPU/memory
- Frontend: 3-10 replicas based on CPU/memory

Adjust HPA settings in deployment files.

### Health Checks

All deployments include:
- **Liveness probes**: Restart unhealthy containers
- **Readiness probes**: Remove from service during startup/updates

### Persistent Storage

- PostgreSQL: 100Gi PVC (adjust in `postgres.yaml`)
- Redis: 50Gi PVC (adjust in `redis.yaml`)

Ensure your cluster has a StorageClass configured.

### Monitoring

Integrate with:
- Prometheus for metrics
- Grafana for dashboards
- ELK stack for logs

## Terraform (AWS)

### Prerequisites

- Terraform >= 1.0
- AWS CLI configured
- AWS account with appropriate permissions

### Setup

1. **Configure variables**:
   ```bash
   cd terraform/aws
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars
   ```

2. **Initialize**:
   ```bash
   terraform init
   ```

3. **Plan**:
   ```bash
   terraform plan
   ```

4. **Apply**:
   ```bash
   terraform apply
   ```

### Architecture

- **VPC**: Multi-AZ VPC with public/private subnets
- **EKS**: Managed Kubernetes cluster
- **RDS**: PostgreSQL with automated backups
- **ElastiCache**: Redis cluster
- **ALB**: Application Load Balancer
- **S3**: Backup storage

### Cost Estimation

See `terraform/aws/README.md` for cost estimates.

## Docker Compose

For simple deployments, use `docker-compose.prod.yml`:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

See `README.md` for detailed Docker Compose instructions.

## Environment-Specific Configurations

### Development

- Single replica deployments
- Lower resource limits
- Local storage
- No auto-scaling

### Staging

- 2-3 replicas
- Medium resource limits
- Production-like storage
- Basic auto-scaling

### Production

- 3+ replicas
- High resource limits
- Persistent storage with backups
- Full auto-scaling
- Multi-AZ deployment
- Monitoring and alerting

## Backup Strategy

### Database Backups

- **Automated**: RDS automated backups (7-day retention)
- **Manual**: `kubectl exec` into postgres pod and run `pg_dump`
- **S3**: Automated backups to S3 bucket

### Redis Backups

- **AOF**: Append-only file enabled
- **Snapshots**: Daily snapshots configured
- **S3**: Backup snapshots to S3

### Application Data

- Persistent volumes backed up via Velero or similar
- S3 for model storage and artifacts

## Disaster Recovery

### RTO/RPO Targets

- **RTO**: 1 hour (Recovery Time Objective)
- **RPO**: 15 minutes (Recovery Point Objective)

### Recovery Procedures

1. **Database**: Restore from latest backup
2. **Redis**: Restore from snapshot or rebuild cache
3. **Application**: Redeploy from container registry
4. **DNS**: Update DNS records to point to new infrastructure

See `docs/DISASTER_RECOVERY.md` for detailed procedures.

## Security Considerations

### Network Security

- Private subnets for databases and cache
- Security groups with least privilege
- VPC peering for multi-region (if needed)

### Secrets Management

- Use Kubernetes secrets (base64 encoded)
- Consider external secret management (AWS Secrets Manager, HashiCorp Vault)
- Rotate secrets regularly

### Container Security

- Scan images for vulnerabilities
- Use non-root users in containers
- Implement network policies
- Enable Pod Security Standards

### Compliance

- Enable audit logging
- Encrypt data at rest and in transit
- Implement access controls
- Regular security scans

## Monitoring & Observability

### Metrics

- Prometheus for metrics collection
- Grafana for visualization
- Custom business metrics

### Logging

- Centralized logging (ELK, Loki, CloudWatch)
- Structured logging format
- Log retention policies

### Tracing

- OpenTelemetry for distributed tracing
- Jaeger or similar for trace visualization

### Alerting

- Prometheus Alertmanager
- PagerDuty/Slack integration
- Critical alert escalation

## Scaling Strategies

### Horizontal Scaling

- HPA for automatic pod scaling
- Cluster autoscaler for node scaling
- Multi-region deployment for global scale

### Vertical Scaling

- Adjust resource limits based on metrics
- Upgrade instance types if needed

### Database Scaling

- Read replicas for read-heavy workloads
- Connection pooling
- Query optimization

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check resource limits, image pull secrets
2. **Database connection failures**: Verify security groups, credentials
3. **High memory usage**: Review resource limits, optimize code
4. **Slow performance**: Check database indexes, cache hit rates

### Debugging Commands

```bash
# Check pod status
kubectl get pods -n cryptoorchestrator

# View logs
kubectl logs -f deployment/backend -n cryptoorchestrator

# Describe pod for events
kubectl describe pod <pod-name> -n cryptoorchestrator

# Exec into pod
kubectl exec -it <pod-name> -n cryptoorchestrator -- /bin/bash

# Check ingress
kubectl get ingress -n cryptoorchestrator

# View HPA status
kubectl get hpa -n cryptoorchestrator
```

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
