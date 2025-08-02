"""
CloudWatch service discovery for monitoring resources that generate costs.
"""

from typing import List
from .base import BaseAWSService
from ..core.models import AWSResource, ResourceState, BillingInfo


class CloudWatchService(BaseAWSService):
    """Handles CloudWatch logs, metrics, and dashboards."""
    
    def get_service_name(self) -> str:
        return "cloudwatch"
    
    def discover_resources(self, region: str) -> List[AWSResource]:
        """Discover CloudWatch resources."""
        resources = []
        resources.extend(self._discover_log_groups(region))
        resources.extend(self._discover_dashboards(region))
        resources.extend(self._discover_alarms(region))
        return resources
    
    def _discover_log_groups(self, region: str) -> List[AWSResource]:
        """Discover CloudWatch Log Groups."""
        resources = []
        try:
            response = self._run_aws_command([
                'logs', 'describe-log-groups',
                '--region', region,
                '--max-items', '100',
                '--output', 'json'
            ])
            
            for log_group in response.get('logGroups', []):
                log_group_name = log_group.get('logGroupName', '')
                stored_bytes = log_group.get('storedBytes', 0)
                retention_days = log_group.get('retentionInDays')
                
                # CloudWatch Logs pricing
                storage_gb = stored_bytes / (1024**3)  # Convert to GB
                monthly_cost = storage_gb * 0.50  # $0.50 per GB ingested + storage
                
                billing_info = BillingInfo(
                    estimated_monthly_cost=monthly_cost,
                    pricing_model="pay-per-use",
                    billing_unit="GB-ingested + GB-stored",
                    usage_metrics={
                        'stored_bytes': stored_bytes,
                        'stored_gb': storage_gb,
                        'retention_days': retention_days
                    },
                    cost_categories=["monitoring", "storage"]
                )
                
                resources.append(AWSResource(
                    service='cloudwatch',
                    resource_type='log_group',
                    identifier=log_group_name,
                    name=log_group_name,
                    region=region,
                    metadata={
                        'stored_bytes': stored_bytes,
                        'retention_days': retention_days,
                        'creation_time': log_group.get('creationTime', 0),
                        'metric_filter_count': log_group.get('metricFilterCount', 0)
                    },
                    state=ResourceState.AVAILABLE,
                    billing_info=billing_info
                ))
        except Exception as e:
            print(f"Error discovering CloudWatch Log Groups in {region}: {e}")
        
        return resources
    
    def _discover_dashboards(self, region: str) -> List[AWSResource]:
        """Discover CloudWatch Dashboards."""
        resources = []
        try:
            response = self._run_aws_command([
                'cloudwatch', 'list-dashboards',
                '--region', region,
                '--output', 'json'
            ])
            
            for dashboard in response.get('DashboardEntries', []):
                dashboard_name = dashboard.get('DashboardName', '')
                
                # CloudWatch Dashboards pricing - $3 per dashboard per month
                billing_info = BillingInfo(
                    estimated_monthly_cost=3.0,
                    pricing_model="fixed",
                    billing_unit="dashboard-month",
                    usage_metrics={
                        'last_modified': dashboard.get('LastModified', '')
                    },
                    cost_categories=["monitoring", "visualization"]
                )
                
                resources.append(AWSResource(
                    service='cloudwatch',
                    resource_type='dashboard',
                    identifier=dashboard_name,
                    name=dashboard_name,
                    region=region,
                    metadata={
                        'last_modified': dashboard.get('LastModified', ''),
                        'size': dashboard.get('Size', 0)
                    },
                    state=ResourceState.AVAILABLE,
                    billing_info=billing_info
                ))
        except Exception as e:
            print(f"Error discovering CloudWatch Dashboards in {region}: {e}")
        
        return resources
    
    def _discover_alarms(self, region: str) -> List[AWSResource]:
        """Discover CloudWatch Alarms."""
        resources = []
        try:
            response = self._run_aws_command([
                'cloudwatch', 'describe-alarms',
                '--region', region,
                '--max-records', '100',
                '--output', 'json'
            ])
            
            for alarm in response.get('MetricAlarms', []):
                alarm_name = alarm.get('AlarmName', '')
                alarm_state = alarm.get('StateValue', 'UNKNOWN')
                
                # CloudWatch Alarms pricing - $0.10 per alarm per month
                billing_info = BillingInfo(
                    estimated_monthly_cost=0.10,
                    pricing_model="fixed",
                    billing_unit="alarm-month",
                    usage_metrics={
                        'state': alarm_state,
                        'metric_name': alarm.get('MetricName', ''),
                        'namespace': alarm.get('Namespace', '')
                    },
                    cost_categories=["monitoring", "alerting"]
                )
                
                resources.append(AWSResource(
                    service='cloudwatch',
                    resource_type='alarm',
                    identifier=alarm_name,
                    name=alarm_name,
                    region=region,
                    metadata={
                        'state': alarm_state,
                        'metric_name': alarm.get('MetricName', ''),
                        'namespace': alarm.get('Namespace', ''),
                        'comparison_operator': alarm.get('ComparisonOperator', ''),
                        'threshold': alarm.get('Threshold', 0),
                        'actions_enabled': alarm.get('ActionsEnabled', False)
                    },
                    state=ResourceState.AVAILABLE,
                    billing_info=billing_info
                ))
        except Exception as e:
            print(f"Error discovering CloudWatch Alarms in {region}: {e}")
        
        return resources
    
    def delete_resource(self, resource: AWSResource) -> bool:
        """Delete a CloudWatch resource."""
        try:
            if resource.resource_type == 'log_group':
                return self._run_aws_command_simple([
                    'logs', 'delete-log-group',
                    '--region', resource.region,
                    '--log-group-name', resource.identifier
                ])
            elif resource.resource_type == 'dashboard':
                return self._run_aws_command_simple([
                    'cloudwatch', 'delete-dashboards',
                    '--region', resource.region,
                    '--dashboard-names', resource.identifier
                ])
            elif resource.resource_type == 'alarm':
                return self._run_aws_command_simple([
                    'cloudwatch', 'delete-alarms',
                    '--region', resource.region,
                    '--alarm-names', resource.identifier
                ])
            else:
                return False
        except Exception as e:
            print(f"Error deleting CloudWatch resource {resource.name}: {e}")
            return False