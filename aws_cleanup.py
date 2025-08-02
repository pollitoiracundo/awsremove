#!/usr/bin/env python3
"""
AWS Resource Cleanup Tool
Interactive program to discover and safely clean up AWS resources with dependency tracking.
"""

import json
import subprocess
import sys
import os
import configparser
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import argparse
from pathlib import Path


@dataclass
class AWSResource:
    service: str
    resource_type: str
    identifier: str
    name: str
    region: str
    dependencies: List[str]
    dependents: List[str]
    metadata: Dict


@dataclass
class AWSAccountInfo:
    account_id: str
    user_arn: str
    user_id: str
    profile: str
    region: str
    environment_type: str = "unknown"


class AWSProfileManager:
    """Manages AWS profiles and account safety checks."""
    
    def __init__(self):
        self.current_profile = None
        self.account_info = None
        self.safe_accounts = set()
        self.protected_accounts = set()
        self.load_safety_config()
    
    def load_safety_config(self):
        """Load account safety configuration from file."""
        config_file = Path.home() / '.aws' / 'cleanup_safety.conf'
        if config_file.exists():
            try:
                config = configparser.ConfigParser()
                config.read(config_file)
                
                if 'safe_accounts' in config:
                    self.safe_accounts = set(config['safe_accounts'].get('accounts', '').split(','))
                    self.safe_accounts = {acc.strip() for acc in self.safe_accounts if acc.strip()}
                    
                if 'protected_accounts' in config:
                    self.protected_accounts = set(config['protected_accounts'].get('accounts', '').split(','))
                    self.protected_accounts = {acc.strip() for acc in self.protected_accounts if acc.strip()}
                    
                print(f"📋 Loaded safety config: {len(self.safe_accounts)} safe accounts, {len(self.protected_accounts)} protected accounts")
            except Exception as e:
                print(f"⚠️  Error loading safety config: {e}")
    
    def save_safety_config(self):
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
            except Exception as e:
                print(f"Error reading credentials file: {e}")
        
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
            except Exception as e:
                print(f"Error reading config file: {e}")
        
        return sorted(list(set(profiles)))
    
    def get_current_account_info(self, profile: str = None) -> AWSAccountInfo:
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
            
            # Determine environment type based on account ID or user ARN
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
            raise Exception(f"Failed to get account information: {e}")
    
    def _determine_environment_type(self, account_id: str, user_arn: str) -> str:
        """Determine if this looks like prod, dev, staging, etc."""
        arn_lower = user_arn.lower()
        
        if any(keyword in arn_lower for keyword in ['prod', 'production']):
            return 'production'
        elif any(keyword in arn_lower for keyword in ['stage', 'staging']):
            return 'staging'
        elif any(keyword in arn_lower for keyword in ['dev', 'development', 'test']):
            return 'development'
        elif account_id in self.protected_accounts:
            return 'protected'
        elif account_id in self.safe_accounts:
            return 'safe'
        else:
            return 'unknown'
    
    def select_profile(self) -> str:
        """Interactive profile selection."""
        profiles = self.get_available_profiles()
        
        if len(profiles) == 1:
            return profiles[0]
        
        print("\n🔐 Available AWS Profiles:")
        for i, profile in enumerate(profiles, 1):
            try:
                account_info = self.get_current_account_info(profile)
                env_indicator = self._get_environment_indicator(account_info.environment_type)
                print(f"{i:2d}. {profile:<20} (Account: {account_info.account_id}) {env_indicator}")
            except Exception:
                print(f"{i:2d}. {profile:<20} (Account: UNKNOWN)")
        
        while True:
            try:
                choice = input(f"\nSelect profile (1-{len(profiles)}): ").strip()
                if choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(profiles):
                        return profiles[index]
                print("Invalid selection. Please try again.")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                sys.exit(0)
    
    def _get_environment_indicator(self, env_type: str) -> str:
        """Get visual indicator for environment type."""
        indicators = {
            'production': '🔴 PRODUCTION',
            'staging': '🟡 STAGING', 
            'development': '🟢 DEV/TEST',
            'protected': '🔒 PROTECTED',
            'safe': '✅ SAFE',
            'unknown': '⚠️  UNKNOWN'
        }
        return indicators.get(env_type, '❓ UNCLASSIFIED')
    
    def verify_account_safety(self, account_info: AWSAccountInfo) -> bool:
        """Verify if it's safe to proceed with this account."""
        print(f"\n🔍 Account Verification:")
        print(f"   Profile: {account_info.profile}")
        print(f"   Account ID: {account_info.account_id}")
        print(f"   User: {account_info.user_arn}")
        print(f"   Region: {account_info.region}")
        print(f"   Environment: {self._get_environment_indicator(account_info.environment_type)}")
        
        # Check if account is protected
        if account_info.account_id in self.protected_accounts:
            print(f"\n🚫 ERROR: Account {account_info.account_id} is in the PROTECTED list!")
            print("This account cannot be used with the cleanup tool.")
            return False
        
        # Check if this looks like a production environment
        if account_info.environment_type == 'production':
            print(f"\n⚠️  WARNING: This appears to be a PRODUCTION environment!")
            print("Proceeding could cause serious damage to production systems.")
            
            confirm = input("Type 'I-UNDERSTAND-THE-RISKS' to continue: ")
            if confirm != 'I-UNDERSTAND-THE-RISKS':
                print("Safety check failed. Exiting.")
                return False
        
        # Final confirmation for unknown accounts
        if account_info.environment_type == 'unknown':
            print(f"\n❓ WARNING: Unknown environment type for account {account_info.account_id}")
            print("Please verify this is a safe account to modify.")
            
            # Offer to add to safe list
            add_to_safe = input("Add this account to your safe accounts list? (y/N): ")
            if add_to_safe.lower() == 'y':
                self.safe_accounts.add(account_info.account_id)
                self.save_safety_config()
                print(f"✅ Added {account_info.account_id} to safe accounts list.")
            
            confirm = input("Continue with cleanup in this account? (y/N): ")
            if confirm.lower() != 'y':
                return False
        
        return True
    
    def setup_aws_command(self, profile: str) -> List[str]:
        """Setup AWS command with proper profile."""
        self.current_profile = profile
        base_cmd = ['aws']
        if profile and profile != 'default':
            base_cmd.extend(['--profile', profile])
        return base_cmd


