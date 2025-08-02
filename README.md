# AWS Resource Cleanup Tool

An interactive Python program that discovers AWS resources across your account and allows safe, dependency-aware cleanup with comprehensive profile and account management.

## Features

- 🔍 **Auto-discovery**: Scans all AWS regions for resources across multiple services
- 🔗 **Dependency tracking**: Shows resource dependencies and dependents
- 🛡️ **Safe deletion**: Multiple confirmation prompts and dry-run mode
- 📋 **Interactive menu**: Easy-to-use command-line interface
- ⚡ **Multi-service support**: EC2, S3, RDS, Lambda, and more
- 🔐 **Profile management**: Support for multiple AWS profiles with safety checks
- 🚨 **Environment protection**: Automatic detection and protection of production environments
- ✅ **Account whitelisting**: Manage safe and protected account lists
- 🔄 **Profile switching**: Switch between AWS profiles without restarting

## Prerequisites

1. **AWS CLI**: Install and configure AWS CLI
   ```bash
   # Install AWS CLI
   pip install awscli
   
   # Configure credentials
   aws configure
   ```

2. **Python 3.6+**: No additional dependencies required

## Usage

### Basic Usage
```bash
python3 aws_cleanup.py
```

### With Specific Profile
```bash
python3 aws_cleanup.py --profile my-dev-profile
```

### Dry Run Mode
```bash
python3 aws_cleanup.py --dry-run
```

### Specific Regions
```bash
python3 aws_cleanup.py --regions us-east-1 us-west-2 --profile production
```

## Interactive Menu

The tool provides an interactive menu with these options:

1. **List all resources** - View discovered resources across all services
2. **Select resource for deletion** - Choose resources to delete
3. **Show selected resources** - Review your deletion selection
4. **Show dependencies** - View resource dependencies and dependents
5. **Delete selected resources (DRY RUN)** - Preview deletion without executing
6. **Delete selected resources (REAL)** - Execute actual deletion
7. **Clear selections** - Reset all selections
8. **Switch AWS profile** - Change to a different AWS profile/account
9. **Manage account safety settings** - Configure safe and protected accounts
0. **Exit** - Quit the program

## Supported Services

### Currently Supported
- **EC2**: Instances, EBS volumes
- **S3**: Buckets
- **RDS**: Database instances
- **Lambda**: Functions

### Dependency Tracking
The tool automatically detects dependencies between resources:
- EC2 instances → VPCs, subnets
- EBS volumes → EC2 instances
- RDS instances → VPCs
- Lambda functions → VPCs

## Safety Features

### Profile and Account Protection
- **Profile selection**: Choose from available AWS profiles at startup
- **Account verification**: Displays account ID, user, and environment type
- **Environment detection**: Automatically identifies production/staging/development environments
- **Protected accounts**: Maintain a list of accounts that cannot be used with the tool
- **Safe accounts**: Whitelist trusted accounts for easier access
- **Profile switching**: Change profiles with safety re-verification

### Multiple Confirmations
- Individual resource selection with dependency warnings
- Final confirmation requiring typing "DELETE"
- Additional "yes/no" confirmation
- Special confirmation for production environments

### Dry Run Mode
- Preview all operations without executing
- See deletion order and dependencies
- Test the tool safely

### Dependency-Aware Deletion
- Automatically orders deletions to respect dependencies
- Deletes dependents before dependencies
- Warns about resources that depend on selected items

### Account Safety Configuration
The tool maintains a configuration file at `~/.aws/cleanup_safety.conf`:
- **Safe accounts**: Accounts marked as safe for cleanup operations
- **Protected accounts**: Accounts that are completely blocked from use
- Configuration persists between sessions

## Example Session

```
🚀 AWS Resource Cleanup Tool Starting...

🔐 Available AWS Profiles:
 1. default              (Account: 123456789012) ✅ SAFE
 2. staging               (Account: 234567890123) 🟡 STAGING
 3. production            (Account: 345678901234) 🔴 PRODUCTION

Select profile (1-3): 1

🔍 Account Verification:
   Profile: default
   Account ID: 123456789012
   User: arn:aws:iam::123456789012:user/dev-user
   Region: us-east-1
   Environment: ✅ SAFE

✅ Connected to AWS account 123456789012 using profile 'default'

🔍 Discovering AWS resources...
Scanning 16 regions...
  📦 Discovering S3 buckets...
  🌍 Scanning region: us-east-1
    🖥️  EC2 resources...
    🗄️  RDS resources...
    ⚡ Lambda functions...

✅ Found 23 resources across 16 regions

============================================================
AWS Resource Cleanup Tool
============================================================
Current Profile: default
Account: 123456789012 ✅ SAFE
Region: us-east-1
------------------------------------------------------------
1. List all resources
2. Select resource for deletion
3. Show selected resources
4. Show dependencies for resource
5. Delete selected resources (DRY RUN)
6. Delete selected resources (REAL)
7. Clear selections
8. Switch AWS profile
9. Manage account safety settings
0. Exit

Enter your choice (0-9): 1

#   Service    Type            Name                           Region          Status
------------------------------------------------------------------------------------------
1   ec2        instance        web-server-1                   us-east-1       
2   ec2        volume          vol-12345                      us-east-1       
3   s3         bucket          my-app-bucket                  global          
4   rds        db_instance     test-db                        us-east-1       
```

## Warning

⚠️ **This tool permanently deletes AWS resources!**

- Always test with dry-run mode first
- Review dependencies carefully
- Have backups of important data
- Use appropriate IAM permissions

## IAM Permissions

Ensure your AWS credentials have necessary permissions for:
- Listing resources (describe/list operations)
- Deleting resources (delete/terminate operations)
- Reading resource metadata

## Limitations

- Some AWS services not yet supported
- Complex dependency chains may need manual resolution
- Global services like IAM, Route53 not included
- No cost estimation before deletion

## Contributing

To add support for additional AWS services:
1. Add discovery method in `AWSResourceDiscovery` class
2. Add deletion logic in `_delete_resource` method
3. Update dependency mapping as needed