"""
AWS Profile and Account Management.
"""

import json
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
        cmd = ['aws', 'sts', 'get-caller-identity', '--output', 'json']
        if profile and profile != 'default':
            cmd.extend(['--profile', profile])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            identity = json.loads(result.stdout)
            
            # Get current region
            region_cmd = ['aws', 'configure', 'get', 'region']
            if profile and profile != 'default':
                region_cmd.extend(['--profile', profile])
            
            region_result = subprocess.run(region_cmd, capture_output=True, text=True)
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
        """Setup AWS command with proper profile."""
        self.current_profile = profile
        base_cmd = ['aws']
        if profile and profile != 'default':
            base_cmd.extend(['--profile', profile])
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