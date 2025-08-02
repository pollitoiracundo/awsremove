"""
Custom exceptions for AWS cleanup operations.
"""


class AWSCleanupError(Exception):
    """Base exception for AWS cleanup operations."""
    pass


class ProfileError(AWSCleanupError):
    """Error related to AWS profile management."""
    pass


class AccountSecurityError(AWSCleanupError):
    """Error related to account security checks."""
    pass


class ResourceDiscoveryError(AWSCleanupError):
    """Error during resource discovery."""
    pass


class ResourceDeletionError(AWSCleanupError):
    """Error during resource deletion."""
    pass


class DependencyError(AWSCleanupError):
    """Error related to resource dependencies."""
    pass


class ServiceNotSupportedError(AWSCleanupError):
    """Error when trying to operate on unsupported service."""
    pass


class ProtectedServiceError(AWSCleanupError):
    """Error when trying to operate on protected service."""
    pass