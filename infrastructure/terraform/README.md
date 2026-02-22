# Terraform Infrastructure as Code for RandWater

This directory contains the Terraform configuration to deploy the National Water Infrastructure Monitoring System on AWS.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet (Route53)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
            ┌────────▼────────┐
            │   CloudFront    │
            │   (CDN)         │
            └────────┬────────┘
                     │
            ┌────────▼──────────────────┐
            │   Application Load        │
            │   Balancer                │
            └────────┬──────────────────┘
                     │
        ┌────────────┴────────────────┐
        │                             │
   ┌────▼──────────┐          ┌──────▼──────┐
   │  EKS Cluster  │          │   NAT GW    │
   │  (Kubernetes) │          │             │
   │  - Pod        │          └─────────────┘
   │  - Services   │
   │  - Ingress    │
   └────┬──────────┘
        │
   ┌────┴─────────────────────────────────┐
   │          Private Subnets              │
   │  ┌──────────────┐  ┌──────────────┐  │
   │  │  RDS Aurora  │  │ ElastiCache  │  │
   │  │ (PostgreSQL) │  │  (Redis)     │  │
   │  └──────────────┘  └──────────────┘  │
   │                                       │
   │  ┌──────────────────────────────┐    │
   │  │   S3 (Backups & Logs)        │    │
   │  └──────────────────────────────┘    │
   └───────────────────────────────────────┘
```

## Prerequisites

### Required Tools

- **Terraform:** >= 1.0
  ```bash
  # macOS
  brew install terraform
  
  # Linux
  wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
  unzip terraform_1.7.0_linux_amd64.zip
  sudo mv terraform /usr/local/bin/
  ```

- **AWS CLI:** >= 2.0
  ```bash
  brew install awscli
  # or
  pip install awscli
  ```

- **kubectl:** >= 1.28
  ```bash
  brew install kubectl
  # or get from https://kubernetes.io/docs/tasks/tools/
  ```

- **Helm:** >= 3.12
  ```bash
  brew install helm
  ```

### AWS Requirements

- AWS Account with appropriate IAM permissions
- AWS Credentials configured locally
  ```bash
  aws configure
  # or
  export AWS_ACCESS_KEY_ID=xxxxx
  export AWS_SECRET_ACCESS_KEY=xxxxx
  export AWS_DEFAULT_REGION=us-east-1
  ```

## Quick Start

### 1. Initialize Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform (downloads providers, creates backend)
terraform init

# Verify configuration
terraform validate

# Format code
terraform fmt -recursive
```

### 2. Plan Deployment

```bash
# Create tfvars file from example
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars

# Plan infrastructure
terraform plan -out=tfplan

# Review the plan and verify resources
```

### 3. Apply Configuration

```bash
# Apply the plan
terraform apply tfplan

# Wait for infrastructure to be created (30-45 minutes typical)
# - EKS Cluster: 10-15 minutes
# - RDS Database: 10-15 minutes
# - ElastiCache: 3-5 minutes
# - Network: 2-3 minutes

# Get outputs
terraform output
```

### 4. Configure kubectl

```bash
# Update kubeconfig with EKS cluster info
aws eks update-kubeconfig \
  --region us-east-1 \
  --name randwater-production

# Verify cluster access
kubectl get nodes
kubectl get pods -A
```

## File Structure

```
infrastructure/terraform/
├── main.tf              # Main configuration (EKS, RDS, ElastiCache)
├── variables.tf         # Variable definitions
├── terraform.tfvars     # Variable values (CREATE FROM EXAMPLE)
├── terraform.tfvars.example
├── outputs.tf           # Output definitions
├── versions.tf          # Required versions
├── modules/
│   └── vpc/
│       ├── main.tf      # VPC, subnets, NAT gateways
│       ├── variables.tf
│       ├── outputs.tf
│       └── README.md
├── environments/        # Environment-specific configs
│   ├── dev.tfvars
│   ├── staging.tfvars
│   └── production.tfvars
└── README.md           # This file
```

