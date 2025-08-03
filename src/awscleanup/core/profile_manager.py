"""
AWS Profile and Account Management.
"""

import json
import os
import subprocess
import configparser
from pathlib import Path
from typing import List, Set
from .models import AWSAccountInfo, EnvironmentType
from .exceptions import ProfileError, AccountSecurityError


class AWSProfileManager:
    """Manages AWS profiles and account safety checks."""
    
    def __init__(self):
        self.current_profile = None
        self.account_info = None
        self.aws_cmd_base = ['aws']  # Default AWS command base
        self.safe_accounts: Set[str] = set()
        self.protected_accounts: Set[str] = set()
        self.load_safety_config()
    
    def load_safety_config(self) -> None:
        """Load account safety configuration from file."""
        config_file = Path.home() / '.aws' / 'cleanup_safety.conf'
        if not config_file.exists():
            return
            
        try:
            config = configparser.ConfigParser()
            config.read(config_file)
            
            if 'safe_accounts' in config:
                accounts = config['safe_accounts'].get('accounts', '')
                self.safe_accounts = {acc.strip() for acc in accounts.split(',') if acc.strip()}
                
            if 'protected_accounts' in config:
                accounts = config['protected_accounts'].get('accounts', '')
                self.protected_accounts = {acc.strip() for acc in accounts.split(',') if acc.strip()}
                
        except Exception as e:
            print(f"⚠️  Error loading safety config: {e}")
    
    def save_safety_config(self) -> None:
        """Save account safety configuration to file."""
        config_file = Path.home() / '.aws' / 'cleanup_safety.conf'
        config_file.parent.mkdir(exist_ok=True)
        
        config = configparser.ConfigParser()
        config['safe_accounts'] = {'accounts': ','.join(self.safe_accounts)}
        config['protected_accounts'] = {'accounts': ','.join(self.protected_accounts)}
        
        with open(config_file, 'w') as f:
            config.write(f)
    
    def get_available_profiles(self) -> List[str]:
        """Get list of available AWS profiles."""
        profiles = ['default']
        
        # Check AWS credentials file
        creds_file = Path.home() / '.aws' / 'credentials'
        if creds_file.exists():
            try:
                config = configparser.ConfigParser()
                config.read(creds_file)
                profiles.extend([section for section in config.sections() if section != 'default'])
            except Exception:
                pass
        
        # Check AWS config file
        config_file = Path.home() / '.aws' / 'config'
        if config_file.exists():
            try:
                config = configparser.ConfigParser()
                config.read(config_file)
                for section in config.sections():
                    if section.startswith('profile '):
                        profile_name = section.replace('profile ', '')
                        if profile_name not in profiles:
                            profiles.append(profile_name)
            except Exception:
                pass
        
        return sorted(list(set(profiles)))
    
    def get_account_info(self, profile: str = None) -> AWSAccountInfo:
        """Get current AWS account information."""
        # Set up environment for this call
        env = os.environ.copy()
        if profile and profile != 'default':
            env['AWS_PROFILE'] = profile
        elif 'AWS_PROFILE' in env:
            del env['AWS_PROFILE']
        
        cmd = ['aws', 'sts', 'get-caller-identity', '--output', 'json']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
            identity = json.loads(result.stdout)
            
            # Get current region
            region_cmd = ['aws', 'configure', 'get', 'region']
            
            region_result = subprocess.run(region_cmd, capture_output=True, text=True, env=env)
            region = region_result.stdout.strip() if region_result.returncode == 0 else 'us-east-1'
            
            # Determine environment type
            env_type = self._determine_environment_type(identity['Account'], identity['Arn'])
            
            return AWSAccountInfo(
                account_id=identity['Account'],
                user_arn=identity['Arn'],
                user_id=identity['UserId'],
                profile=profile or 'default',
                region=region,
                environment_type=env_type
            )
        except subprocess.CalledProcessError as e:
            if e.returncode == 253:
                available_profiles = self.get_available_profiles()
                available_profiles = [p for p in available_profiles if p != 'default']
                if available_profiles:
                    raise ProfileError(
                        f"No credentials found for profile '{profile or 'default'}'. "
                        f"Available profiles: {', '.join(available_profiles)}. "
                        f"Use --profile <profile_name> to specify a profile."
                    )
                else:
                    raise ProfileError(
                        "No AWS credentials found. Run 'aws configure' to set up credentials "
                        "or create a profile with 'aws configure --profile <profile_name>'."
                    )
            else:
                raise ProfileError(f"AWS CLI error (exit code {e.returncode}): {e.stderr or e}")
        except json.JSONDecodeError as e:
            raise ProfileError(f"Failed to parse AWS response: {e}")
        except Exception as e:
            raise ProfileError(f"Failed to get account information: {e}")
    
    def _determine_environment_type(self, account_id: str, user_arn: str) -> EnvironmentType:
        """Determine environment type based on account and ARN."""
        arn_lower = user_arn.lower()
        
        if account_id in self.protected_accounts:
            return EnvironmentType.PROTECTED
        elif account_id in self.safe_accounts:
            return EnvironmentType.SAFE
        elif any(keyword in arn_lower for keyword in ['prod', 'production']):
            return EnvironmentType.PRODUCTION
        elif any(keyword in arn_lower for keyword in ['stage', 'staging']):
            return EnvironmentType.STAGING
        elif any(keyword in arn_lower for keyword in ['dev', 'development']):
            return EnvironmentType.DEVELOPMENT
        elif any(keyword in arn_lower for keyword in ['test', 'testing']):
            return EnvironmentType.TESTING
        else:
            return EnvironmentType.UNKNOWN
    
    def verify_account_safety(self, account_info: AWSAccountInfo) -> bool:
        """Verify if it's safe to proceed with this account."""
        if account_info.account_id in self.protected_accounts:
            raise AccountSecurityError(
                f"Account {account_info.account_id} is in the PROTECTED list!"
            )
        
        return True
    
    def setup_aws_command(self, profile: str) -> List[str]:
        """Setup AWS command with proper profile using environment variable."""
        self.current_profile = profile
        
        # Set AWS_PROFILE environment variable for all AWS CLI calls
        if profile and profile != 'default':
            os.environ['AWS_PROFILE'] = profile
        elif 'AWS_PROFILE' in os.environ:
            # Remove AWS_PROFILE if using default profile
            del os.environ['AWS_PROFILE']
        
        # Use simple aws command without --profile flag since we use env var
        base_cmd = ['aws']
        self.aws_cmd_base = base_cmd  # Store the command base
        return base_cmd
    
    def add_safe_account(self, account_id: str) -> None:
        """Add account to safe list."""
        self.safe_accounts.add(account_id)
        self.save_safety_config()
    
    def add_protected_account(self, account_id: str) -> None:
        """Add account to protected list."""
        self.protected_accounts.add(account_id)
        self.save_safety_config()
    
    def remove_safe_account(self, account_id: str) -> bool:
        """Remove account from safe list. Returns True if removed."""
        if account_id in self.safe_accounts:
            self.safe_accounts.remove(account_id)
            self.save_safety_config()
            return True
        return False
    
    def remove_protected_account(self, account_id: str) -> bool:
        """Remove account from protected list. Returns True if removed."""
        if account_id in self.protected_accounts:
            self.protected_accounts.remove(account_id)
            self.save_safety_config()
            return True
        return False
    
    def get_configured_region(self, profile: str = None) -> str:
        """Get the configured region for a profile."""
        # Set up environment for this call
        env = os.environ.copy()
        if profile and profile != 'default':
            env['AWS_PROFILE'] = profile
        elif 'AWS_PROFILE' in env:
            del env['AWS_PROFILE']
        
        try:
            region_cmd = ['aws', 'configure', 'get', 'region']
            result = subprocess.run(region_cmd, capture_output=True, text=True, env=env)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return None
        except Exception:
            return None
    
    def set_default_region(self, profile: str, region: str) -> None:
        """Set default region for a profile."""
        try:
            env = os.environ.copy()
            if profile and profile != 'default':
                env['AWS_PROFILE'] = profile
            elif 'AWS_PROFILE' in env:
                del env['AWS_PROFILE']
            
            cmd = ['aws', 'configure', 'set', 'region', region]
            subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        except subprocess.CalledProcessError as e:
            raise ProfileError(f"Failed to set region for profile {profile}: {e}")
    
    def get_available_regions_simple(self, profile: str = None) -> List[str]:
        """Get available regions using a simple approach with default region."""
        # Common AWS regions as fallback
        common_regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2',
            'ap-south-1', 'sa-east-1', 'ca-central-1'
        ]
        
        try:
            # Set up environment
            env = os.environ.copy()
            if profile and profile != 'default':
                env['AWS_PROFILE'] = profile
            elif 'AWS_PROFILE' in env:
                del env['AWS_PROFILE']
            
            # Try to get regions using us-east-1 as default
            cmd = ['aws', 'ec2', 'describe-regions', '--region', 'us-east-1', 
                   '--query', 'Regions[].RegionName', '--output', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
            regions = json.loads(result.stdout)
            return sorted(regions)
        except Exception:
            # Fallback to common regions if API call fails
            return common_regions