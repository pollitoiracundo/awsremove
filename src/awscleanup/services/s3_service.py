"""
S3 service discovery and management.
"""

from typing import List
from .base import BaseAWSService
from ..core.models import AWSResource, ResourceState, BillingInfo


class S3Service(BaseAWSService):
    """Handles S3 buckets."""
    
    def get_service_name(self) -> str:
        return "s3"
    
    def is_global_service(self) -> bool:
        return True
    
    def discover_resources(self, region: str = None) -> List[AWSResource]:
        """Discover S3 buckets (global service)."""
        resources = []
        try:
            response = self._run_aws_command([
                's3api', 'list-buckets',
                '--query', 'Buckets[].[Name,CreationDate]',
                '--output', 'json'
            ])
            
            for bucket_data in response:
                bucket_name, creation_date = bucket_data
                
                # Get bucket location
                try:
                    location_response = self._run_aws_command([
                        's3api', 'get-bucket-location',
                        '--bucket', bucket_name,
                        '--output', 'json'
                    ])
                    bucket_region = location_response.get('LocationConstraint') or 'us-east-1'
                except Exception:
                    bucket_region = 'unknown'
                
                # Get bucket size and object count (optional)
                bucket_info = self._get_bucket_info(bucket_name)
                
                # Estimate S3 costs
                billing_info = self._estimate_s3_cost(bucket_info)
                
                resources.append(AWSResource(
                    service='s3',
                    resource_type='bucket',
                    identifier=bucket_name,
                    name=bucket_name,
                    region=bucket_region,
                    metadata={
                        'creation_date': creation_date,
                        'region': bucket_region,
                        **bucket_info
                    },
                    state=ResourceState.AVAILABLE,
                    billing_info=billing_info
                ))
        except Exception as e:
            print(f"Error discovering S3 buckets: {e}")
        
        return resources
    
    def _get_bucket_info(self, bucket_name: str) -> dict:
        """Get additional bucket information."""
        info = {'objects': 0, 'size': 0}
        try:
            # Try to get object count and size
            response = self._run_aws_command([
                's3api', 'list-objects-v2',
                '--bucket', bucket_name,
                '--query', 'length(Contents[])',
                '--output', 'json'
            ])
            info['objects'] = response or 0
        except Exception:
            pass  # Non-critical information
        
        return info
    
    def delete_resource(self, resource: AWSResource) -> bool:
        """Delete an S3 bucket."""
        try:
            # First, try to empty the bucket
            empty_success = self._run_aws_command_simple([
                's3', 'rm', f's3://{resource.identifier}',
                '--recursive'
            ])
            
            # Then delete the bucket
            if empty_success:
                return self._run_aws_command_simple([
                    's3api', 'delete-bucket',
                    '--bucket', resource.identifier
                ])
            return False
            
        except Exception as e:
            print(f"Error deleting S3 bucket {resource.name}: {e}")
            return False
    
    def _estimate_s3_cost(self, bucket_info: dict) -> BillingInfo:
        """Estimate S3 bucket monthly cost."""
        object_count = bucket_info.get('objects', 0)
        estimated_size_gb = max(object_count * 0.1, 1.0) if object_count > 0 else 1.0
        
        # S3 Standard pricing (simplified)
        storage_cost = estimated_size_gb * 0.023  # $0.023 per GB-month
        request_cost = max(object_count * 0.0004 / 1000, 0.001)  # PUT/GET requests
        
        monthly_cost = storage_cost + request_cost
        
        return BillingInfo(
            estimated_monthly_cost=monthly_cost,
            pricing_model="pay-per-use",
            billing_unit="GB-month + requests",
            usage_metrics={
                'estimated_size_gb': estimated_size_gb,
                'object_count': object_count,
                'storage_class': 'STANDARD',
                'storage_cost': storage_cost,
                'request_cost': request_cost
            },
            cost_categories=["storage", "requests"]
        )