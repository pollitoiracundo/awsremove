"""
Enhanced RDS service discovery with billing information.
"""

from typing import List
from .base import BaseAWSService
from ..core.models import AWSResource, ResourceState, BillingInfo


class RDSService(BaseAWSService):
    """Handles RDS instances, clusters, and related resources."""
    
    def get_service_name(self) -> str:
        return "rds"
    
    def discover_resources(self, region: str) -> List[AWSResource]:
        """Discover RDS instances, clusters, and snapshots."""
        resources = []
        resources.extend(self._discover_db_instances(region))
        resources.extend(self._discover_db_clusters(region))
        resources.extend(self._discover_db_snapshots(region))
        return resources
    
    def _discover_db_instances(self, region: str) -> List[AWSResource]:
        """Discover RDS database instances."""
        resources = []
        try:
            response = self._run_aws_command([
                'rds', 'describe-db-instances',
                '--region', region,
                '--output', 'json'
            ])
            
            for instance in response.get('DBInstances', []):
                db_id = instance.get('DBInstanceIdentifier', '')
                instance_class = instance.get('DBInstanceClass', 'db.t3.micro')
                engine = instance.get('Engine', 'unknown')
                status = instance.get('DBInstanceStatus', 'unknown')
                allocated_storage = instance.get('AllocatedStorage', 20)
                
                # Estimate RDS instance cost
                billing_info = self._estimate_rds_instance_cost(instance_class, engine, allocated_storage, status)
                
                resources.append(AWSResource(
                    service='rds',
                    resource_type='db_instance',
                    identifier=db_id,
                    name=db_id,
                    region=region,
                    dependencies=[instance.get('DBSubnetGroup', {}).get('VpcId')] if instance.get('DBSubnetGroup') else [],
                    metadata={
                        'engine': engine,
                        'engine_version': instance.get('EngineVersion', ''),
                        'instance_class': instance_class,
                        'allocated_storage': allocated_storage,
                        'storage_type': instance.get('StorageType', 'gp2'),
                        'multi_az': instance.get('MultiAZ', False),
                        'publicly_accessible': instance.get('PubliclyAccessible', False),
                        'endpoint': instance.get('Endpoint', {}).get('Address', ''),
                        'backup_retention_days': instance.get('BackupRetentionPeriod', 0)
                    },
                    state=self._map_rds_state(status),
                    billing_info=billing_info
                ))
        except Exception as e:
            print(f"Error discovering RDS instances in {region}: {e}")
        
        return resources
    
    def _discover_db_clusters(self, region: str) -> List[AWSResource]:
        """Discover RDS clusters (Aurora)."""
        resources = []
        try:
            response = self._run_aws_command([
                'rds', 'describe-db-clusters',
                '--region', region,
                '--output', 'json'
            ])
            
            for cluster in response.get('DBClusters', []):
                cluster_id = cluster.get('DBClusterIdentifier', '')
                engine = cluster.get('Engine', 'aurora')
                status = cluster.get('Status', 'unknown')
                
                # Aurora cluster pricing varies significantly
                billing_info = BillingInfo(
                    estimated_monthly_cost=73.0,  # Base Aurora cost estimate
                    pricing_model="aurora-capacity",
                    billing_unit="ACU-hours",
                    usage_metrics={
                        'engine': engine,
                        'cluster_members': len(cluster.get('DBClusterMembers', [])),
                        'multi_az': cluster.get('MultiAZ', False)
                    },
                    cost_categories=["database", "compute", "storage"]
                )
                
                resources.append(AWSResource(
                    service='rds',
                    resource_type='db_cluster',
                    identifier=cluster_id,
                    name=cluster_id,
                    region=region,
                    metadata={
                        'engine': engine,
                        'engine_version': cluster.get('EngineVersion', ''),
                        'cluster_members': cluster.get('DBClusterMembers', []),
                        'endpoint': cluster.get('Endpoint', ''),
                        'reader_endpoint': cluster.get('ReaderEndpoint', ''),
                        'backup_retention_days': cluster.get('BackupRetentionPeriod', 0)
                    },
                    state=self._map_rds_state(status),
                    billing_info=billing_info
                ))
        except Exception as e:
            print(f"Error discovering RDS clusters in {region}: {e}")
        
        return resources
    
    def _discover_db_snapshots(self, region: str) -> List[AWSResource]:
        """Discover RDS snapshots."""
        resources = []
        try:
            response = self._run_aws_command([
                'rds', 'describe-db-snapshots',
                '--region', region,
                '--snapshot-type', 'manual',
                '--max-items', '100',  # Limit to avoid too many results
                '--output', 'json'
            ])
            
            for snapshot in response.get('DBSnapshots', []):
                snapshot_id = snapshot.get('DBSnapshotIdentifier', '')
                allocated_storage = snapshot.get('AllocatedStorage', 0)
                status = snapshot.get('Status', 'unknown')
                
                # Snapshot storage cost
                monthly_cost = allocated_storage * 0.095  # $0.095 per GB-month
                
                billing_info = BillingInfo(
                    estimated_monthly_cost=monthly_cost,
                    pricing_model="storage",
                    billing_unit="GB-month",
                    usage_metrics={
                        'allocated_storage': allocated_storage,
                        'engine': snapshot.get('Engine', 'unknown')
                    },
                    cost_categories=["storage", "backup"]
                )
                
                resources.append(AWSResource(
                    service='rds',
                    resource_type='db_snapshot',
                    identifier=snapshot_id,
                    name=snapshot_id,
                    region=region,
                    dependencies=[snapshot.get('DBInstanceIdentifier')] if snapshot.get('DBInstanceIdentifier') else [],
                    metadata={
                        'source_db': snapshot.get('DBInstanceIdentifier', ''),
                        'engine': snapshot.get('Engine', ''),
                        'allocated_storage': allocated_storage,
                        'creation_time': snapshot.get('SnapshotCreateTime', ''),
                        'encrypted': snapshot.get('Encrypted', False)
                    },
                    state=self._map_rds_state(status),
                    billing_info=billing_info
                ))
        except Exception as e:
            print(f"Error discovering RDS snapshots in {region}: {e}")
        
        return resources
    
    def _estimate_rds_instance_cost(self, instance_class: str, engine: str, storage_gb: int, status: str) -> BillingInfo:
        """Estimate RDS instance cost based on class and configuration."""
        # RDS instance pricing (simplified estimates)
        instance_costs = {
            'db.t3.micro': 0.017, 'db.t3.small': 0.034, 'db.t3.medium': 0.068,
            'db.t3.large': 0.136, 'db.t3.xlarge': 0.272, 'db.t3.2xlarge': 0.544,
            'db.m5.large': 0.192, 'db.m5.xlarge': 0.384, 'db.m5.2xlarge': 0.768,
            'db.r5.large': 0.24, 'db.r5.xlarge': 0.48, 'db.r5.2xlarge': 0.96,
            'db.m6i.large': 0.184, 'db.m6i.xlarge': 0.368, 'db.m6i.2xlarge': 0.736
        }
        
        hourly_cost = instance_costs.get(instance_class, 0.05)
        
        # Engine multipliers
        engine_multipliers = {
            'postgres': 1.0, 'mysql': 1.0, 'mariadb': 1.0,
            'oracle-ee': 2.5, 'oracle-se2': 2.0, 'oracle-se1': 1.8,
            'sqlserver-ex': 1.0, 'sqlserver-web': 1.2, 'sqlserver-se': 1.8, 'sqlserver-ee': 2.2
        }
        
        hourly_cost *= engine_multipliers.get(engine, 1.0)
        
        # Calculate monthly cost
        if status.lower() in ['available', 'running']:
            compute_cost = hourly_cost * 24 * 30
        else:
            compute_cost = 0.0  # stopped instances don't incur compute costs
        
        # Storage cost (GP2 pricing)
        storage_cost = storage_gb * 0.115  # $0.115 per GB-month
        
        total_cost = compute_cost + storage_cost
        
        return BillingInfo(
            estimated_monthly_cost=total_cost,
            pricing_model="on-demand",
            billing_unit="hours + GB-month",
            usage_metrics={
                'instance_class': instance_class,
                'engine': engine,
                'hourly_rate': hourly_cost,
                'storage_gb': storage_gb,
                'compute_cost': compute_cost,
                'storage_cost': storage_cost
            },
            cost_categories=["database", "compute", "storage"]
        )
    
    def _map_rds_state(self, status: str) -> ResourceState:
        """Map RDS status to ResourceState."""
        status_mapping = {
            'available': ResourceState.AVAILABLE,
            'stopped': ResourceState.STOPPED,
            'starting': ResourceState.PENDING,
            'stopping': ResourceState.PENDING,
            'deleting': ResourceState.DELETING,
            'creating': ResourceState.PENDING,
            'backing-up': ResourceState.AVAILABLE,
            'modifying': ResourceState.AVAILABLE
        }
        return status_mapping.get(status.lower(), ResourceState.UNKNOWN)
    
    def delete_resource(self, resource: AWSResource) -> bool:
        """Delete an RDS resource."""
        try:
            if resource.resource_type == 'db_instance':
                return self._run_aws_command_simple([
                    'rds', 'delete-db-instance',
                    '--region', resource.region,
                    '--db-instance-identifier', resource.identifier,
                    '--skip-final-snapshot'
                ])
            elif resource.resource_type == 'db_cluster':
                return self._run_aws_command_simple([
                    'rds', 'delete-db-cluster',
                    '--region', resource.region,
                    '--db-cluster-identifier', resource.identifier,
                    '--skip-final-snapshot'
                ])
            elif resource.resource_type == 'db_snapshot':
                return self._run_aws_command_simple([
                    'rds', 'delete-db-snapshot',
                    '--region', resource.region,
                    '--db-snapshot-identifier', resource.identifier
                ])
            else:
                return False
        except Exception as e:
            print(f"Error deleting RDS resource {resource.name}: {e}")
            return False