## Configuration

### Environment-Specific Deployment

```bash
# Development
terraform plan -var-file=environments/dev.tfvars -out=tfplan-dev
terraform apply tfplan-dev

# Staging
terraform plan -var-file=environments/staging.tfvars -out=tfplan-staging
terraform apply tfplan-staging

# Production
terraform plan -var-file=environments/production.tfvars -out=tfplan-prod
terraform apply tfplan-prod
```

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | us-east-1 | AWS region |
| `environment` | production | dev/staging/production |
| `kubernetes_version` | 1.28 | Kubernetes version |
| `node_instance_types` | t3.large | EC2 instance types |
| `node_desired_size` | 3 | Initial node count |
| `db_instance_class` | db.t3.large | RDS instance type |
| `redis_node_type` | cache.t3.medium | Redis node type |
| `backup_retention_days` | 30 | Backup retention |

## Deployment Options

### Option 1: Development (Minimal Cost)

```hcl
# terraform.tfvars
environment = "dev"
node_instance_types = ["t3.medium"]
node_desired_size = 1
node_max_size = 3
db_instance_class = "db.t3.medium"
redis_node_type = "cache.t3.small"
```

**Estimated Cost:** $200-300/month

### Option 2: Staging (Testing)

```hcl
# terraform.tfvars
environment = "staging"
node_instance_types = ["t3.large"]
node_desired_size = 2
db_instance_class = "db.t3.large"
redis_node_type = "cache.t3.medium"
```

**Estimated Cost:** $400-500/month

### Option 3: Production (High Availability)

```hcl
# terraform.tfvars
environment = "production"
node_instance_types = ["m5.xlarge"]
node_desired_size = 5
db_instance_class = "db.r5.2xlarge"
redis_node_type = "cache.r6g.xlarge"
enable_cross_region_replica = true
```

**Estimated Cost:** $1,500-2,000/month

## Monitoring & Operations

### Check Cluster Status

```bash
# Check EKS cluster
kubectl get nodes -o wide

# Check deployments
kubectl get deployments -A

# Check pod status
kubectl get pods -A

# View cluster logs
kubectl logs -n kube-system -l component=kubelet --tail=50
```

### Access RDS Database

```bash
# Get RDS endpoint from Terraform output
ENDPOINT=$(terraform output -raw rds_endpoint)

# Connect to database (requires psql installed)
psql -h $ENDPOINT -U postgres -d randwater

# Or via EC2 bastion (recommended for production)
ssh -i key.pem ec2-user@bastion-ip
psql -h $ENDPOINT -U postgres -d randwater
```

### Access Redis

```bash
# Get Redis endpoint
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)

# Connect via redis-cli
redis-cli -h $REDIS_ENDPOINT -p 6379

# Or from within a pod
kubectl run -it --rm redis-client --image=redis:7 -- redis-cli -h $REDIS_ENDPOINT -p 6379
```

## Updating Infrastructure

### Scale Kubernetes Nodes

```bash
# Increase node count
terraform apply -var="node_desired_size=5"

# Change instance type
terraform apply -var="node_instance_types=[\"m5.xlarge\"]"
```

### Upgrade Kubernetes Version

```bash
# Update in variables.tf or tfvars
terraform apply -var="kubernetes_version=1.29"

# Rolling upgrade of node groups
# Takes 20-30 minutes per node group
```

### Scale Database

```bash
# Increase storage
terraform apply -var="db_allocated_storage=500"

# Change instance class
terraform apply -var="db_instance_class=db.r5.4xlarge"

# Creates minor downtime (2-3 minutes)
```

## Troubleshooting

### Terraform Issues

```bash
# Validate configuration
terraform validate

# Check syntax
terraform fmt -check

# Get detailed output
terraform plan -var-file=terraform.tfvars -out=tfplan
terraform apply -auto-approve -var-file=terraform.tfvars -lock=false

# View state
terraform state list
terraform state show aws_eks_cluster.main
```

