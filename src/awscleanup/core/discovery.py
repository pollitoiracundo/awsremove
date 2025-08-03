"""
Resource discovery coordination and dependency mapping.
"""

import subprocess
import json
import os
from typing import List, Dict, Set
from collections import defaultdict
from .models import AWSResource, CleanupSession
from .profile_manager import AWSProfileManager
from ..services.service_factory import ServiceFactory
from ..config.settings import Settings
from .exceptions import ResourceDiscoveryError


class ResourceDiscovery:
    """Coordinates resource discovery across AWS services."""
    
    def __init__(self, profile_manager: AWSProfileManager, settings: Settings):
        self.profile_manager = profile_manager
        self.settings = settings
        # Use the already configured aws_cmd_base from profile manager
        self.aws_cmd_base = profile_manager.aws_cmd_base
        self.dependency_map = defaultdict(set)
    
    def get_available_regions(self) -> List[str]:
        """Get all available AWS regions."""
        try:
            # Get configured default region first
            configured_region = self.profile_manager.get_configured_region(self.profile_manager.current_profile)
            default_region = configured_region or 'us-east-1'
            
            # Use the default region for the describe-regions call
            cmd = self.aws_cmd_base + ['ec2', 'describe-regions', '--region', default_region, 
                                     '--query', 'Regions[].RegionName', '--output', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=os.environ)
            return json.loads(result.stdout)
        except Exception as e:
            print(f"Error getting regions: {e}")
            # Fallback to configured region or us-east-1
            configured_region = self.profile_manager.get_configured_region(self.profile_manager.current_profile)
            return [configured_region or 'us-east-1']
    
    def discover_all_resources(self, session: CleanupSession) -> List[AWSResource]:
        """Discover all AWS resources across enabled services."""
        print("🔍 Discovering AWS resources...")
        all_resources = []
        
        # Get enabled services
        enabled_services = self.settings.get_enabled_services()
        if not enabled_services:
            print("⚠️  No services are enabled for discovery!")
            return []
        
        print(f"📋 Enabled services: {', '.join(enabled_services)}")
        
        # Get regions
        regions = self.get_available_regions()
        print(f"🌍 Scanning {len(regions)} regions...")
        
        # Discover resources for each enabled service
        for service_name in enabled_services:
            try:
                service = ServiceFactory.create_service(service_name, self.aws_cmd_base)
                
                if service.is_global_service():
                    print(f"  🌐 {service_name.upper()}: Global service...")
                    resources = service.discover_resources()
                    all_resources.extend(resources)
                else:
                    print(f"  📍 {service_name.upper()}: Regional service...")
                    for region in regions:
                        print(f"    🔍 {region}")
                        resources = service.discover_resources(region)
                        all_resources.extend(resources)
                        
            except Exception as e:
                print(f"❌ Error discovering {service_name} resources: {e}")
        
        # Build dependency relationships
        self._build_dependency_map(all_resources)
        
        # Update session
        session.resources = all_resources
        
        print(f"✅ Found {len(all_resources)} resources")
        return all_resources
    
    def _build_dependency_map(self, resources: List[AWSResource]) -> None:
        """Build bidirectional dependency relationships."""
        # Create resource lookup map
        resource_map = {r.identifier: r for r in resources}
        
        # Clear existing dependents
        for resource in resources:
            resource.dependents.clear()
        
        # Build dependency relationships
        for resource in resources:
            for dep_id in resource.dependencies:
                if dep_id in resource_map:
                    resource_map[dep_id].dependents.append(resource.identifier)
    
    def get_deletion_order(self, selected_resources: List[AWSResource]) -> List[AWSResource]:
        """Calculate safe deletion order respecting dependencies."""
        deletion_order = []
        remaining = selected_resources.copy()
        remaining_ids = {r.identifier for r in remaining}
        
        while remaining:
            # Find resources with no dependents in the remaining set
            can_delete = []
            for resource in remaining:
                has_dependents_in_remaining = any(
                    dep_id in remaining_ids for dep_id in resource.dependents
                )
                if not has_dependents_in_remaining:
                    can_delete.append(resource)
            
            if not can_delete:
                # Circular dependency or unresolved - take the first one
                can_delete = [remaining[0]]
                print("⚠️  Warning: Potential circular dependency detected")
            
            # Add to deletion order and remove from remaining
            deletion_order.extend(can_delete)
            for resource in can_delete:
                remaining.remove(resource)
                remaining_ids.remove(resource.identifier)
        
        return deletion_order