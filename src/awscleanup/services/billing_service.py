"""
Billing inventory service for AWS cost analysis.
"""

import json
import os
import subprocess
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from .base import BaseAWSService
from ..core.models import AWSResource, BillingInfo, ResourceState
from ..core.exceptions import ResourceDiscoveryError


class BillingService:
    """Service for billing analysis and cost estimation."""
    
    def __init__(self, aws_cmd_base: List[str]):
        self.aws_cmd_base = aws_cmd_base
        self.pricing_cache = {}
    
    def get_cost_and_usage_data(self, days: int = 30) -> Dict:
        """Get Cost and Usage data for the specified period."""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            cmd = self.aws_cmd_base + [
                'ce', 'get-cost-and-usage',
                '--time-period', f'Start={start_date},End={end_date}',
                '--granularity', 'DAILY',
                '--metrics', 'BlendedCost',
                '--group-by', 'Type=DIMENSION,Key=SERVICE',
                '--output', 'json'
            ]
            
            result = self._run_aws_command(cmd)
            return result.get('ResultsByTime', [])
        except Exception as e:
            print(f"Warning: Could not fetch cost data: {e}")
            return []
    
    def get_billing_summary(self) -> Dict:
        """Get overall billing summary."""
        try:
            # Get current month costs
            now = datetime.now()
            start_of_month = now.replace(day=1).date()
            
            cmd = self.aws_cmd_base + [
                'ce', 'get-cost-and-usage',
                '--time-period', f'Start={start_of_month},End={now.date()}',
                '--granularity', 'MONTHLY',
                '--metrics', 'BlendedCost', 'UnblendedCost',
                '--output', 'json'
            ]
            
            result = self._run_aws_command(cmd)
            
            summary = {
                'current_month_cost': 0.0,
                'forecast_monthly_cost': 0.0,
                'top_services': [],
                'cost_trend': 'stable'
            }
            
            if result.get('ResultsByTime'):
                month_data = result['ResultsByTime'][0]
                total_cost = month_data.get('Total', {}).get('BlendedCost', {})
                summary['current_month_cost'] = float(total_cost.get('Amount', 0))
                
                # Estimate monthly cost based on daily average
                days_in_month = now.day
                if days_in_month > 0:
                    daily_avg = summary['current_month_cost'] / days_in_month
                    days_in_current_month = (now.replace(month=now.month+1, day=1) - timedelta(days=1)).day
                    summary['forecast_monthly_cost'] = daily_avg * days_in_current_month
            
            return summary
            
        except Exception as e:
            print(f"Warning: Could not fetch billing summary: {e}")
            return {'current_month_cost': 0.0, 'forecast_monthly_cost': 0.0, 'top_services': [], 'cost_trend': 'unknown'}
    
    def estimate_resource_cost(self, resource: AWSResource) -> Optional[BillingInfo]:
        """Estimate monthly cost for a resource."""
        try:
            if resource.service == 'ec2':
                return self._estimate_ec2_cost(resource)
            elif resource.service == 's3':
                return self._estimate_s3_cost(resource)
            elif resource.service == 'rds':
                return self._estimate_rds_cost(resource)
            elif resource.service == 'lambda':
                return self._estimate_lambda_cost(resource)
            else:
                # Generic estimation for unknown services
                return BillingInfo(
                    pricing_model="unknown",
                    billing_unit="unknown",
                    cost_categories=["unknown"]
                )
        except Exception:
            return None
    
    def _estimate_ec2_cost(self, resource: AWSResource) -> BillingInfo:
        """Estimate EC2 instance cost."""
        instance_type = resource.metadata.get('instance_type', 't3.micro')
        state = resource.metadata.get('state', {})
        
        # Basic cost estimates (simplified)
        cost_per_hour = {
            't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
            't3.large': 0.0832, 't3.xlarge': 0.1664, 't3.2xlarge': 0.3328,
            'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384,
            'c5.large': 0.085, 'c5.xlarge': 0.17, 'c5.2xlarge': 0.34,
            'r5.large': 0.126, 'r5.xlarge': 0.252, 'r5.2xlarge': 0.504
        }
        
        hourly_cost = cost_per_hour.get(instance_type, 0.05)  # default fallback
        
        # Calculate monthly cost (24 hours * 30 days)
        if resource.state == ResourceState.RUNNING:
            monthly_cost = hourly_cost * 24 * 30
        else:
            monthly_cost = 0.0  # stopped instances don't incur compute costs
        
        # Add EBS storage cost estimate
        ebs_cost = 0.10 * 30  # rough estimate for 30GB GP3 storage
        monthly_cost += ebs_cost
        
        return BillingInfo(
            estimated_monthly_cost=monthly_cost,
            pricing_model="on-demand",
            billing_unit="hours",
            usage_metrics={
                'instance_type': instance_type,
                'hourly_rate': hourly_cost,
                'storage_gb': 30
            },
            cost_categories=["compute", "storage"]
        )
    
    def _estimate_s3_cost(self, resource: AWSResource) -> BillingInfo:
        """Estimate S3 bucket cost."""
        object_count = resource.metadata.get('objects', 0)
        estimated_size_gb = object_count * 0.1 if object_count > 0 else 1  # rough estimate
        
        # S3 Standard pricing (simplified)
        storage_cost_per_gb = 0.023  # per month
        request_cost = max(object_count * 0.0004 / 1000, 0.01)  # PUT/GET requests
        
        monthly_cost = (estimated_size_gb * storage_cost_per_gb) + request_cost
        
        return BillingInfo(
            estimated_monthly_cost=monthly_cost,
            pricing_model="pay-per-use",
            billing_unit="GB-month",
            usage_metrics={
                'estimated_size_gb': estimated_size_gb,
                'object_count': object_count,
                'storage_class': 'STANDARD'
            },
            cost_categories=["storage", "requests"]
        )
    
    def _estimate_rds_cost(self, resource: AWSResource) -> BillingInfo:
        """Estimate RDS instance cost."""
        instance_class = resource.metadata.get('instance_class', 'db.t3.micro')
        
        # RDS cost estimates (simplified)
        cost_per_hour = {
            'db.t3.micro': 0.017, 'db.t3.small': 0.034, 'db.t3.medium': 0.068,
            'db.t3.large': 0.136, 'db.t3.xlarge': 0.272,
            'db.m5.large': 0.192, 'db.m5.xlarge': 0.384,
            'db.r5.large': 0.24, 'db.r5.xlarge': 0.48
        }
        
        hourly_cost = cost_per_hour.get(instance_class, 0.02)
        monthly_cost = hourly_cost * 24 * 30
        
        # Add storage cost
        storage_cost = 20 * 0.115  # 20GB GP2 storage estimate
        monthly_cost += storage_cost
        
        return BillingInfo(
            estimated_monthly_cost=monthly_cost,
            pricing_model="on-demand",
            billing_unit="hours",
            usage_metrics={
                'instance_class': instance_class,
                'hourly_rate': hourly_cost,
                'storage_gb': 20
            },
            cost_categories=["database", "storage"]
        )
    
    def _estimate_lambda_cost(self, resource: AWSResource) -> BillingInfo:
        """Estimate Lambda function cost."""
        runtime = resource.metadata.get('runtime', 'python3.9')
        
        # Lambda cost is based on requests and duration
        # Estimate: 1M requests per month, 100ms average duration
        estimated_requests = 1000000
        estimated_duration_ms = 100
        memory_mb = 128  # default
        
        # Lambda pricing (simplified)
        request_cost = estimated_requests * 0.0000002  # $0.20 per 1M requests
        gb_seconds = (memory_mb / 1024) * (estimated_duration_ms / 1000) * estimated_requests
        compute_cost = gb_seconds * 0.0000166667  # $0.0000166667 per GB-second
        
        monthly_cost = request_cost + compute_cost
        
        return BillingInfo(
            estimated_monthly_cost=monthly_cost,
            pricing_model="pay-per-use",
            billing_unit="requests + GB-seconds",
            usage_metrics={
                'estimated_requests': estimated_requests,
                'memory_mb': memory_mb,
                'runtime': runtime
            },
            cost_categories=["compute", "requests"]
        )
    
    def _run_aws_command(self, cmd: List[str]) -> Dict:
        """Run AWS command and return JSON result."""
        try:
            # Use current environment which should have AWS_PROFILE set
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=os.environ)
            return json.loads(result.stdout) if result.stdout.strip() else {}
        except subprocess.CalledProcessError as e:
            if e.returncode == 253:
                raise ResourceDiscoveryError(
                    f"AWS credentials not found for billing service. Please configure AWS credentials or specify a valid profile."
                )
            else:
                raise ResourceDiscoveryError(f"AWS command failed (exit code {e.returncode}): {e.stderr or e}")
        except json.JSONDecodeError as e:
            raise ResourceDiscoveryError(f"Failed to parse AWS response: {e}")
    
    def generate_billing_report(self, resources: List[AWSResource]) -> Dict:
        """Generate comprehensive billing report."""
        billing_resources = [r for r in resources if r.generates_cost]
        
        total_estimated_cost = sum(r.estimated_monthly_cost for r in billing_resources)
        
        # Group by service
        by_service = {}
        for resource in billing_resources:
            service = resource.service
            if service not in by_service:
                by_service[service] = {'count': 0, 'cost': 0.0, 'resources': []}
            by_service[service]['count'] += 1
            by_service[service]['cost'] += resource.estimated_monthly_cost
            by_service[service]['resources'].append(resource)
        
        # Group by cost categories
        by_category = {}
        for resource in billing_resources:
            if resource.billing_info:
                for category in resource.billing_info.cost_categories:
                    if category not in by_category:
                        by_category[category] = 0.0
                    by_category[category] += resource.estimated_monthly_cost
        
        # Top cost resources
        top_resources = sorted(
            billing_resources, 
            key=lambda r: r.estimated_monthly_cost, 
            reverse=True
        )[:10]
        
        return {
            'total_resources': len(resources),
            'billing_resources': len(billing_resources),
            'total_estimated_monthly_cost': total_estimated_cost,
            'by_service': by_service,
            'by_category': by_category,
            'top_cost_resources': top_resources,
            'cost_distribution': self._calculate_cost_distribution(billing_resources)
        }
    
    def _calculate_cost_distribution(self, resources: List[AWSResource]) -> Dict:
        """Calculate cost distribution statistics."""
        costs = [r.estimated_monthly_cost for r in resources if r.estimated_monthly_cost > 0]
        
        if not costs:
            return {'min': 0, 'max': 0, 'avg': 0, 'median': 0}
        
        costs.sort()
        n = len(costs)
        
        return {
            'min': costs[0],
            'max': costs[-1],
            'avg': sum(costs) / n,
            'median': costs[n // 2] if n % 2 == 1 else (costs[n // 2 - 1] + costs[n // 2]) / 2,
            'total_resources_with_cost': n
        }