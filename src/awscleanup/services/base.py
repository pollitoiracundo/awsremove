"""
Base classes for AWS service discovery and management.
"""

import json
import subprocess
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..core.models import AWSResource, ResourceState
from ..core.exceptions import ResourceDiscoveryError, ResourceDeletionError


class BaseAWSService(ABC):
    """Base class for AWS service handlers."""
    
    def __init__(self, aws_cmd_base: List[str]):
        self.aws_cmd_base = aws_cmd_base
        self.service_name = self.get_service_name()
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Get the AWS service name."""
        pass
    
    @abstractmethod
    def discover_resources(self, region: str) -> List[AWSResource]:
        """Discover resources in the specified region."""
        pass
    
    @abstractmethod
    def delete_resource(self, resource: AWSResource) -> bool:
        """Delete a specific resource."""
        pass
    
    def is_global_service(self) -> bool:
        """Check if this is a global service (not region-specific)."""
        return False
    
    def get_supported_regions(self) -> List[str]:
        """Get list of regions where this service is available."""
        return []  # Empty means all regions
    
    def _run_aws_command(self, cmd_args: List[str]) -> Dict[str, Any]:
        """Run an AWS CLI command and return parsed JSON result."""
        cmd = self.aws_cmd_base + cmd_args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout) if result.stdout.strip() else {}
        except subprocess.CalledProcessError as e:
            raise ResourceDiscoveryError(f"AWS command failed: {e}")
        except json.JSONDecodeError as e:
            raise ResourceDiscoveryError(f"Failed to parse AWS response: {e}")
    
    def _run_aws_command_simple(self, cmd_args: List[str]) -> bool:
        """Run an AWS CLI command for deletion. Returns success status."""
        cmd = self.aws_cmd_base + cmd_args
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _parse_tags(self, tags: List[Dict]) -> Dict[str, str]:
        """Parse AWS tags into a simple key-value dict."""
        if not tags:
            return {}
        return {tag.get('Key', ''): tag.get('Value', '') for tag in tags}
    
    def _get_name_from_tags(self, tags: List[Dict], fallback: str = None) -> str:
        """Extract Name tag from AWS tags list."""
        tag_dict = self._parse_tags(tags)
        return tag_dict.get('Name', fallback or '')
    
    def _determine_state(self, state_info: Any) -> ResourceState:
        """Determine resource state from AWS response."""
        if isinstance(state_info, dict):
            state_name = state_info.get('Name', '').lower()
        else:
            state_name = str(state_info).lower()
        
        state_mapping = {
            'running': ResourceState.RUNNING,
            'stopped': ResourceState.STOPPED,
            'pending': ResourceState.PENDING,
            'terminated': ResourceState.TERMINATED,
            'available': ResourceState.AVAILABLE,
            'deleting': ResourceState.DELETING,
        }
        
        return state_mapping.get(state_name, ResourceState.UNKNOWN)