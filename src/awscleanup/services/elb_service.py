"""
Elastic Load Balancer service discovery and management.
"""

from typing import List
from .base import BaseAWSService
from ..core.models import AWSResource, ResourceState, BillingInfo


class ELBService(BaseAWSService):
    """Handles Classic Load Balancers, ALBs, and NLBs."""
    
    def get_service_name(self) -> str:
        return "elb"
    
    def discover_resources(self, region: str) -> List[AWSResource]:
        """Discover all types of load balancers."""
        resources = []
        resources.extend(self._discover_classic_load_balancers(region))
        resources.extend(self._discover_application_load_balancers(region))
        resources.extend(self._discover_network_load_balancers(region))
        return resources
    
    def _discover_classic_load_balancers(self, region: str) -> List[AWSResource]:
        """Discover Classic Load Balancers (ELB v1)."""
        resources = []
        try:
            response = self._run_aws_command([
                'elb', 'describe-load-balancers',
                '--region', region,
                '--output', 'json'
            ])
            
            for lb in response.get('LoadBalancerDescriptions', []):
                lb_name = lb.get('LoadBalancerName', '')
                vpc_id = lb.get('VPCId')
                scheme = lb.get('Scheme', 'internet-facing')
                
                # Estimate cost for Classic Load Balancer
                billing_info = BillingInfo(
                    estimated_monthly_cost=18.0,  # ~$0.025/hour * 24 * 30
                    pricing_model="hourly",
                    billing_unit="hours",
                    usage_metrics={
                        'scheme': scheme,
                        'instances': len(lb.get('Instances', [])),
                        'type': 'classic'
                    },
                    cost_categories=["load-balancing", "network"]
                )
                
                resources.append(AWSResource(
                    service='elb',
                    resource_type='classic-load-balancer',
                    identifier=lb_name,
                    name=lb_name,
                    region=region,
                    dependencies=[vpc_id] if vpc_id else [],
                    metadata={
                        'scheme': scheme,
                        'dns_name': lb.get('DNSName', ''),
                        'instances': lb.get('Instances', []),
                        'availability_zones': lb.get('AvailabilityZones', [])
                    },
                    state=ResourceState.AVAILABLE,
                    billing_info=billing_info
                ))
        except Exception as e:
            print(f"Error discovering Classic Load Balancers in {region}: {e}")
        
        return resources
    
    def _discover_application_load_balancers(self, region: str) -> List[AWSResource]:
        """Discover Application Load Balancers (ALB)."""
        resources = []
        try:
            response = self._run_aws_command([
                'elbv2', 'describe-load-balancers',
                '--region', region,
                '--query', 'LoadBalancers[?Type==`application`]',
                '--output', 'json'
            ])
            
            for lb in response:
                lb_name = lb.get('LoadBalancerName', '')
                lb_arn = lb.get('LoadBalancerArn', '')
                vpc_id = lb.get('VpcId')
                scheme = lb.get('Scheme', 'internet-facing')
                
                # ALB pricing includes Load Balancer Capacity Units (LCUs)
                billing_info = BillingInfo(
                    estimated_monthly_cost=22.5,  # Base $16.2/month + LCU costs
                    pricing_model="hourly + LCU",
                    billing_unit="hours + LCUs",
                    usage_metrics={
                        'scheme': scheme,
                        'type': 'application',
                        'ip_address_type': lb.get('IpAddressType', 'ipv4')
                    },
                    cost_categories=["load-balancing", "network"]
                )
                
                resources.append(AWSResource(
                    service='elb',
                    resource_type='application-load-balancer',
                    identifier=lb_arn,
                    name=lb_name,
                    region=region,
                    dependencies=[vpc_id] if vpc_id else [],
                    metadata={
                        'scheme': scheme,
                        'dns_name': lb.get('DNSName', ''),
                        'state': lb.get('State', {}).get('Code', 'unknown'),
                        'type': lb.get('Type', 'application'),
                        'availability_zones': lb.get('AvailabilityZones', [])
                    },
                    state=self._determine_state(lb.get('State', {}).get('Code')),
                    billing_info=billing_info
                ))
        except Exception as e:
            print(f"Error discovering Application Load Balancers in {region}: {e}")
        
        return resources
    
    def _discover_network_load_balancers(self, region: str) -> List[AWSResource]:
        """Discover Network Load Balancers (NLB)."""
        resources = []
        try:
            response = self._run_aws_command([
                'elbv2', 'describe-load-balancers',
                '--region', region,
                '--query', 'LoadBalancers[?Type==`network`]',
                '--output', 'json'
            ])
            
            for lb in response:
                lb_name = lb.get('LoadBalancerName', '')
                lb_arn = lb.get('LoadBalancerArn', '')
                vpc_id = lb.get('VpcId')
                scheme = lb.get('Scheme', 'internet-facing')
                
                # NLB pricing
                billing_info = BillingInfo(
                    estimated_monthly_cost=16.2,  # $0.0225/hour * 24 * 30
                    pricing_model="hourly + NLCU",
                    billing_unit="hours + NLCUs",
                    usage_metrics={
                        'scheme': scheme,
                        'type': 'network',
                        'ip_address_type': lb.get('IpAddressType', 'ipv4')
                    },
                    cost_categories=["load-balancing", "network"]
                )
                
                resources.append(AWSResource(
                    service='elb',
                    resource_type='network-load-balancer',
                    identifier=lb_arn,
                    name=lb_name,
                    region=region,
                    dependencies=[vpc_id] if vpc_id else [],
                    metadata={
                        'scheme': scheme,
                        'dns_name': lb.get('DNSName', ''),
                        'state': lb.get('State', {}).get('Code', 'unknown'),
                        'type': lb.get('Type', 'network'),
                        'availability_zones': lb.get('AvailabilityZones', [])
                    },
                    state=self._determine_state(lb.get('State', {}).get('Code')),
                    billing_info=billing_info
                ))
        except Exception as e:
            print(f"Error discovering Network Load Balancers in {region}: {e}")
        
        return resources
    
    def delete_resource(self, resource: AWSResource) -> bool:
        """Delete a load balancer."""
        try:
            if resource.resource_type == 'classic-load-balancer':
                return self._run_aws_command_simple([
                    'elb', 'delete-load-balancer',
                    '--region', resource.region,
                    '--load-balancer-name', resource.name
                ])
            else:  # ALB or NLB
                return self._run_aws_command_simple([
                    'elbv2', 'delete-load-balancer',
                    '--region', resource.region,
                    '--load-balancer-arn', resource.identifier
                ])
        except Exception as e:
            print(f"Error deleting load balancer {resource.name}: {e}")
            return False