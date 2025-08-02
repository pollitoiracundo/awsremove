"""
Main application controller for AWS Cleanup Tool.
"""

import sys
from typing import List, Optional
from .models import CleanupSession, MenuItem, AWSResource
from .profile_manager import AWSProfileManager
from .discovery import ResourceDiscovery
from .exceptions import AccountSecurityError, ProfileError
from ..config.settings import Settings
from ..ui.retro_ui import RetroUI
from ..ui.colors import Color
from ..services.service_factory import ServiceFactory
from ..services.billing_service import BillingService


class AWSCleanupApp:
    """Main application controller."""
    
    def __init__(self):
        self.settings = Settings()
        self.profile_manager = AWSProfileManager()
        self.ui = RetroUI(self.settings.ui_settings['color_scheme'])
        self.session: Optional[CleanupSession] = None
        self.discovery: Optional[ResourceDiscovery] = None
        self.billing_service: Optional[BillingService] = None
        
    def run(self, profile: str = None) -> None:
        """Run the application."""
        try:
            self.ui.show_splash_screen()
            
            # Initialize session
            self._initialize_session(profile)
            
            # Main application loop
            self._main_loop()
            
        except KeyboardInterrupt:
            self.ui.show_message("Operation cancelled by user.", "info", 1.0)
        except Exception as e:
            self.ui.show_message(f"Fatal error: {e}", "error", 3.0)
        finally:
            print("\nGoodbye! 👋")
    
    def _initialize_session(self, profile: str = None) -> None:
        """Initialize the cleanup session."""
        try:
            # Select AWS profile
            if profile:
                selected_profile = profile
                self.ui.show_message(f"Using specified profile: {profile}", "info", 1.0)
            else:
                selected_profile = self._select_profile_interactive()
            
            # Get account information
            account_info = self.profile_manager.get_account_info(selected_profile)
            
            # Verify account safety
            self.profile_manager.verify_account_safety(account_info)
            
            # Create session
            self.session = CleanupSession(account_info=account_info)
            self.profile_manager.account_info = account_info
            
            # Initialize discovery and billing service
            self.discovery = ResourceDiscovery(self.profile_manager, self.settings)
            self.billing_service = BillingService(self.profile_manager.aws_cmd_base)
            
            self.ui.show_message(f"Connected to AWS account {account_info.account_id}", "success", 1.5)
            
        except AccountSecurityError as e:
            self.ui.show_message(f"Security Error: {e}", "error", 3.0)
            sys.exit(1)
        except ProfileError as e:
            self.ui.show_message(f"Profile Error: {e}", "error", 3.0)
            sys.exit(1)
    
    def _select_profile_interactive(self) -> str:
        """Interactive profile selection."""
        profiles = self.profile_manager.get_available_profiles()
        
        if len(profiles) == 1:
            return profiles[0]
        
        # Create menu items for profiles
        menu_items = []
        for i, profile in enumerate(profiles):
            try:
                account_info = self.profile_manager.get_account_info(profile)
                label = f"{profile:<20} (Account: {account_info.account_id})"
                menu_items.append(MenuItem(
                    label=label,
                    action=f"select_profile_{i}",
                    hotkey=str(i + 1) if i < 9 else None
                ))
            except Exception:
                menu_items.append(MenuItem(
                    label=f"{profile:<20} (Account: UNKNOWN)",
                    action=f"select_profile_{i}",
                    enabled=False
                ))
        
        # Show profile selection menu
        while True:
            self.ui.terminal.clear_screen()
            self.ui._draw_box(5, 3, self.ui.terminal.width - 10, len(menu_items) + 6, "SELECT AWS PROFILE")
            
            for i, item in enumerate(menu_items):
                y = 6 + i
                x = 8
                
                if i == self.ui.selected_index:
                    prefix = f"{self.ui.colors.menu_selected}▶ {item.label}{Color.RESET}"
                else:
                    color = self.ui.colors.menu_item if item.enabled else self.ui.colors.menu_disabled
                    prefix = f"{color}  {item.label}{Color.RESET}"
                
                self.ui.terminal.move_cursor(x, y)
                print(prefix)
            
            key = self.ui.terminal.get_key()
            
            if key == 'UP':
                self.ui.selected_index = (self.ui.selected_index - 1) % len(menu_items)
            elif key == 'DOWN':
                self.ui.selected_index = (self.ui.selected_index + 1) % len(menu_items)
            elif key == 'ENTER':
                selected_item = menu_items[self.ui.selected_index]
                if selected_item.enabled:
                    profile_index = int(selected_item.action.split('_')[-1])
                    return profiles[profile_index]
            elif key == 'ESCAPE' or key == 'CTRL_C':
                sys.exit(0)
    
    def _main_loop(self) -> None:
        """Main application loop."""
        while True:
            menu_items = self._create_main_menu()
            action = self.ui.show_main_menu(self.session, menu_items)
            
            if action == 'exit':
                break
            elif action == 'discover_resources':
                self._discover_resources()
            elif action == 'list_resources':
                self._list_resources()
            elif action == 'select_resources':
                self._select_resources()
            elif action == 'show_selected':
                self._show_selected_resources()
            elif action == 'show_dependencies':
                self._show_dependencies()
            elif action == 'dry_run':
                self._perform_dry_run()
            elif action == 'delete_resources':
                self._delete_resources()
            elif action == 'clear_selections':
                self._clear_selections()
            elif action == 'switch_profile':
                self._switch_profile()
            elif action == 'manage_services':
                self._manage_services()
            elif action == 'manage_safety':
                self._manage_safety_settings()
            elif action == 'billing_inventory':
                self._show_billing_inventory()
    
    def _create_main_menu(self) -> List[MenuItem]:
        """Create main menu items."""
        items = [
            MenuItem("🔍 Discover Resources", "discover_resources", hotkey="d"),
            MenuItem("💰 Billing Inventory", "billing_inventory", 
                    enabled=bool(self.session.resources), hotkey="b"),
            MenuItem("📋 List Resources", "list_resources", 
                    enabled=bool(self.session.resources), hotkey="l"),
            MenuItem("✅ Select Resources", "select_resources", 
                    enabled=bool(self.session.resources), hotkey="s"),
            MenuItem("👁️  Show Selected", "show_selected", 
                    enabled=bool(self.session.selected_resources), hotkey="v"),
            MenuItem("🔗 Show Dependencies", "show_dependencies", 
                    enabled=bool(self.session.resources), hotkey="p"),
            MenuItem("🧪 Dry Run Deletion", "dry_run", 
                    enabled=bool(self.session.selected_resources), hotkey="t"),
            MenuItem("🗑️  DELETE RESOURCES", "delete_resources", 
                    enabled=bool(self.session.selected_resources), hotkey="x"),
            MenuItem("🧹 Clear Selections", "clear_selections", 
                    enabled=bool(self.session.selected_resources), hotkey="c"),
            MenuItem("🔄 Switch Profile", "switch_profile", hotkey="w"),
            MenuItem("⚙️  Manage Services", "manage_services", hotkey="m"),
            MenuItem("🛡️  Safety Settings", "manage_safety", hotkey="f"),
            MenuItem("🚪 Exit", "exit", hotkey="q"),
        ]
        
        return items
    
    def _discover_resources(self) -> None:
        """Discover AWS resources."""
        try:
            self.ui.show_message("Discovering AWS resources...", "info", 1.0)
            resources = self.discovery.discover_all_resources(self.session)
            
            # Add billing information to all resources
            for resource in resources:
                if not resource.billing_info:
                    billing_info = self.billing_service.estimate_resource_cost(resource)
                    resource.billing_info = billing_info
            
            if resources:
                total_cost = sum(r.estimated_monthly_cost for r in resources)
                message = f"✅ Found {len(resources)} resources (Est. ${total_cost:.2f}/month)"
                self.ui.show_message(message, "success", 2.0)
            else:
                self.ui.show_message("No resources found.", "warning", 2.0)
        except Exception as e:
            self.ui.show_message(f"Discovery failed: {e}", "error", 3.0)
    
    def _list_resources(self) -> None:
        """List discovered resources."""
        if not self.session.resources:
            self.ui.show_message("No resources discovered yet.", "warning", 2.0)
            return
        
        # Group resources by service
        self.ui.show_resource_list(self.session.resources, self.session.selected_resources)
    
    def _select_resources(self) -> None:
        """Interactive resource selection."""
        if not self.session.resources:
            self.ui.show_message("No resources discovered yet.", "warning", 2.0)
            return
        
        while True:
            selected_index = self.ui.show_resource_list(self.session.resources, self.session.selected_resources)
            
            if selected_index is None:
                break
            
            resource = self.session.resources[selected_index]
            
            # Toggle selection
            was_selected = self.session.toggle_resource_selection(resource.identifier)
            
            if was_selected:
                self.ui.show_message(f"✅ Selected: {resource.display_name}", "success", 1.0)
            else:
                self.ui.show_message(f"❌ Deselected: {resource.display_name}", "info", 1.0)
    
    def _show_selected_resources(self) -> None:
        """Show selected resources."""
        selected = self.session.get_selected_resources()
        if not selected:
            self.ui.show_message("No resources selected.", "info", 2.0)
            return
        
        self.ui.show_resource_list(selected, self.session.selected_resources)
    
    def _show_dependencies(self) -> None:
        """Show resource dependencies."""
        if not self.session.resources:
            self.ui.show_message("No resources discovered yet.", "warning", 2.0)
            return
        
        selected_index = self.ui.show_resource_list(self.session.resources, self.session.selected_resources)
        if selected_index is not None:
            resource = self.session.resources[selected_index]
            self.ui.show_resource_details(resource)
    
    def _perform_dry_run(self) -> None:
        """Perform dry run deletion."""
        selected = self.session.get_selected_resources()
        if not selected:
            self.ui.show_message("No resources selected.", "warning", 2.0)
            return
        
        # Calculate deletion order
        deletion_order = self.discovery.get_deletion_order(selected)
        
        self.ui.terminal.clear_screen()
        self.ui._draw_box(2, 2, self.ui.terminal.width - 4, self.ui.terminal.height - 4, "DRY RUN - DELETION ORDER")
        
        messages = [
            f"🧪 DRY RUN MODE - No resources will be deleted",
            "",
            f"Deletion order for {len(deletion_order)} resources:",
            ""
        ]
        
        for i, resource in enumerate(deletion_order[:15]):  # Show first 15
            messages.append(f"{i+1:2d}. {resource.service}/{resource.resource_type}: {resource.display_name}")
        
        if len(deletion_order) > 15:
            messages.append(f"    ... and {len(deletion_order) - 15} more")
        
        messages.extend([
            "",
            "Press any key to continue..."
        ])
        
        for i, msg in enumerate(messages):
            if i < self.ui.terminal.height - 6:
                self.ui.terminal.move_cursor(5, 4 + i)
                print(f"{self.ui.colors.info}{msg}{Color.RESET}")
        
        self.ui.terminal.get_key()
    
    def _delete_resources(self) -> None:
        """Delete selected resources."""
        selected = self.session.get_selected_resources()
        if not selected:
            self.ui.show_message("No resources selected.", "warning", 2.0)
            return
        
        # Show confirmation
        if not self.ui.confirm_deletion(selected):
            self.ui.show_message("Deletion cancelled.", "info", 2.0)
            return
        
        # Calculate deletion order
        deletion_order = self.discovery.get_deletion_order(selected)
        
        # Perform deletion with progress
        def delete_callback(resource: AWSResource) -> bool:
            try:
                service = ServiceFactory.create_service(resource.service, self.discovery.aws_cmd_base)
                return service.delete_resource(resource)
            except Exception:
                return False
        
        self.ui.show_deletion_progress(deletion_order, delete_callback)
        
        # Clear selections after deletion
        self.session.selected_resources.clear()
    
    def _clear_selections(self) -> None:
        """Clear all resource selections."""
        count = len(self.session.selected_resources)
        self.session.selected_resources.clear()
        self.ui.show_message(f"Cleared {count} selections.", "success", 1.5)
    
    def _switch_profile(self) -> None:
        """Switch AWS profile."""
        try:
            new_profile = self._select_profile_interactive()
            
            if new_profile == self.session.account_info.profile:
                self.ui.show_message("Already using that profile.", "info", 1.5)
                return
            
            # Reinitialize with new profile
            self._initialize_session(new_profile)
            self.ui.show_message(f"Switched to profile: {new_profile}", "success", 2.0)
            
        except Exception as e:
            self.ui.show_message(f"Failed to switch profile: {e}", "error", 3.0)
    
    def _manage_services(self) -> None:
        """Manage service configurations."""
        # This would be a sub-menu for service management
        self.ui.show_message("Service management - Coming in next update!", "info", 2.0)
    
    def _manage_safety_settings(self) -> None:
        """Manage safety settings."""
        # This would be a sub-menu for safety settings
        self.ui.show_message("Safety settings - Coming in next update!", "info", 2.0)
    
    def _show_billing_inventory(self) -> None:
        """Show comprehensive billing inventory and cost analysis."""
        if not self.session.resources:
            self.ui.show_message("No resources discovered yet. Run discovery first.", "warning", 2.0)
            return
        
        try:
            # Generate billing report
            billing_report = self.billing_service.generate_billing_report(self.session.resources)
            
            # Show billing inventory UI
            action = self.ui.show_billing_inventory(billing_report, self.session.resources)
            
            if action == 'export_billing':
                self._export_billing_report(billing_report)
                
        except Exception as e:
            self.ui.show_message(f"Error generating billing report: {e}", "error", 3.0)
    
    def _export_billing_report(self, billing_report: dict) -> None:
        """Export billing report to file."""
        try:
            import json
            from datetime import datetime
            
            # Create export data
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'account_id': self.session.account_info.account_id,
                'profile': self.session.account_info.profile,
                'total_estimated_monthly_cost': billing_report['total_estimated_monthly_cost'],
                'summary': {
                    'total_resources': billing_report['total_resources'],
                    'billing_resources': billing_report['billing_resources'],
                    'by_service': billing_report['by_service'],
                    'by_category': billing_report['by_category']
                },
                'top_cost_resources': [
                    {
                        'service': r.service,
                        'resource_type': r.resource_type,
                        'name': r.display_name,
                        'identifier': r.identifier,
                        'region': r.region,
                        'estimated_monthly_cost': r.estimated_monthly_cost,
                        'pricing_model': r.billing_info.pricing_model if r.billing_info else 'unknown'
                    }
                    for r in billing_report['top_cost_resources']
                ]
            }
            
            # Export to file
            filename = f"aws_billing_inventory_{self.session.account_info.account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.ui.show_message(f"✅ Billing report exported to: {filename}", "success", 3.0)
            
        except Exception as e:
            self.ui.show_message(f"❌ Export failed: {e}", "error", 3.0)