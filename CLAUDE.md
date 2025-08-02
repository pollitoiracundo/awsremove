# AWS Resource Cleanup Tool - CLAUDE.md

This file contains information for Claude Code about the AWS Resource Cleanup Tool project structure, features, and usage patterns.

## Project Overview

An interactive 80s-style terminal application for discovering, analyzing, and safely cleaning up AWS resources with comprehensive billing analysis. Built with a modular architecture using Python 3.6+ and AWS CLI.

## Project Structure

```
awsremove/
├── src/awscleanup/                 # Main package
│   ├── core/                       # Core business logic
│   │   ├── models.py              # Data models (AWSResource, BillingInfo, etc.)
│   │   ├── exceptions.py          # Custom exception hierarchy
│   │   ├── profile_manager.py     # AWS profile and account management
│   │   ├── discovery.py           # Resource discovery coordination
│   │   └── application.py         # Main application controller
│   ├── services/                   # AWS service handlers
│   │   ├── base.py                # Abstract base service class
│   │   ├── ec2_service.py         # EC2 instances and volumes
│   │   ├── s3_service.py          # S3 buckets
│   │   ├── rds_service.py         # RDS instances, clusters, snapshots
│   │   ├── elb_service.py         # Load balancers (Classic, ALB, NLB)
│   │   ├── cloudwatch_service.py  # CloudWatch resources
│   │   ├── billing_service.py     # Cost estimation and billing analysis
│   │   └── service_factory.py     # Service creation factory
│   ├── ui/                         # 80s-style terminal interface
│   │   ├── colors.py              # Color schemes (Neon, Matrix, Classic)
│   │   ├── terminal.py            # Terminal control and effects
│   │   └── retro_ui.py            # Main UI implementation
│   ├── config/                     # Configuration management
│   │   └── settings.py            # Application settings
│   └── utils/                      # Utility functions
│       └── cli.py                 # Command line interface utilities
├── aws_cleanup_retro.py           # Main entry point
├── demo_effects.py                # Visual effects demo
├── requirements.txt               # Dependencies (none!)
├── README_RETRO.md               # User documentation
└── CLAUDE.md                     # This file
```

## Key Features

### 🎮 Retro Terminal Interface
- 80s-style ASCII art and neon color schemes
- Arrow key navigation with smooth animations
- Matrix rain effects and typewriter text
- Three color schemes: Neon (default), Matrix, Classic

### 💰 Comprehensive Billing Analysis
- Real-time cost estimation for all supported resources
- Visual cost breakdowns by service and category
- Monthly cost projections and top cost resource identification
- JSON export functionality for billing reports

### 🔐 Enterprise Security
- Multi-AWS profile support with safety verification
- Environment detection (Production/Staging/Development)
- Protected and safe account lists
- Service blacklisting for critical services

### ⚡ Supported AWS Services
- **EC2**: Instances, EBS volumes with cost estimation
- **S3**: Buckets with storage and request cost analysis
- **RDS**: Instances, clusters, snapshots with pricing models
- **Lambda**: Functions with request and compute cost estimates
- **ELB**: Classic, Application, and Network Load Balancers
- **CloudWatch**: Log groups, dashboards, alarms

## Design Patterns Used

### Factory Pattern
- `ServiceFactory` creates AWS service handlers
- Easily extensible for new AWS services
- Centralized service registration

### Strategy Pattern
- `ColorScheme` classes for different UI themes
- Configurable pricing models for different resource types
- Pluggable authentication strategies

### Observer Pattern
- UI state updates based on resource selection
- Real-time billing calculations during discovery

### MVC Architecture
- `core/models.py`: Data models and business logic
- `ui/retro_ui.py`: View layer with 80s styling
- `core/application.py`: Controller coordinating interactions

## Configuration Files

The application creates and manages several configuration files in `~/.aws/`:

- `cleanup_safety.conf`: Safe and protected account lists
- `cleanup_services.conf`: Service enable/disable settings
- `cleanup_ui.conf`: UI preferences and color schemes

## Common Development Tasks

### Adding a New AWS Service

