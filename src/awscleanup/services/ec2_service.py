"""
EC2 service discovery and management.
"""

from typing import List
from .base import BaseAWSService
from ..core.models import AWSResource, ResourceState
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
                '--query', 'Reservations[].Instances[].[InstanceId,Tags,State,VpcId,SubnetId]',
                '--output', 'json'
            ])
            
            for instance_data in response:
                if len(instance_data) >= 3:
                    instance_id, tags, state, vpc_id, subnet_id = instance_data[:5]
                    
                    # Skip terminated instances
                    if state and state.get('Name') == 'terminated':
                        continue
                    
                    name = self._get_name_from_tags(tags or [], instance_id)
                    dependencies = [vpc_id, subnet_id] if vpc_id and subnet_id else []
                    
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
                            'tags': self._parse_tags(tags or [])
                        },
                        state=self._determine_state(state)
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
                        state=self._determine_state(state)
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