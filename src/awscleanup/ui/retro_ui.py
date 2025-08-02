"""
80s-style retro terminal user interface.
"""

import time
import random
from typing import List, Optional, Callable, Any, Dict
from .colors import Color, get_color_scheme
from .terminal import Terminal, RetroEffects
from ..core.models import MenuItem, AWSResource, CleanupSession, EnvironmentType


class RetroUI:
    """80s-style terminal user interface."""
    
    def __init__(self, color_scheme: str = "neon"):
        self.terminal = Terminal()
        self.colors = get_color_scheme(color_scheme)
        self.selected_index = 0
        self.easter_egg_triggered = False
        
    def show_splash_screen(self):
        """Show awesome 80s splash screen."""
        self.terminal.clear_screen()
        self.terminal.hide_cursor()
        
        # ASCII art logo
        logo = [
            "  ██████╗ ██╗      ██████╗ ██╗   ██╗██████╗     ██████╗ ██╗     ███████╗ █████╗ ███╗   ██╗███████╗██████╗ ",
            " ██╔════╝ ██║     ██╔═══██╗██║   ██║██╔══██╗   ██╔════╝ ██║     ██╔════╝██╔══██╗████╗  ██║██╔════╝██╔══██╗",
            " ██║      ██║     ██║   ██║██║   ██║██║  ██║   ██║  ███╗██║     █████╗  ███████║██╔██╗ ██║█████╗  ██████╔╝",
            " ██║      ██║     ██║   ██║██║   ██║██║  ██║   ██║   ██║██║     ██╔══╝  ██╔══██║██║╚██╗██║██╔══╝  ██╔══██╗",
            " ╚██████╗ ███████╗╚██████╔╝╚██████╔╝██████╔╝   ╚██████╔╝███████╗███████╗██║  ██║██║ ╚████║███████╗██║  ██║",
            "  ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝     ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝",
            "",
            "                                    ┌─── AWS RESOURCE CLEANUP TOOL ───┐",
            "                                    │        RETRO EDITION           │",
            "                                    └─────────────────────────────────┘"
        ]
        
        # Center and display logo with effects
        width = self.terminal.width
        height = self.terminal.height
        
        start_y = max(1, (height - len(logo)) // 2 - 3)
        
        for i, line in enumerate(logo):
            self.terminal.move_cursor((width - len(line)) // 2, start_y + i)
            if i < len(logo) - 3:
                print(f"{self.colors.header}{line}{Color.RESET}")
            else:
                print(f"{self.colors.accent}{line}{Color.RESET}")
            time.sleep(0.1)
        
        # Add some retro flavor text
        flavor_texts = [
            "⚡ INITIALIZING QUANTUM FLUX CAPACITORS ⚡",
            "🌐 CONNECTING TO THE MAINFRAME 🌐",
            "🔥 LOADING CYBER PROTOCOLS 🔥",
            "✨ SYNCING WITH THE MATRIX ✨"
        ]
        
        flavor = random.choice(flavor_texts)
        self.terminal.move_cursor((width - len(flavor)) // 2, start_y + len(logo) + 2)
        RetroEffects.typewriter_print(f"{self.colors.info}{flavor}{Color.RESET}")
        
        time.sleep(1.5)
        self.terminal.show_cursor()
    
    def show_main_menu(self, session: CleanupSession, menu_items: List[MenuItem]) -> str:
        """Show main menu with arrow key navigation."""
        while True:
            self._draw_main_menu(session, menu_items)
            
            key = self.terminal.get_key()
            
            if key == 'UP':
                self.selected_index = (self.selected_index - 1) % len(menu_items)
            elif key == 'DOWN':
                self.selected_index = (self.selected_index + 1) % len(menu_items)
            elif key == 'ENTER' or key == ' ':
                selected_item = menu_items[self.selected_index]
                if selected_item.enabled:
                    return selected_item.action
            elif key == 'CTRL_C' or key == 'CTRL_Q' or key == 'ESCAPE':
                return 'exit'
            elif key.lower() == 'k' and session.account_info and not self.easter_egg_triggered:
                # Konami code easter egg trigger
                if self._check_konami_sequence():
                    self._trigger_easter_egg()
                    self.easter_egg_triggered = True
            
            # Handle hotkeys
            for i, item in enumerate(menu_items):
                if item.hotkey and key.lower() == item.hotkey.lower() and item.enabled:
                    self.selected_index = i
                    return item.action
    
    def _draw_main_menu(self, session: CleanupSession, menu_items: List[MenuItem]):
        """Draw the main menu interface."""
        self.terminal.clear_screen()
        width = self.terminal.width
        
        # Header
        self._draw_header(session)
        
        # Menu box
        menu_start_y = 8
        self._draw_box(5, menu_start_y, width - 10, len(menu_items) + 4, "MAIN MENU")
        
        # Menu items
        for i, item in enumerate(menu_items):
            y = menu_start_y + 2 + i
            x = 8
            
            if i == self.selected_index:
                # Selected item
                prefix = f"{self.colors.menu_selected}▶ {item.label} {Color.RESET}"
                if item.hotkey:
                    prefix += f" {self.colors.accent}[{item.hotkey}]{Color.RESET}"
            else:
                # Regular item
                color = self.colors.menu_item if item.enabled else self.colors.menu_disabled
                prefix = f"{color}  {item.label}{Color.RESET}"
                if item.hotkey:
                    prefix += f" {self.colors.accent}[{item.hotkey}]{Color.RESET}"
            
            self.terminal.move_cursor(x, y)
            print(prefix)
        
        # Footer with controls
        footer_y = menu_start_y + len(menu_items) + 6
        controls = [
            "↑↓ Navigate", "ENTER Select", "ESC Exit", "Ctrl+C Quit"
        ]
        
        control_text = " | ".join(controls)
        self.terminal.move_cursor((width - len(control_text)) // 2, footer_y)
        print(f"{self.colors.info}{control_text}{Color.RESET}")
    
    def _draw_header(self, session: CleanupSession):
        """Draw the header with account information."""
        width = self.terminal.width
        
        # Title bar
        title = "═══ CLOUD CLEANER - RETRO EDITION ═══"
        self.terminal.move_cursor((width - len(title)) // 2, 2)
        print(f"{self.colors.header}{title}{Color.RESET}")
        
        if session.account_info:
            # Account info
            account = session.account_info
            env_indicator = self._get_environment_indicator(account.environment_type)
            
            info_lines = [
                f"Profile: {account.profile}",
                f"Account: {account.account_id} {env_indicator}",
                f"Region: {account.region}",
                f"Resources: {len(session.resources)} discovered, {len(session.selected_resources)} selected"
            ]
            
            for i, line in enumerate(info_lines):
                self.terminal.move_cursor(3, 4 + i)
                print(f"{self.colors.info}{line}{Color.RESET}")
    
    def _draw_box(self, x: int, y: int, width: int, height: int, title: str = ""):
        """Draw a retro-style box."""
        # Top border
        self.terminal.move_cursor(x, y)
        top_line = "╔" + "═" * (width - 2) + "╗"
        if title:
            title_pos = (width - len(title) - 4) // 2
            top_line = top_line[:title_pos] + f"╣ {title} ╠" + top_line[title_pos + len(title) + 4:]
        print(f"{self.colors.border}{top_line}{Color.RESET}")
        
        # Side borders
        for i in range(1, height - 1):
            self.terminal.move_cursor(x, y + i)
            print(f"{self.colors.border}║{Color.RESET}" + " " * (width - 2) + f"{self.colors.border}║{Color.RESET}")
        
        # Bottom border
        self.terminal.move_cursor(x, y + height - 1)
        print(f"{self.colors.border}╚" + "═" * (width - 2) + "╝{Color.RESET}")
    
    def _get_environment_indicator(self, env_type: EnvironmentType) -> str:
        """Get visual indicator for environment type."""
        indicators = {
            EnvironmentType.PRODUCTION: f"{self.colors.error}🔴 PRODUCTION{Color.RESET}",
            EnvironmentType.STAGING: f"{self.colors.warning}🟡 STAGING{Color.RESET}",
            EnvironmentType.DEVELOPMENT: f"{self.colors.success}🟢 DEV{Color.RESET}",
            EnvironmentType.TESTING: f"{self.colors.info}🔵 TEST{Color.RESET}",
            EnvironmentType.PROTECTED: f"{self.colors.error}🔒 PROTECTED{Color.RESET}",
            EnvironmentType.SAFE: f"{self.colors.success}✅ SAFE{Color.RESET}",
            EnvironmentType.UNKNOWN: f"{self.colors.warning}⚠️ UNKNOWN{Color.RESET}"
        }
        return indicators.get(env_type, "❓ UNCLASSIFIED")
    
    def show_resource_list(self, resources: List[AWSResource], selected_resources: set) -> Optional[int]:
        """Show resource list with selection interface."""
        if not resources:
            self.show_message("No resources found!", "info")
            return None
        
        page_size = self.terminal.height - 10
        current_page = 0
        max_pages = (len(resources) - 1) // page_size + 1
        selected_index = 0
        
        while True:
            self.terminal.clear_screen()
            
            # Header
            title = f"RESOURCES (Page {current_page + 1}/{max_pages})"
            self._draw_box(2, 2, self.terminal.width - 4, self.terminal.height - 4, title)
            
            # Resource list
            start_idx = current_page * page_size
            end_idx = min(start_idx + page_size, len(resources))
            
            for i in range(start_idx, end_idx):
                resource = resources[i]
                y = 4 + (i - start_idx)
                x = 5
                
                # Selection indicator
                if resource.identifier in selected_resources:
                    status = f"{self.colors.warning}[SELECTED]{Color.RESET}"
                else:
                    status = ""
                
                # Highlight current selection
                if i == selected_index:
                    line = f"{self.colors.menu_selected}▶ {resource.service:<10} {resource.resource_type:<15} {resource.display_name[:30]:<30} {resource.region:<15} {status}{Color.RESET}"
                else:
                    line = f"  {resource.service:<10} {resource.resource_type:<15} {resource.display_name[:30]:<30} {resource.region:<15} {status}"
                
                self.terminal.move_cursor(x, y)
                print(line)
            
            # Controls
            controls = ["↑↓ Navigate", "SPACE Select", "ENTER Details", "ESC Back", "PgUp/PgDn Pages"]
            control_text = " | ".join(controls)
            self.terminal.move_cursor(5, self.terminal.height - 2)
            print(f"{self.colors.info}{control_text}{Color.RESET}")
            
            # Handle input
            key = self.terminal.get_key()
            
            if key == 'UP':
                selected_index = max(0, selected_index - 1)
                if selected_index < start_idx:
                    current_page = max(0, current_page - 1)
            elif key == 'DOWN':
                selected_index = min(len(resources) - 1, selected_index + 1)
                if selected_index >= end_idx:
                    current_page = min(max_pages - 1, current_page + 1)
            elif key == 'SPACE':
                return selected_index
            elif key == 'ENTER':
                self.show_resource_details(resources[selected_index])
            elif key == 'ESCAPE':
                return None
            elif key in ['PAGE_UP', 'b']:
                current_page = max(0, current_page - 1)
                selected_index = current_page * page_size
            elif key in ['PAGE_DOWN', 'f']:
                current_page = min(max_pages - 1, current_page + 1)
                selected_index = current_page * page_size
    
    def show_resource_details(self, resource: AWSResource):
        """Show detailed resource information."""
        self.terminal.clear_screen()
        
        title = f"RESOURCE DETAILS: {resource.display_name}"
        self._draw_box(2, 2, self.terminal.width - 4, self.terminal.height - 4, title)
        
        details = [
            f"Service: {resource.service}",
            f"Type: {resource.resource_type}",
            f"Identifier: {resource.identifier}",
            f"Name: {resource.name}",
            f"Region: {resource.region}",
            f"State: {resource.state.value}",
            "",
            "Dependencies:",
        ]
        
        if resource.dependencies:
            for dep in resource.dependencies:
                details.append(f"  → {dep}")
        else:
            details.append("  None")
        
        details.append("")
        details.append("Dependents:")
        
        if resource.dependents:
            for dep in resource.dependents:
                details.append(f"  ← {dep}")
        else:
            details.append("  None")
        
        if resource.metadata:
            details.append("")
            details.append("Metadata:")
            for key, value in resource.metadata.items():
                details.append(f"  {key}: {value}")
        
        for i, line in enumerate(details):
            if i < self.terminal.height - 6:
                self.terminal.move_cursor(5, 4 + i)
                print(f"{self.colors.info}{line}{Color.RESET}")
        
        self.terminal.move_cursor(5, self.terminal.height - 2)
        print(f"{self.colors.info}Press any key to continue...{Color.RESET}")
        
        self.terminal.get_key()
    
    def show_message(self, message: str, msg_type: str = "info", duration: float = 2.0):
        """Show a message box."""
        color_map = {
            "info": self.colors.info,
            "success": self.colors.success,
            "warning": self.colors.warning,
            "error": self.colors.error
        }
        
        color = color_map.get(msg_type, self.colors.info)
        
        # Simple message display
        self.terminal.clear_screen()
        
        lines = message.split('\n')
        max_length = max(len(line) for line in lines)
        box_width = min(self.terminal.width - 4, max_length + 4)
        box_height = len(lines) + 4
        
        x = (self.terminal.width - box_width) // 2
        y = (self.terminal.height - box_height) // 2
        
        self._draw_box(x, y, box_width, box_height, msg_type.upper())
        
        for i, line in enumerate(lines):
            self.terminal.move_cursor(x + 2, y + 2 + i)
            print(f"{color}{line}{Color.RESET}")
        
        time.sleep(duration)
    
    def _check_konami_sequence(self) -> bool:
        """Check for Konami code easter egg (simplified)."""
        return random.random() < 0.1  # 10% chance for demo
    
    def _trigger_easter_egg(self):
        """Trigger the easter egg."""
        self.terminal.clear_screen()
        
        # Matrix rain effect
        RetroEffects.matrix_rain(self.terminal.width, self.terminal.height, 3.0)
        
        # Show easter egg message
        messages = [
            "🎮 KONAMI CODE DETECTED! 🎮",
            "",
            "WELCOME TO THE MATRIX, NEO...",
            "",
            "You have unlocked the secret retro mode!",
            "All your base are belong to us.",
            "",
            "Press any key to continue..."
        ]
        
        self.terminal.clear_screen()
        width = self.terminal.width
        height = self.terminal.height
        
        start_y = (height - len(messages)) // 2
        
        for i, msg in enumerate(messages):
            self.terminal.move_cursor((width - len(msg)) // 2, start_y + i)
            print(f"{self.colors.success}{msg}{Color.RESET}")
        
        self.terminal.get_key()
    
    def confirm_deletion(self, resources: List[AWSResource]) -> bool:
        """Show deletion confirmation dialog."""
        self.terminal.clear_screen()
        
        title = "⚠️ CONFIRM DELETION ⚠️"
        self._draw_box(5, 5, self.terminal.width - 10, self.terminal.height - 10, title)
        
        messages = [
            f"You are about to DELETE {len(resources)} AWS resources!",
            "",
            "This action CANNOT be undone!",
            "",
            "Resources to be deleted:",
            ""
        ]
        
        # Show first few resources
        for i, resource in enumerate(resources[:10]):
            messages.append(f"  • {resource.service}/{resource.resource_type}: {resource.display_name}")
        
        if len(resources) > 10:
            messages.append(f"  ... and {len(resources) - 10} more")
        
        messages.extend([
            "",
            "Type 'DELETE' to confirm, or ESC to cancel:"
        ])
        
        for i, msg in enumerate(messages):
            if i < self.terminal.height - 12:
                self.terminal.move_cursor(7, 7 + i)
                if "DELETE" in msg or "CANNOT" in msg:
                    print(f"{self.colors.error}{msg}{Color.RESET}")
                else:
                    print(f"{self.colors.info}{msg}{Color.RESET}")
        
        # Get confirmation
        self.terminal.move_cursor(7, 7 + len(messages))
        self.terminal.show_cursor()
        
        confirmation = ""
        while True:
            key = self.terminal.get_key()
            
            if key == 'ESCAPE':
                return False
            elif key == 'ENTER':
                return confirmation == "DELETE"
            elif key == 'BACKSPACE':
                if confirmation:
                    confirmation = confirmation[:-1]
                    self.terminal.move_cursor(7, 7 + len(messages))
                    print(" " * 20)
                    self.terminal.move_cursor(7, 7 + len(messages))
                    print(f"{self.colors.warning}{confirmation}{Color.RESET}")
            elif key.isalpha():
                confirmation += key.upper()
                self.terminal.move_cursor(7, 7 + len(messages))
                print(f"{self.colors.warning}{confirmation}{Color.RESET}")
    
    def show_deletion_progress(self, resources: List[AWSResource], callback: Callable[[AWSResource], bool]):
        """Show deletion progress with retro progress bar."""
        self.terminal.clear_screen()
        self.terminal.hide_cursor()
        
        title = "DELETION IN PROGRESS"
        self._draw_box(5, 5, self.terminal.width - 10, 15, title)
        
        total = len(resources)
        
        for i, resource in enumerate(resources):
            # Progress bar
            progress = (i + 1) / total
            bar_width = self.terminal.width - 20
            filled = int(bar_width * progress)
            
            self.terminal.move_cursor(7, 8)
            print(f"{self.colors.info}Progress: {i + 1}/{total}{Color.RESET}")
            
            self.terminal.move_cursor(7, 10)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(f"{self.colors.success}[{bar}] {progress:.1%}{Color.RESET}")
            
            # Current resource
            self.terminal.move_cursor(7, 12)
            print(f"{self.colors.info}Deleting: {resource.service}/{resource.resource_type}{Color.RESET}")
            self.terminal.move_cursor(7, 13)
            print(f"{self.colors.info}Name: {resource.display_name[:50]}{Color.RESET}")
            
            # Delete resource
            success = callback(resource)
            
            # Show result
            self.terminal.move_cursor(7, 15)
            if success:
                print(f"{self.colors.success}✓ Successfully deleted{Color.RESET}")
            else:
                print(f"{self.colors.error}✗ Failed to delete{Color.RESET}")
            
            time.sleep(0.5)
        
        self.terminal.move_cursor(7, 17)
        print(f"{self.colors.success}Deletion complete! Press any key to continue...{Color.RESET}")
        self.terminal.show_cursor()
        self.terminal.get_key()
    
    def show_billing_inventory(self, billing_report: Dict, resources: List['AWSResource']) -> Optional[str]:
        """Show comprehensive billing inventory with retro styling."""
        while True:
            self.terminal.clear_screen()
            
            # Header
            title = f"💰 BILLING INVENTORY - TOTAL: ${billing_report['total_estimated_monthly_cost']:.2f}/month"
            self._draw_box(2, 2, self.terminal.width - 4, self.terminal.height - 4, title)
            
            # Summary stats
            y = 4
            stats = [
                f"Total Resources: {billing_report['total_resources']}",
                f"Billing Resources: {billing_report['billing_resources']}",
                f"Estimated Monthly Cost: ${billing_report['total_estimated_monthly_cost']:.2f}",
                ""
            ]
            
            for stat in stats:
                self.terminal.move_cursor(5, y)
                print(f"{self.colors.info}{stat}{Color.RESET}")
                y += 1
            
            # Cost by service
            y += 1
            self.terminal.move_cursor(5, y)
            print(f"{self.colors.accent}COST BY SERVICE:{Color.RESET}")
            y += 1
            
            for service, data in sorted(billing_report['by_service'].items(), 
                                      key=lambda x: x[1]['cost'], reverse=True):
                self.terminal.move_cursor(7, y)
                cost_bar = self._create_cost_bar(data['cost'], billing_report['total_estimated_monthly_cost'], 30)
                print(f"{self.colors.success}{service.upper():<12} ${data['cost']:>8.2f} {cost_bar} ({data['count']} resources){Color.RESET}")
                y += 1
                if y >= self.terminal.height - 8:
                    break
            
            # Cost by category
            y += 2
            if y < self.terminal.height - 6:
                self.terminal.move_cursor(5, y)
                print(f"{self.colors.accent}COST BY CATEGORY:{Color.RESET}")
                y += 1
                
                for category, cost in sorted(billing_report['by_category'].items(), 
                                           key=lambda x: x[1], reverse=True):
                    self.terminal.move_cursor(7, y)
                    cost_bar = self._create_cost_bar(cost, billing_report['total_estimated_monthly_cost'], 20)
                    print(f"{self.colors.warning}{category:<12} ${cost:>8.2f} {cost_bar}{Color.RESET}")
                    y += 1
                    if y >= self.terminal.height - 4:
                        break
            
            # Controls
            controls = ["1 Detailed View", "2 Top Costs", "3 Export", "ESC Back"]
            control_text = " | ".join(controls)
            self.terminal.move_cursor(5, self.terminal.height - 2)
            print(f"{self.colors.info}{control_text}{Color.RESET}")
            
            # Handle input
            key = self.terminal.get_key()
            
            if key == '1':
                self._show_detailed_billing_view(billing_report, resources)
            elif key == '2':
                self._show_top_cost_resources(billing_report['top_cost_resources'])
            elif key == '3':
                return 'export_billing'
            elif key == 'ESCAPE':
                return None
    
    def _create_cost_bar(self, cost: float, max_cost: float, width: int) -> str:
        """Create a visual cost bar."""
        if max_cost == 0:
            return "░" * width
        
        filled = int((cost / max_cost) * width)
        return "█" * filled + "░" * (width - filled)
    
    def _show_detailed_billing_view(self, billing_report: Dict, resources: List['AWSResource']):
        """Show detailed billing information for each resource."""
        billing_resources = [r for r in resources if r.generates_cost]
        
        if not billing_resources:
            self.show_message("No resources with billing information found.", "info", 2.0)
            return
        
        # Sort by cost descending
        billing_resources.sort(key=lambda r: r.estimated_monthly_cost, reverse=True)
        
        page_size = self.terminal.height - 12
        current_page = 0
        max_pages = (len(billing_resources) - 1) // page_size + 1
        selected_index = 0
        
        while True:
            self.terminal.clear_screen()
            
            title = f"DETAILED BILLING VIEW (Page {current_page + 1}/{max_pages})"
            self._draw_box(2, 2, self.terminal.width - 4, self.terminal.height - 4, title)
            
            # Column headers
            self.terminal.move_cursor(5, 4)
            print(f"{self.colors.accent}{'SERVICE':<12} {'TYPE':<20} {'NAME':<25} {'MONTHLY COST':<15} {'MODEL':<12}{Color.RESET}")
            self.terminal.move_cursor(5, 5)
            print(f"{self.colors.border}{'-' * (self.terminal.width - 10)}{Color.RESET}")
            
            # Resource list
            start_idx = current_page * page_size
            end_idx = min(start_idx + page_size, len(billing_resources))
            
            for i in range(start_idx, end_idx):
                resource = billing_resources[i]
                y = 6 + (i - start_idx)
                x = 5
                
                billing = resource.billing_info
                cost_str = f"${resource.estimated_monthly_cost:.2f}"
                model = billing.pricing_model if billing else "unknown"
                
                if i == selected_index:
                    line = f"{self.colors.menu_selected}▶ {resource.service:<11} {resource.resource_type:<19} {resource.display_name[:24]:<24} {cost_str:<15} {model:<12}{Color.RESET}"
                else:
                    # Color code by cost level
                    if resource.estimated_monthly_cost > 100:
                        color = self.colors.error
                    elif resource.estimated_monthly_cost > 10:
                        color = self.colors.warning
                    else:
                        color = self.colors.success
                    
                    line = f"{color}  {resource.service:<11} {resource.resource_type:<19} {resource.display_name[:24]:<24} {cost_str:<15} {model:<12}{Color.RESET}"
                
                self.terminal.move_cursor(x, y)
                print(line)
            
            # Summary
            summary_y = self.terminal.height - 6
            self.terminal.move_cursor(5, summary_y)
            page_total = sum(r.estimated_monthly_cost for r in billing_resources[start_idx:end_idx])
            print(f"{self.colors.info}Page Total: ${page_total:.2f} | Overall Total: ${billing_report['total_estimated_monthly_cost']:.2f}{Color.RESET}")
            
            # Controls
            controls = ["↑↓ Navigate", "ENTER Details", "PgUp/PgDn Pages", "ESC Back"]
            control_text = " | ".join(controls)
            self.terminal.move_cursor(5, self.terminal.height - 2)
            print(f"{self.colors.info}{control_text}{Color.RESET}")
            
            # Handle input
            key = self.terminal.get_key()
            
            if key == 'UP':
                selected_index = max(0, selected_index - 1)
                if selected_index < start_idx:
                    current_page = max(0, current_page - 1)
            elif key == 'DOWN':
                selected_index = min(len(billing_resources) - 1, selected_index + 1)
                if selected_index >= end_idx:
                    current_page = min(max_pages - 1, current_page + 1)
            elif key == 'ENTER':
                if selected_index < len(billing_resources):
                    self._show_resource_billing_details(billing_resources[selected_index])
            elif key == 'ESCAPE':
                break
            elif key in ['PAGE_UP', 'b']:
                current_page = max(0, current_page - 1)
                selected_index = current_page * page_size
            elif key in ['PAGE_DOWN', 'f']:
                current_page = min(max_pages - 1, current_page + 1)
                selected_index = current_page * page_size
    
    def _show_top_cost_resources(self, top_resources: List['AWSResource']):
        """Show top cost resources."""
        self.terminal.clear_screen()
        
        title = f"TOP {len(top_resources)} MOST EXPENSIVE RESOURCES"
        self._draw_box(2, 2, self.terminal.width - 4, self.terminal.height - 4, title)
        
        for i, resource in enumerate(top_resources[:15]):  # Show top 15
            y = 4 + i
            cost = f"${resource.estimated_monthly_cost:.2f}/month"
            
            # Color by cost level
            if resource.estimated_monthly_cost > 100:
                color = self.colors.error
            elif resource.estimated_monthly_cost > 10:
                color = self.colors.warning
            else:
                color = self.colors.success
            
            self.terminal.move_cursor(5, y)
            print(f"{color}{i+1:2d}. {resource.service}/{resource.resource_type:<20} {resource.display_name[:30]:<30} {cost}{Color.RESET}")
        
        if len(top_resources) > 15:
            self.terminal.move_cursor(5, 20)
            remaining_cost = sum(r.estimated_monthly_cost for r in top_resources[15:])
            print(f"{self.colors.info}... and {len(top_resources) - 15} more resources (${remaining_cost:.2f}/month){Color.RESET}")
        
        self.terminal.move_cursor(5, self.terminal.height - 2)
        print(f"{self.colors.info}Press any key to continue...{Color.RESET}")
        
        self.terminal.get_key()
    
    def _show_resource_billing_details(self, resource: 'AWSResource'):
        """Show detailed billing information for a specific resource."""
        self.terminal.clear_screen()
        
        title = f"BILLING DETAILS: {resource.display_name}"
        self._draw_box(2, 2, self.terminal.width - 4, self.terminal.height - 4, title)
        
        billing = resource.billing_info
        if not billing:
            self.terminal.move_cursor(5, 4)
            print(f"{self.colors.warning}No billing information available for this resource.{Color.RESET}")
            self.terminal.get_key()
            return
        
        details = [
            f"Service: {resource.service.upper()}",
            f"Resource Type: {resource.resource_type}",
            f"Identifier: {resource.identifier}",
            f"Region: {resource.region}",
            "",
            f"Estimated Monthly Cost: {billing.formatted_cost}",
            f"Pricing Model: {billing.pricing_model}",
            f"Billing Unit: {billing.billing_unit}",
            f"Cost Categories: {', '.join(billing.cost_categories)}",
            ""
        ]
        
        if billing.usage_metrics:
            details.append("Usage Metrics:")
            for key, value in billing.usage_metrics.items():
                details.append(f"  {key}: {value}")
        
        for i, line in enumerate(details):
            if i < self.terminal.height - 6:
                self.terminal.move_cursor(5, 4 + i)
                if "Monthly Cost" in line:
                    print(f"{self.colors.accent}{line}{Color.RESET}")
                else:
                    print(f"{self.colors.info}{line}{Color.RESET}")
        
        self.terminal.move_cursor(5, self.terminal.height - 2)
        print(f"{self.colors.info}Press any key to continue...{Color.RESET}")
        
        self.terminal.get_key()