### Cluster Issues

```bash
# Check node status
kubectl describe nodes

# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# View cluster logs
aws eks describe-cluster --name randwater-production

# Get events
kubectl get events -A
```

### RDS Issues

```bash
# Check RDS status
aws rds describe-db-instances --db-instance-identifier randwater-production-db

# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Check parameter groups
aws rds describe-db-parameters --db-instance-identifier randwater-production-db
```

## Maintenance

### Regular Tasks

| Task | Frequency | Command |
|------|-----------|---------|
| Backup verification | Daily | `./scripts/verify_backup.sh` |
| Security updates | Weekly | `terraform plan` & review |
| Cost review | Monthly | AWS Cost Explorer |
| Capacity planning | Monthly | Review metrics & scale if needed |
| Disaster recovery test | Quarterly | `./scripts/dr_test.sh` |

### Backup & Restore

```bash
# Manual backup
aws rds create-db-snapshot \
  --db-instance-identifier randwater-production-db \
  --db-snapshot-identifier backup-$(date +%s)

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier randwater-production-db-restored \
  --db-snapshot-identifier backup-xxxxx

# Monitor restore
aws rds describe-db-instances --db-instance-identifier randwater-production-db-restored
```

## Destroying Infrastructure

### Complete Removal (Use with Caution!)

```bash
# Review what will be deleted
terraform plan -destroy

# Delete all resources
terraform destroy -var-file=terraform.tfvars

# Manually delete non-Terraform resources
aws s3 rm s3://randwater-backups --recursive  # Optional
aws s3 rb s3://randwater-terraform-state      # Optional
```

## Security Best Practices

1. **Secrets Management**
   ```bash
   # Use AWS Secrets Manager for sensitive data
   aws secretsmanager create-secret \
     --name randwater/db-password \
     --secret-string $(openssl rand -base64 32)
   
   # Reference in Terraform
   # data "aws_secretsmanager_secret_version" "db_password" {
   #   secret_id = "randwater/db-password"
   # }
   ```

2. **Network Security**
   - Enable VPC Flow Logs
   - Use Network ACLs
   - Restrict security group rules
   - Enable GuardDuty

3. **Access Control**
   - Use IAM roles for pod credentials
   - Enable RBAC in Kubernetes
   - Implement network policies
   - Use private subnets for databases

4. **Encryption**
   - Enable encryption at rest (S3, RDS, EBS)
   - Enable encryption in transit (TLS/SSL)
   - Rotate encryption keys regularly

## Cost Optimization

### Recommended Savings

1. **Use Reserved Instances**
   ```bash
   # AWS EC2 Reserved Instance Marketplace
   # Saves 40-60% on compute costs
   ```

2. **Spot Instances for Non-Critical Workloads**
   ```hcl
   # In node group configuration
   # savings of 70-90%
   ```

3. **Right-Size Resources**
   - Monitor actual usage
   - Use CloudWatch metrics
   - Adjust instance types accordingly

4. **S3 Lifecycle Policies**
   - Move old backups to Glacier
   - Delete expired data
   - Use Intelligent-Tiering

## Support and Documentation

- **Terraform Docs:** https://www.terraform.io/docs
- **AWS Terraform Provider:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **EKS Best Practices:** https://aws.github.io/aws-eks-best-practices/
- **Kubernetes Docs:** https://kubernetes.io/docs/

## Contributing

Before committing Terraform changes:

```bash
# Format code
terraform fmt -recursive

# Validate
terraform validate

# Plan and review
terraform plan -out=tfplan

# Check for security issues
tfsec .

# Generate documentation
terraform-docs markdown . > modules/vpc/README.md
```

---

**Last Updated:** January 2024
**Terraform Version:** >= 1.0
**AWS Provider Version:** >= 5.0