1. Create service class in `src/awscleanup/services/`:
```python
class NewService(BaseAWSService):
    def get_service_name(self) -> str:
        return "new_service"
    
    def discover_resources(self, region: str) -> List[AWSResource]:
        # Implementation
        pass
    
    def delete_resource(self, resource: AWSResource) -> bool:
        # Implementation
        pass
```

2. Register in `service_factory.py`:
```python
_services = {
    'new_service': NewService,
    # ... existing services
}
```

3. Add to default configuration in `settings.py`:
```python
'new_service': ServiceConfig('new_service', enabled=True, protected=False)
```

### Adding Billing Support

1. Implement cost estimation in service class:
```python
def _estimate_cost(self, resource_config) -> BillingInfo:
    return BillingInfo(
        estimated_monthly_cost=calculated_cost,
        pricing_model="on-demand",
        billing_unit="hours",
        usage_metrics=metrics_dict,
        cost_categories=["compute", "storage"]
    )
```

2. Apply billing info during resource creation:
```python
resource.billing_info = self._estimate_cost(resource_data)
```

### Adding New Color Schemes

1. Create color scheme class in `ui/colors.py`:
```python
class CustomScheme(ColorScheme):
    def __init__(self):
        super().__init__("custom")
    
    @property
    def header(self) -> str:
        return Color.BRIGHT_BLUE + Color.BOLD
```

2. Register in `get_color_scheme()` function

### Testing Commands

```bash
# Basic functionality test
python3 aws_cleanup_retro.py --help

# Visual effects demo
python3 demo_effects.py

# Matrix color scheme
python3 aws_cleanup_retro.py --color-scheme matrix --no-splash

# Specific profile
python3 aws_cleanup_retro.py --profile dev-account
```

## Safety Mechanisms

### Account Protection
- Protected accounts list prevents accidental use
- Environment detection with visual warnings
- Profile verification before operations

### Resource Protection
- Service blacklisting for critical services (IAM, Route53, CloudFormation)
- Dependency analysis and safe deletion ordering
- Multiple confirmation prompts

### Billing Protection
- Cost visibility before any deletions
- High-cost resource warnings
- Export capabilities for audit trails

## Error Handling

Custom exception hierarchy in `core/exceptions.py`:
- `AWSCleanupError`: Base exception
- `ProfileError`: AWS profile issues
- `AccountSecurityError`: Security violations
- `ResourceDiscoveryError`: Discovery failures
- `ServiceNotSupportedError`: Unsupported services

## Performance Considerations

- Lazy loading of AWS services
- Caching of pricing information
- Efficient dependency graph calculation
- Pagination for large resource lists

## Future Enhancements

### Planned Services
- ECS/Fargate containers
- API Gateway endpoints
- CloudFront distributions
- SNS/SQS messaging
- DynamoDB tables

### UI Improvements
- Sound effects for retro experience
- More visual effects and animations
- Customizable keyboard shortcuts
- Multi-pane views

### Analytics Features
- Cost trend analysis
- Resource usage patterns
- Optimization recommendations
- Budget tracking integration

## Debugging Tips

### Common Issues
1. **AWS CLI not found**: Ensure AWS CLI is installed and in PATH
2. **Profile errors**: Check `~/.aws/credentials` and `~/.aws/config`
3. **Permission errors**: Verify IAM permissions for discovery operations
4. **Terminal rendering**: Ensure terminal supports ANSI colors and Unicode

### Debug Mode
Set environment variable for verbose output:
```bash
export AWS_CLEANUP_DEBUG=1
python3 aws_cleanup_retro.py
```

### Log Files
Application logs errors to console. For persistent logging, redirect output:
```bash
python3 aws_cleanup_retro.py 2>&1 | tee cleanup.log
```

## Dependencies

- **Python 3.6+**: Core runtime
- **AWS CLI**: Must be installed and configured
- **Terminal**: ANSI color support recommended
- **No external Python packages**: Uses only standard library

## License and Attribution

This tool is built for educational and operational purposes. Always test in non-production environments first and ensure proper backup procedures are in place before performing deletions.

---

*This project demonstrates modern Python architecture patterns while providing practical AWS resource management capabilities with a fun retro aesthetic.*