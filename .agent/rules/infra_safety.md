---
trigger: always_on
glob: "{k8s,terraform}/**/*"
description: Standards for Infrastructure as Code (K8s and Terraform).
---

# Infrastructure Safety Rules

## Kubernetes (k8s)
- **Resource Limits**: Every deployment MUST have esources.limits and esources.requests defined (CPU and Memory).
- **Probes**: Always include livenessProbe and eadinessProbe for services.
- **Namespacing**: Ensure all resources explicitly define their 
amespace.

## Verification`r`n- **Live Audit**: Use `terraform` and `kubernetes` MCPs to verify live resource state against IaC definitions during planning.`r`n`r`n## Terraform
- **State Locking**: Use a remote backend with state locking (e.g., S3 + DynamoDB).
- **Variables**: Never hardcode secrets. Use sensitive = true for secret variables.
- **Modules**: Favor reusable modules over giant monolithic files.

