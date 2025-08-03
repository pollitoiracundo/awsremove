"""
Base classes for AWS service discovery and management.
"""

import json
import os
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
        
        # Create environment with AWS_PROFILE explicitly set
        env = os.environ.copy()
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
            return json.loads(result.stdout) if result.stdout.strip() else {}
        except subprocess.CalledProcessError as e:
            if e.returncode == 253:
                raise ResourceDiscoveryError(
                    f"AWS credentials not found. Please configure AWS credentials or specify a valid profile. "
                    f"Command failed: {' '.join(cmd)}"
                )
            elif e.returncode == 254:
                raise ResourceDiscoveryError(
                    f"AWS access denied. Check your AWS permissions for the current profile. "
                    f"Error: {e.stderr or 'Permission denied'}"
                )
            else:
                error_msg = e.stderr.decode() if hasattr(e.stderr, 'decode') else str(e.stderr or e)
                if "UnauthorizedOperation" in error_msg or "AccessDenied" in error_msg:
                    raise ResourceDiscoveryError(
                        f"AWS access denied. The current AWS user/role does not have sufficient permissions. "
                        f"Error: {error_msg}"
                    )
                else:
                    raise ResourceDiscoveryError(f"AWS command failed (exit code {e.returncode}): {error_msg}")
        except json.JSONDecodeError as e:
            raise ResourceDiscoveryError(f"Failed to parse AWS response: {e}")
    
    def _run_aws_command_simple(self, cmd_args: List[str]) -> bool:
        """Run an AWS CLI command for deletion. Returns success status."""
        cmd = self.aws_cmd_base + cmd_args
        try:
            # Use current environment which should have AWS_PROFILE set
            subprocess.run(cmd, capture_output=True, text=True, check=True, env=os.environ)
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