class AWSResourceDiscovery:
    """Discovers AWS resources across all services and regions."""
    
    def __init__(self, profile_manager: AWSProfileManager):
        self.regions = []
        self.resources = []
        self.dependency_map = defaultdict(set)
        self.profile_manager = profile_manager
        self.aws_cmd_base = profile_manager.setup_aws_command(profile_manager.current_profile)
        
    def get_available_regions(self) -> List[str]:
        """Get all available AWS regions."""
        try:
            cmd = self.aws_cmd_base + ['ec2', 'describe-regions', '--query', 'Regions[].RegionName', '--output', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Error getting regions: {e}")
            return ['us-east-1']  # fallback
    
    def discover_ec2_resources(self, region: str) -> List[AWSResource]:
        """Discover EC2 instances, volumes, snapshots, etc."""
        resources = []
        
        # EC2 Instances
        try:
            cmd = self.aws_cmd_base + [
                'ec2', 'describe-instances',
                '--region', region,
                '--query', 'Reservations[].Instances[].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name,VpcId,SubnetId]',
                '--output', 'json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            instances = json.loads(result.stdout)
            for instance in instances:
                if len(instance) >= 3:
                    instance_id, name, state, vpc_id, subnet_id = instance[:5]
                    if state != 'terminated':
                        resources.append(AWSResource(
                            service='ec2',
                            resource_type='instance',
                            identifier=instance_id,
                            name=name or instance_id,
                            region=region,
                            dependencies=[vpc_id, subnet_id] if vpc_id and subnet_id else [],
                            dependents=[],
                            metadata={'state': state, 'vpc_id': vpc_id, 'subnet_id': subnet_id}
                        ))
        except Exception as e:
            print(f"Error discovering EC2 instances in {region}: {e}")
        
        # EBS Volumes
        try:
            cmd = self.aws_cmd_base + [
                'ec2', 'describe-volumes',
                '--region', region,
                '--query', 'Volumes[].[VolumeId,Tags[?Key==`Name`].Value|[0],State,Attachments[0].InstanceId]',
                '--output', 'json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            volumes = json.loads(result.stdout)
            for volume in volumes:
                if len(volume) >= 3:
                    volume_id, name, state, instance_id = volume[:4]
                    dependencies = [instance_id] if instance_id else []
                    resources.append(AWSResource(
                        service='ec2',
                        resource_type='volume',
                        identifier=volume_id,
                        name=name or volume_id,
                        region=region,
                        dependencies=dependencies,
                        dependents=[],
                        metadata={'state': state, 'instance_id': instance_id}
                    ))
        except Exception as e:
            print(f"Error discovering EBS volumes in {region}: {e}")
            
        return resources
    
    def discover_s3_resources(self) -> List[AWSResource]:
        """Discover S3 buckets (global service)."""
        resources = []
        try:
            cmd = self.aws_cmd_base + [
                's3api', 'list-buckets',
                '--query', 'Buckets[].[Name,CreationDate]',
                '--output', 'json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            buckets = json.loads(result.stdout)
            for bucket in buckets:
                bucket_name, creation_date = bucket
                resources.append(AWSResource(
                    service='s3',
                    resource_type='bucket',
                    identifier=bucket_name,
                    name=bucket_name,
                    region='global',
                    dependencies=[],
                    dependents=[],
                    metadata={'creation_date': creation_date}
                ))
        except Exception as e:
            print(f"Error discovering S3 buckets: {e}")
            
        return resources
    
    def discover_rds_resources(self, region: str) -> List[AWSResource]:
        """Discover RDS instances and clusters."""
        resources = []
        
        # RDS Instances
        try:
            cmd = self.aws_cmd_base + [
                'rds', 'describe-db-instances',
                '--region', region,
                '--query', 'DBInstances[].[DBInstanceIdentifier,DBInstanceStatus,VpcId,DBSubnetGroup.VpcId]',
                '--output', 'json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            instances = json.loads(result.stdout)
            for instance in instances:
                if len(instance) >= 2:
                    db_id, status, vpc_id, subnet_vpc = instance[:4]
                    dependencies = [vpc_id] if vpc_id else []
                    resources.append(AWSResource(
                        service='rds',
                        resource_type='db_instance',
                        identifier=db_id,
                        name=db_id,
                        region=region,
                        dependencies=dependencies,
                        dependents=[],
                        metadata={'status': status, 'vpc_id': vpc_id}
                    ))
        except Exception as e:
            print(f"Error discovering RDS instances in {region}: {e}")
            
        return resources
    
    def discover_lambda_resources(self, region: str) -> List[AWSResource]:
        """Discover Lambda functions."""
        resources = []
        try:
            cmd = self.aws_cmd_base + [
                'lambda', 'list-functions',
                '--region', region,
                '--query', 'Functions[].[FunctionName,Runtime,VpcConfig.VpcId]',
                '--output', 'json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            functions = json.loads(result.stdout)
            for func in functions:
                if len(func) >= 2:
                    func_name, runtime, vpc_id = func[:3]
                    dependencies = [vpc_id] if vpc_id else []
                    resources.append(AWSResource(
                        service='lambda',
                        resource_type='function',
                        identifier=func_name,
                        name=func_name,
                        region=region,
                        dependencies=dependencies,
                        dependents=[],
                        metadata={'runtime': runtime, 'vpc_id': vpc_id}
                    ))
        except Exception as e:
            print(f"Error discovering Lambda functions in {region}: {e}")
            
        return resources
    
    def discover_all_resources(self) -> List[AWSResource]:
        """Discover all AWS resources across all services and regions."""
        print("🔍 Discovering AWS resources...")
        all_resources = []
        
        # Get available regions
        self.regions = self.get_available_regions()
        print(f"Scanning {len(self.regions)} regions...")
        
        # Global services (S3)
        print("  📦 Discovering S3 buckets...")
        all_resources.extend(self.discover_s3_resources())
        
        # Regional services
        for region in self.regions:
            print(f"  🌍 Scanning region: {region}")
            
            print(f"    🖥️  EC2 resources...")
            all_resources.extend(self.discover_ec2_resources(region))
            
            print(f"    🗄️  RDS resources...")
            all_resources.extend(self.discover_rds_resources(region))
            
            print(f"    ⚡ Lambda functions...")
            all_resources.extend(self.discover_lambda_resources(region))
        
        self.resources = all_resources
        self.build_dependency_map()
        return all_resources
    
    def build_dependency_map(self):
        """Build bidirectional dependency relationships."""
        # Create a lookup map
        resource_map = {r.identifier: r for r in self.resources}
        
        # Build dependency relationships
        for resource in self.resources:
            for dep_id in resource.dependencies:
                if dep_id in resource_map:
                    resource_map[dep_id].dependents.append(resource.identifier)


class InteractiveCleanup:
    """Interactive interface for resource selection and cleanup."""
    
    def __init__(self, resources: List[AWSResource], profile_manager: AWSProfileManager):
        self.resources = resources
        self.selected_for_deletion = set()
        self.resource_map = {r.identifier: r for r in resources}
        self.profile_manager = profile_manager
        self.aws_cmd_base = profile_manager.aws_cmd_base
    
    def display_resources(self, resources: List[AWSResource] = None):
        """Display resources in a formatted table."""
        if resources is None:
            resources = self.resources
            
        if not resources:
            print("No resources found.")
            return
            
        print(f"\n{'#':<3} {'Service':<10} {'Type':<15} {'Name':<30} {'Region':<15} {'Status'}")
        print("-" * 90)
        
        for i, resource in enumerate(resources, 1):
            status = "🗑️ SELECTED" if resource.identifier in self.selected_for_deletion else ""
            print(f"{i:<3} {resource.service:<10} {resource.resource_type:<15} {resource.name[:29]:<30} {resource.region:<15} {status}")
    
    def show_dependencies(self, resource: AWSResource):
        """Show dependencies and dependents for a resource."""
        print(f"\n📋 Dependencies for {resource.name} ({resource.identifier}):")
        
        if resource.dependencies:
            print("  🔗 Depends on:")
            for dep_id in resource.dependencies:
                if dep_id in self.resource_map:
                    dep = self.resource_map[dep_id]
                    print(f"    - {dep.name} ({dep.service}/{dep.resource_type})")
                else:
                    print(f"    - {dep_id} (external or not discovered)")
        else:
            print("  ✅ No dependencies")
            
        if resource.dependents:
            print("  ⚠️  Resources that depend on this:")
            for dep_id in resource.dependents:
                if dep_id in self.resource_map:
                    dep = self.resource_map[dep_id]
                    print(f"    - {dep.name} ({dep.service}/{dep.resource_type})")
        else:
            print("  ✅ No dependents")
    
    def select_resource(self, resource_index: int):
        """Select/deselect a resource for deletion."""
        if 1 <= resource_index <= len(self.resources):
            resource = self.resources[resource_index - 1]
            
            if resource.identifier in self.selected_for_deletion:
                self.selected_for_deletion.remove(resource.identifier)
                print(f"❌ Deselected: {resource.name}")
            else:
                # Show dependencies before selection
                self.show_dependencies(resource)
                
                # Warn about dependents
                if resource.dependents:
                    print(f"\n⚠️  WARNING: {len(resource.dependents)} resources depend on this!")
                    confirm = input("Are you sure you want to select this for deletion? (y/N): ")
                    if confirm.lower() != 'y':
                        print("Selection cancelled.")
                        return
                
                self.selected_for_deletion.add(resource.identifier)
                print(f"✅ Selected: {resource.name}")
        else:
            print("Invalid resource number.")
    
    def show_selected(self):
        """Show all selected resources."""
        if not self.selected_for_deletion:
            print("No resources selected for deletion.")
            return
            
        selected_resources = [r for r in self.resources if r.identifier in self.selected_for_deletion]
        print(f"\n🗑️  {len(selected_resources)} resources selected for deletion:")
        self.display_resources(selected_resources)
    
    def confirm_deletion(self) -> bool:
        """Final confirmation before deletion."""
        if not self.selected_for_deletion:
            print("No resources selected for deletion.")
            return False
            
        self.show_selected()
        print(f"\n⚠️  YOU ARE ABOUT TO DELETE {len(self.selected_for_deletion)} AWS RESOURCES!")
        print("This action cannot be undone.")
        
        confirm1 = input("Type 'DELETE' to confirm: ")
        if confirm1 != 'DELETE':
            print("Deletion cancelled.")
            return False
            
        confirm2 = input("Are you absolutely sure? (yes/no): ")
        if confirm2.lower() != 'yes':
            print("Deletion cancelled.")
            return False
            
        return True
    
    def delete_resources(self, dry_run: bool = True):
        """Delete selected resources (with dry-run option)."""
        if not self.confirm_deletion():
            return
            
        selected_resources = [r for r in self.resources if r.identifier in self.selected_for_deletion]
        
        # Sort by dependencies (delete dependents first)
        # This is a simplified ordering - a full implementation would need topological sorting
        deletion_order = []
        remaining = selected_resources.copy()
        
        while remaining:
            # Find resources with no dependents in the remaining set
            can_delete = []
            for resource in remaining:
                has_dependents_in_remaining = any(
                    dep_id in [r.identifier for r in remaining] 
                    for dep_id in resource.dependents
                )
                if not has_dependents_in_remaining:
                    can_delete.append(resource)
            
            if not can_delete:
                # Circular dependency or unresolved - just take the first one
                can_delete = [remaining[0]]
            
            deletion_order.extend(can_delete)
            for resource in can_delete:
                remaining.remove(resource)
        
        print(f"\n🗂️  Deletion order ({len(deletion_order)} resources):")
        for i, resource in enumerate(deletion_order, 1):
            print(f"{i}. {resource.name} ({resource.service}/{resource.resource_type})")
        
        if dry_run:
            print("\n🧪 DRY RUN - No resources will actually be deleted.")
            return
        
        print(f"\n🗑️  Deleting resources...")
        for i, resource in enumerate(deletion_order, 1):
            print(f"[{i}/{len(deletion_order)}] Deleting {resource.name}...")
            success = self._delete_resource(resource)
            if success:
                print(f"✅ Deleted: {resource.name}")
            else:
                print(f"❌ Failed to delete: {resource.name}")
    
    def _delete_resource(self, resource: AWSResource) -> bool:
        """Delete a single resource."""
        try:
            if resource.service == 'ec2' and resource.resource_type == 'instance':
                cmd = self.aws_cmd_base + [
                    'ec2', 'terminate-instances',
                    '--region', resource.region,
                    '--instance-ids', resource.identifier
                ]
                subprocess.run(cmd, check=True)
                
            elif resource.service == 'ec2' and resource.resource_type == 'volume':
                cmd = self.aws_cmd_base + [
                    'ec2', 'delete-volume',
                    '--region', resource.region,
                    '--volume-id', resource.identifier
                ]
                subprocess.run(cmd, check=True)
                
            elif resource.service == 's3' and resource.resource_type == 'bucket':
                # First empty the bucket
                cmd1 = self.aws_cmd_base + [
                    's3', 'rm', f's3://{resource.identifier}',
                    '--recursive'
                ]
                subprocess.run(cmd1, check=True)
                # Then delete the bucket
                cmd2 = self.aws_cmd_base + [
                    's3api', 'delete-bucket',
                    '--bucket', resource.identifier
                ]
                subprocess.run(cmd2, check=True)
                
            elif resource.service == 'rds' and resource.resource_type == 'db_instance':
                cmd = self.aws_cmd_base + [
                    'rds', 'delete-db-instance',
                    '--region', resource.region,
                    '--db-instance-identifier', resource.identifier,
                    '--skip-final-snapshot'
                ]
                subprocess.run(cmd, check=True)
                
            elif resource.service == 'lambda' and resource.resource_type == 'function':
                cmd = self.aws_cmd_base + [
                    'lambda', 'delete-function',
                    '--region', resource.region,
                    '--function-name', resource.identifier
                ]
                subprocess.run(cmd, check=True)
                
            else:
                print(f"⚠️  Don't know how to delete {resource.service}/{resource.resource_type}")
                return False
                
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error deleting {resource.name}: {e}")
            return False
    
    def interactive_menu(self):
        """Main interactive menu."""
        while True:
            account_info = self.profile_manager.account_info
            env_indicator = self.profile_manager._get_environment_indicator(account_info.environment_type)
            
            print("\n" + "="*60)
            print("AWS Resource Cleanup Tool")
            print("="*60)
            print(f"Current Profile: {account_info.profile}")
            print(f"Account: {account_info.account_id} {env_indicator}")
            print(f"Region: {account_info.region}")
            print("-" * 60)
            print("1. List all resources")
            print("2. Select resource for deletion")
            print("3. Show selected resources")
            print("4. Show dependencies for resource")
            print("5. Delete selected resources (DRY RUN)")
            print("6. Delete selected resources (REAL)")
            print("7. Clear selections")
            print("8. Switch AWS profile")
            print("9. Manage account safety settings")
            print("0. Exit")
            if not self.resources:
                print("\n⚠️  No resources loaded. Use option 8 to switch profiles or restart to discover resources.")
            
            choice = input("\nEnter your choice (0-9): ").strip()
            
            if choice == '1':
                self.display_resources()
                
            elif choice == '2':
                self.display_resources()
                try:
                    resource_num = int(input("\nEnter resource number to select/deselect: "))
                    self.select_resource(resource_num)
                except ValueError:
                    print("Invalid number.")
                    
            elif choice == '3':
                self.show_selected()
                
            elif choice == '4':
                self.display_resources()
                try:
                    resource_num = int(input("\nEnter resource number to show dependencies: "))
                    if 1 <= resource_num <= len(self.resources):
                        resource = self.resources[resource_num - 1]
                        self.show_dependencies(resource)
                    else:
                        print("Invalid resource number.")
                except ValueError:
                    print("Invalid number.")
                    
            elif choice == '5':
                self.delete_resources(dry_run=True)
                
            elif choice == '6':
                self.delete_resources(dry_run=False)
                
            elif choice == '7':
                self.selected_for_deletion.clear()
                print("✅ All selections cleared.")
                
            elif choice == '8':
                self._switch_profile()
                
            elif choice == '9':
                self._manage_safety_settings()
                
            elif choice == '0':
                print("Goodbye! 👋")
                break
                
            else:
                print("Invalid choice. Please try again.")
    
    def _switch_profile(self):
        """Switch to a different AWS profile."""
        print("\n🔄 Switching AWS Profile...")
        new_profile = self.profile_manager.select_profile()
        
        if new_profile == self.profile_manager.current_profile:
            print("Already using that profile.")
            return
        
        try:
            # Get account info for new profile
            new_account_info = self.profile_manager.get_current_account_info(new_profile)
            
            # Verify safety
            if not self.profile_manager.verify_account_safety(new_account_info):
                print("Profile switch cancelled for safety reasons.")
                return
            
            # Update profile manager
            self.profile_manager.current_profile = new_profile
            self.profile_manager.account_info = new_account_info
            self.profile_manager.aws_cmd_base = self.profile_manager.setup_aws_command(new_profile)
            self.aws_cmd_base = self.profile_manager.aws_cmd_base
            
            print(f"✅ Switched to profile: {new_profile}")
            print("You will need to re-discover resources for the new account.")
            
            # Clear current resources and selections
            self.resources = []
            self.selected_for_deletion.clear()
            self.resource_map = {}
            
        except Exception as e:
            print(f"❌ Error switching profile: {e}")
    
    def _manage_safety_settings(self):
        """Manage account safety settings."""
        while True:
            print("\n🔒 Account Safety Settings")
            print("1. View safe accounts")
            print("2. View protected accounts")
            print("3. Add account to safe list")
            print("4. Add account to protected list")
            print("5. Remove account from safe list")
            print("6. Remove account from protected list")
            print("7. Back to main menu")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == '1':
                print(f"\n✅ Safe accounts ({len(self.profile_manager.safe_accounts)}):")
                for acc in sorted(self.profile_manager.safe_accounts):
                    print(f"  - {acc}")
                    
            elif choice == '2':
                print(f"\n🔒 Protected accounts ({len(self.profile_manager.protected_accounts)}):")
                for acc in sorted(self.profile_manager.protected_accounts):
                    print(f"  - {acc}")
                    
            elif choice == '3':
                acc_id = input("Enter account ID to add to safe list: ").strip()
                if acc_id:
                    self.profile_manager.safe_accounts.add(acc_id)
                    self.profile_manager.save_safety_config()
                    print(f"✅ Added {acc_id} to safe accounts.")
                    
            elif choice == '4':
                acc_id = input("Enter account ID to add to protected list: ").strip()
                if acc_id:
                    self.profile_manager.protected_accounts.add(acc_id)
                    self.profile_manager.save_safety_config()
                    print(f"🔒 Added {acc_id} to protected accounts.")
                    
            elif choice == '5':
                acc_id = input("Enter account ID to remove from safe list: ").strip()
                if acc_id in self.profile_manager.safe_accounts:
                    self.profile_manager.safe_accounts.remove(acc_id)
                    self.profile_manager.save_safety_config()
                    print(f"❌ Removed {acc_id} from safe accounts.")
                else:
                    print("Account not found in safe list.")
                    
            elif choice == '6':
                acc_id = input("Enter account ID to remove from protected list: ").strip()
                if acc_id in self.profile_manager.protected_accounts:
                    self.profile_manager.protected_accounts.remove(acc_id)
                    self.profile_manager.save_safety_config()
                    print(f"❌ Removed {acc_id} from protected accounts.")
                else:
                    print("Account not found in protected list.")
                    
            elif choice == '7':
                break
                
            else:
                print("Invalid choice. Please try again.")


def main():
    parser = argparse.ArgumentParser(description='AWS Resource Cleanup Tool')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    parser.add_argument('--regions', nargs='+', help='Specific regions to scan (default: all)')
    parser.add_argument('--profile', help='AWS profile to use')
    args = parser.parse_args()
    
    # Check if AWS CLI is available
    try:
        subprocess.run(['aws', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ AWS CLI not found. Please install and configure AWS CLI first.")
        sys.exit(1)
    
    print("🚀 AWS Resource Cleanup Tool Starting...")
    
    # Initialize profile manager
    profile_manager = AWSProfileManager()
    
    # Select profile
    if args.profile:
        selected_profile = args.profile
        print(f"Using specified profile: {selected_profile}")
    else:
        selected_profile = profile_manager.select_profile()
    
    # Get account information
    try:
        account_info = profile_manager.get_current_account_info(selected_profile)
        profile_manager.account_info = account_info
    except Exception as e:
        print(f"❌ Error getting account information: {e}")
        print("Please check your AWS credentials and configuration.")
        sys.exit(1)
    
    # Verify account safety
    if not profile_manager.verify_account_safety(account_info):
        print("❌ Safety verification failed. Exiting.")
        sys.exit(1)
    
    # Set up AWS commands with the selected profile
    profile_manager.setup_aws_command(selected_profile)
    
    print(f"\n✅ Connected to AWS account {account_info.account_id} using profile '{selected_profile}'")
    
    # Discover resources
    discovery = AWSResourceDiscovery(profile_manager)
    resources = discovery.discover_all_resources()
    
    print(f"\n✅ Found {len(resources)} resources across {len(discovery.regions)} regions")
    
    if not resources:
        print("No resources found to clean up.")
        return
    
    # Start interactive cleanup
    cleanup = InteractiveCleanup(resources, profile_manager)
    cleanup.interactive_menu()


if __name__ == '__main__':
    main()