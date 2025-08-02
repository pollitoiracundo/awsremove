"""
Factory for creating AWS service handlers.
"""

from typing import Dict, List, Type
from .base import BaseAWSService
from .ec2_service import EC2Service
from .s3_service import S3Service
from ..core.exceptions import ServiceNotSupportedError


class ServiceFactory:
    """Factory for creating AWS service instances."""
    
    # Registry of supported services
    _services: Dict[str, Type[BaseAWSService]] = {
        'ec2': EC2Service,
        's3': S3Service,
        # Add more services here as they're implemented
    }
    
    @classmethod
    def create_service(cls, service_name: str, aws_cmd_base: List[str]) -> BaseAWSService:
        """Create a service instance."""
        if service_name not in cls._services:
            raise ServiceNotSupportedError(f"Service '{service_name}' is not supported")
        
        service_class = cls._services[service_name]
        return service_class(aws_cmd_base)
    
    @classmethod
    def get_supported_services(cls) -> List[str]:
        """Get list of supported service names."""
        return list(cls._services.keys())
    
    @classmethod
    def register_service(cls, service_name: str, service_class: Type[BaseAWSService]) -> None:
        """Register a new service class."""
        cls._services[service_name] = service_class