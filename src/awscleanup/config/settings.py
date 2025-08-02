"""
Configuration management for AWS cleanup tool.
"""

import json
import configparser
from pathlib import Path
from typing import Dict, List, Optional
from ..core.models import ServiceConfig


class Settings:
    """Application settings and configuration."""
    
    def __init__(self):
        self.config_dir = Path.home() / '.aws'
        self.service_config_file = self.config_dir / 'cleanup_services.conf'
        self.ui_config_file = self.config_dir / 'cleanup_ui.conf'
        
        # Default service configurations
        self.default_services = {
            'ec2': ServiceConfig('ec2', enabled=True, protected=False),
            's3': ServiceConfig('s3', enabled=True, protected=False),
            'rds': ServiceConfig('rds', enabled=True, protected=False),
            'lambda': ServiceConfig('lambda', enabled=True, protected=False),
            'iam': ServiceConfig('iam', enabled=False, protected=True),  # Protected by default
            'route53': ServiceConfig('route53', enabled=False, protected=True),
            'cloudformation': ServiceConfig('cloudformation', enabled=False, protected=True),
        }
        
        # UI settings
        self.ui_settings = {
            'retro_mode': True,
            'animation_speed': 'normal',  # slow, normal, fast
            'sound_effects': False,
            'color_scheme': 'neon',  # neon, classic, matrix
            'easter_eggs': True,
        }
        
        self.load_configuration()
    
    def load_configuration(self) -> None:
        """Load configuration from files."""
        self.load_service_config()
        self.load_ui_config()
    
    def load_service_config(self) -> None:
        """Load service configuration."""
        if not self.service_config_file.exists():
            self.save_service_config()
            return
        
        try:
            config = configparser.ConfigParser()
            config.read(self.service_config_file)
            
            for service_name in self.default_services:
                if service_name in config:
                    section = config[service_name]
                    self.default_services[service_name] = ServiceConfig(
                        name=service_name,
                        enabled=section.getboolean('enabled', True),
                        protected=section.getboolean('protected', False),
                        discovery_regions=self._parse_regions(section.get('regions', ''))
                    )
        except Exception as e:
            print(f"⚠️  Error loading service config: {e}")
    
    def load_ui_config(self) -> None:
        """Load UI configuration."""
        if not self.ui_config_file.exists():
            self.save_ui_config()
            return
        
        try:
            config = configparser.ConfigParser()
            config.read(self.ui_config_file)
            
            if 'ui' in config:
                ui_section = config['ui']
                self.ui_settings.update({
                    'retro_mode': ui_section.getboolean('retro_mode', True),
                    'animation_speed': ui_section.get('animation_speed', 'normal'),
                    'sound_effects': ui_section.getboolean('sound_effects', False),
                    'color_scheme': ui_section.get('color_scheme', 'neon'),
                    'easter_eggs': ui_section.getboolean('easter_eggs', True),
                })
        except Exception as e:
            print(f"⚠️  Error loading UI config: {e}")
    
    def save_service_config(self) -> None:
        """Save service configuration."""
        self.config_dir.mkdir(exist_ok=True)
        
        config = configparser.ConfigParser()
        for service_name, service_config in self.default_services.items():
            config[service_name] = {
                'enabled': str(service_config.enabled),
                'protected': str(service_config.protected),
                'regions': ','.join(service_config.discovery_regions or [])
            }
        
        with open(self.service_config_file, 'w') as f:
            config.write(f)
    
    def save_ui_config(self) -> None:
        """Save UI configuration."""
        self.config_dir.mkdir(exist_ok=True)
        
        config = configparser.ConfigParser()
        config['ui'] = {
            'retro_mode': str(self.ui_settings['retro_mode']),
            'animation_speed': self.ui_settings['animation_speed'],
            'sound_effects': str(self.ui_settings['sound_effects']),
            'color_scheme': self.ui_settings['color_scheme'],
            'easter_eggs': str(self.ui_settings['easter_eggs']),
        }
        
        with open(self.ui_config_file, 'w') as f:
            config.write(f)
    
    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get configuration for a specific service."""
        return self.default_services.get(service_name)
    
    def set_service_enabled(self, service_name: str, enabled: bool) -> None:
        """Enable or disable a service."""
        if service_name in self.default_services:
            self.default_services[service_name].enabled = enabled
            self.save_service_config()
    
    def set_service_protected(self, service_name: str, protected: bool) -> None:
        """Mark a service as protected or unprotected."""
        if service_name in self.default_services:
            self.default_services[service_name].protected = protected
            self.save_service_config()
    
    def get_enabled_services(self) -> List[str]:
        """Get list of enabled services."""
        return [name for name, config in self.default_services.items() 
                if config.enabled and not config.protected]
    
    def get_protected_services(self) -> List[str]:
        """Get list of protected services."""
        return [name for name, config in self.default_services.items() 
                if config.protected]
    
    def _parse_regions(self, regions_str: str) -> Optional[List[str]]:
        """Parse comma-separated regions string."""
        if not regions_str.strip():
            return None
        return [r.strip() for r in regions_str.split(',') if r.strip()]
    
    def toggle_easter_eggs(self) -> bool:
        """Toggle easter eggs on/off. Returns new state."""
        self.ui_settings['easter_eggs'] = not self.ui_settings['easter_eggs']
        self.save_ui_config()
        return self.ui_settings['easter_eggs']