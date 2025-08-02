"""
Core data models for AWS resource management.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from enum import Enum


class EnvironmentType(Enum):
    """Environment classification."""
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"
    PROTECTED = "protected"
    SAFE = "safe"
    UNKNOWN = "unknown"


class ResourceState(Enum):
    """Resource operational state."""
    RUNNING = "running"
    STOPPED = "stopped"
    PENDING = "pending"
    TERMINATED = "terminated"
    AVAILABLE = "available"
    DELETING = "deleting"
    UNKNOWN = "unknown"


@dataclass
class AWSResource:
    """Represents an AWS resource with dependencies."""
    service: str
    resource_type: str
    identifier: str
    name: str
    region: str
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    state: ResourceState = ResourceState.UNKNOWN
    
    @property
    def display_name(self) -> str:
        """Get a human-readable display name."""
        return self.name or self.identifier
    
    @property
    def full_identifier(self) -> str:
        """Get a unique identifier including service and type."""
        return f"{self.service}:{self.resource_type}:{self.identifier}"


@dataclass
class AWSAccountInfo:
    """AWS account and profile information."""
    account_id: str
    user_arn: str
    user_id: str
    profile: str
    region: str
    environment_type: EnvironmentType = EnvironmentType.UNKNOWN
    
    @property
    def is_production(self) -> bool:
        """Check if this is a production environment."""
        return self.environment_type == EnvironmentType.PRODUCTION
    
    @property
    def is_protected(self) -> bool:
        """Check if this account is protected."""
        return self.environment_type == EnvironmentType.PROTECTED


@dataclass
class ServiceConfig:
    """Configuration for AWS service handling."""
    name: str
    enabled: bool = True
    protected: bool = False
    discovery_regions: Optional[List[str]] = None
    
    def is_allowed(self) -> bool:
        """Check if service operations are allowed."""
        return self.enabled and not self.protected


@dataclass
class CleanupSession:
    """Represents a cleanup session state."""
    account_info: AWSAccountInfo
    resources: List[AWSResource] = field(default_factory=list)
    selected_resources: Set[str] = field(default_factory=set)
    service_configs: Dict[str, ServiceConfig] = field(default_factory=dict)
    
    def get_selected_resources(self) -> List[AWSResource]:
        """Get list of selected resources."""
        return [r for r in self.resources if r.identifier in self.selected_resources]
    
    def is_resource_selected(self, resource_id: str) -> bool:
        """Check if a resource is selected."""
        return resource_id in self.selected_resources
    
    def toggle_resource_selection(self, resource_id: str) -> bool:
        """Toggle resource selection. Returns True if now selected."""
        if resource_id in self.selected_resources:
            self.selected_resources.remove(resource_id)
            return False
        else:
            self.selected_resources.add(resource_id)
            return True


@dataclass
class MenuItem:
    """Represents a menu item in the UI."""
    label: str
    action: str
    enabled: bool = True
    hotkey: Optional[str] = None
    description: Optional[str] = None