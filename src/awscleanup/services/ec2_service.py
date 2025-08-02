"""
EC2 service discovery and management.
"""

from typing import List
from .base import BaseAWSService
from ..core.models import AWSResource, ResourceState, BillingInfo
from ..core.exceptions import ResourceDeletionError


class EC2Service(BaseAWSService):
    """Handles EC2 instances and related resources."""
    
    def get_service_name(self) -> str:
        return "ec2"
    
    def discover_resources(self, region: str) -> List[AWSResource]:
        """Discover EC2 instances and volumes."""
        resources = []
        resources.extend(self._discover_instances(region))
        resources.extend(self._discover_volumes(region))
        return resources
    
    def _discover_instances(self, region: str) -> List[AWSResource]:
        """Discover EC2 instances."""
        resources = []
        try:
            response = self._run_aws_command([
                'ec2', 'describe-instances',
                '--region', region,
                '--query', 'Reservations[].Instances[].[InstanceId,Tags,State,VpcId,SubnetId,InstanceType]',
                '--output', 'json'
            ])
            
            for instance_data in response:
                if len(instance_data) >= 3:
                    instance_id, tags, state, vpc_id, subnet_id, instance_type = instance_data[:6]
                    
                    # Skip terminated instances
                    if state and state.get('Name') == 'terminated':
                        continue
                    
                    name = self._get_name_from_tags(tags or [], instance_id)
                    dependencies = [vpc_id, subnet_id] if vpc_id and subnet_id else []
                    
                    # Estimate billing cost
                    billing_info = self._estimate_instance_cost(instance_type or 't3.micro', state)
                    
                    resources.append(AWSResource(
                        service='ec2',
                        resource_type='instance',
                        identifier=instance_id,
                        name=name,
                        region=region,
                        dependencies=dependencies,
                        metadata={
                            'state': state,
                            'vpc_id': vpc_id,
                            'subnet_id': subnet_id,
                            'instance_type': instance_type,
                            'tags': self._parse_tags(tags or [])
                        },
                        state=self._determine_state(state),
                        billing_info=billing_info
                    ))
        except Exception as e:
            print(f"Error discovering EC2 instances in {region}: {e}")
        
        return resources
    
    def _discover_volumes(self, region: str) -> List[AWSResource]:
        """Discover EBS volumes."""
        resources = []
        try:
            response = self._run_aws_command([
                'ec2', 'describe-volumes',
                '--region', region,
                '--query', 'Volumes[].[VolumeId,Tags,State,Attachments[0].InstanceId,Size,VolumeType]',
                '--output', 'json'
            ])
            
            for volume_data in response:
                if len(volume_data) >= 3:
                    volume_id, tags, state, instance_id, size, volume_type = volume_data[:6]
                    
                    name = self._get_name_from_tags(tags or [], volume_id)
                    dependencies = [instance_id] if instance_id else []
                    
                    # Estimate EBS volume cost
                    billing_info = self._estimate_volume_cost(volume_type or 'gp3', size or 8)
                    
                    resources.append(AWSResource(
                        service='ec2',
                        resource_type='volume',
                        identifier=volume_id,
                        name=name,
                        region=region,
                        dependencies=dependencies,
                        metadata={
                            'state': state,
                            'instance_id': instance_id,
                            'size': size,
                            'volume_type': volume_type,
                            'tags': self._parse_tags(tags or [])
                        },
                        state=self._determine_state(state),
                        billing_info=billing_info
                    ))
        except Exception as e:
            print(f"Error discovering EBS volumes in {region}: {e}")
        
        return resources
    
    def delete_resource(self, resource: AWSResource) -> bool:
        """Delete an EC2 resource."""
        try:
            if resource.resource_type == 'instance':
                return self._delete_instance(resource)
            elif resource.resource_type == 'volume':
                return self._delete_volume(resource)
            else:
                raise ResourceDeletionError(f"Unsupported EC2 resource type: {resource.resource_type}")
        except Exception as e:
            print(f"Error deleting {resource.name}: {e}")
            return False
    
    def _delete_instance(self, resource: AWSResource) -> bool:
        """Delete an EC2 instance."""
        return self._run_aws_command_simple([
            'ec2', 'terminate-instances',
            '--region', resource.region,
            '--instance-ids', resource.identifier
        ])
    
    def _delete_volume(self, resource: AWSResource) -> bool:
        """Delete an EBS volume."""
        return self._run_aws_command_simple([
            'ec2', 'delete-volume',
            '--region', resource.region,
            '--volume-id', resource.identifier
        ])
    
    def _estimate_instance_cost(self, instance_type: str, state: dict) -> BillingInfo:
        """Estimate EC2 instance monthly cost."""
        # EC2 pricing (simplified on-demand rates)
        instance_costs = {
            't3.nano': 0.0052, 't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
            't3.large': 0.0832, 't3.xlarge': 0.1664, 't3.2xlarge': 0.3328,
            't2.nano': 0.0058, 't2.micro': 0.0116, 't2.small': 0.023, 't2.medium': 0.046,
            'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384, 'm5.4xlarge': 0.768,
            'm6i.large': 0.0864, 'm6i.xlarge': 0.1728, 'm6i.2xlarge': 0.3456,
            'c5.large': 0.085, 'c5.xlarge': 0.17, 'c5.2xlarge': 0.34, 'c5.4xlarge': 0.68,
            'r5.large': 0.126, 'r5.xlarge': 0.252, 'r5.2xlarge': 0.504, 'r5.4xlarge': 1.008,
            'r6i.large': 0.1008, 'r6i.xlarge': 0.2016, 'r6i.2xlarge': 0.4032
        }
        
        hourly_cost = instance_costs.get(instance_type, 0.05)
        
        # Only charge for running instances
        if state and state.get('Name') == 'running':
            monthly_cost = hourly_cost * 24 * 30
        else:
            monthly_cost = 0.0
        
        return BillingInfo(
            estimated_monthly_cost=monthly_cost,
            pricing_model="on-demand" if monthly_cost > 0 else "stopped",
            billing_unit="hours",
            usage_metrics={
                'instance_type': instance_type,
                'hourly_rate': hourly_cost,
                'state': state.get('Name', 'unknown') if state else 'unknown'
            },
            cost_categories=["compute"]
        )
    
    def _estimate_volume_cost(self, volume_type: str, size_gb: int) -> BillingInfo:
        """Estimate EBS volume monthly cost."""
        # EBS pricing per GB-month
        volume_costs = {
            'gp3': 0.08,     # General Purpose SSD (gp3)
            'gp2': 0.10,     # General Purpose SSD (gp2) 
            'io1': 0.125,    # Provisioned IOPS SSD (io1)
            'io2': 0.125,    # Provisioned IOPS SSD (io2)
            'st1': 0.045,    # Throughput Optimized HDD
            'sc1': 0.025,    # Cold HDD
            'standard': 0.05  # Magnetic
        }
        
        cost_per_gb = volume_costs.get(volume_type, 0.08)
        monthly_cost = size_gb * cost_per_gb
        
        return BillingInfo(
            estimated_monthly_cost=monthly_cost,
            pricing_model="provisioned",
            billing_unit="GB-month",
            usage_metrics={
                'volume_type': volume_type,
                'size_gb': size_gb,
                'cost_per_gb': cost_per_gb
            },
            cost_categories=["storage"]
        )