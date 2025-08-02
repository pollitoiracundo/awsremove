# 🌈 AWS Resource Cleanup Tool - RETRO EDITION 🌈

```
  ██████╗ ██╗      ██████╗ ██╗   ██╗██████╗     ██████╗ ██╗     ███████╗ █████╗ ███╗   ██╗███████╗██████╗ 
 ██╔════╝ ██║     ██╔═══██╗██║   ██║██╔══██╗   ██╔════╝ ██║     ██╔════╝██╔══██╗████╗  ██║██╔════╝██╔══██╗
 ██║      ██║     ██║   ██║██║   ██║██║  ██║   ██║  ███╗██║     █████╗  ███████║██╔██╗ ██║█████╗  ██████╔╝
 ██║      ██║     ██║   ██║██║   ██║██║  ██║   ██║   ██║██║     ██╔══╝  ██╔══██║██║╚██╗██║██╔══╝  ██╔══██╗
 ╚██████╗ ███████╗╚██████╔╝╚██████╔╝██████╔╝   ╚██████╔╝███████╗███████╗██║  ██║██║ ╚████║███████╗██║  ██║
  ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝     ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝

                             ┌─── RETRO EDITION ───┐
                             │    🕹️ TOTALLY RAD 🕹️   │
                             └─────────────────────┘
```

An **epic 80s-style terminal interface** for discovering and safely cleaning up AWS resources with **arrow key navigation**, **neon colors**, and **Matrix effects**! 🚀

## ✨ Features

### 🎮 Retro Experience
- **80s-style ASCII art** and splash screens
- **Neon color schemes** (Neon, Matrix, Classic)
- **Arrow key navigation** - no more typing numbers!
- **Smooth animations** and visual effects
- **Matrix rain effect** easter eggs
- **Typewriter text effects**
- **Retro progress bars**

### 🔐 Enterprise Security
- **Multi-AWS profile support** with safety checks
- **Environment detection** (Production/Staging/Dev)
- **Service blacklisting** - protect critical services
- **Account whitelisting/blacklisting**
- **Multiple confirmation prompts**
- **Dependency-aware deletion ordering**

### 🛠️ Technical Excellence
- **Modular architecture** with clean separation of concerns
- **Factory pattern** for service discovery
- **Strategy pattern** for different color schemes
- **Observer pattern** for UI updates
- **Exception handling** with custom error types
- **Configuration management** with persistent settings

### ⚡ Supported Services
- **EC2** (Instances, Volumes)
- **S3** (Buckets)
- **RDS** (Database instances)
- **Lambda** (Functions)
- *More services coming soon!*

## 🚀 Quick Start

### Installation
```bash
# Clone and enter directory
git clone <your-repo>
cd awsremove

# Make executable
chmod +x aws_cleanup_retro.py

# Run with style!
./aws_cleanup_retro.py
```

### Usage Examples
```bash
# Basic retro experience
./aws_cleanup_retro.py

# Use Matrix color scheme
./aws_cleanup_retro.py --color-scheme matrix

# Skip splash for quick access
./aws_cleanup_retro.py --no-splash --profile dev

# Dry run mode
./aws_cleanup_retro.py --dry-run

# Specific regions only
./aws_cleanup_retro.py --regions us-east-1 us-west-2
```

## 🎨 Color Schemes

### 🌈 Neon (Default)
Bright magenta and cyan colors for that authentic 80s vibe!

### 💚 Matrix
Classic green-on-black Matrix style - "Follow the white rabbit..."

### ⚪ Classic
Traditional terminal colors for a retro computing feel

## 🎮 Controls

| Key | Action |
|-----|--------|
| `↑↓` | Navigate menus |
| `ENTER` | Select/Confirm |
| `SPACE` | Toggle selection |
| `ESC` | Back/Cancel |
| `Ctrl+C` | Emergency exit |
| `K` | Easter egg trigger 🎯 |

## 📁 Project Structure

```
awsremove/
├── src/awscleanup/
│   ├── core/                    # Core business logic
│   │   ├── models.py           # Data models and enums
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── profile_manager.py  # AWS profile management
│   │   ├── discovery.py        # Resource discovery coordination
│   │   └── application.py      # Main application controller
│   ├── services/               # AWS service handlers
│   │   ├── base.py            # Abstract base service
│   │   ├── ec2_service.py     # EC2 resource management
│   │   ├── s3_service.py      # S3 bucket management
│   │   └── service_factory.py # Service creation factory
│   ├── ui/                    # User interface components
│   │   ├── colors.py          # Color schemes and ANSI codes
│   │   ├── terminal.py        # Terminal control utilities
│   │   └── retro_ui.py        # 80s-style UI implementation
│   ├── config/                # Configuration management
│   │   └── settings.py        # Application settings
│   └── utils/                 # Utility functions
│       └── cli.py             # Command line interface
├── aws_cleanup_retro.py       # Main entry point
├── requirements.txt           # Dependencies (none!)
└── README_RETRO.md           # This file
```

## 🛡️ Safety Features

### 🔒 Account Protection
- **Protected Accounts List**: Accounts that cannot be used
- **Safe Accounts List**: Pre-approved accounts
- **Environment Detection**: Automatic prod/staging/dev detection
- **Profile Verification**: Account info displayed before proceeding

### ⚙️ Service Protection
- **Service Blacklisting**: Disable dangerous services (IAM, Route53, etc.)
- **Service Configuration**: Per-service enable/disable settings
- **Regional Restrictions**: Limit discovery to specific regions

### 🧪 Safe Testing
- **Dry Run Mode**: Preview all operations without executing
- **Dependency Analysis**: Shows what depends on what
- **Deletion Ordering**: Respects dependencies automatically
- **Multiple Confirmations**: Type "DELETE" to confirm

## 🎯 Easter Eggs

The retro edition includes several hidden features:

1. **Matrix Rain Effect**: Triggered by certain key combinations
2. **Konami Code**: Try the classic sequence! ⬆️⬆️⬇️⬇️⬅️➡️⬅️➡️
3. **Glitch Text**: Random text corruption effects
4. **Secret Messages**: Hidden in the splash screen
5. **Retro Sound Effects**: Coming soon! 🔊

## 📊 Configuration Files

The tool creates configuration files in `~/.aws/`:

- `cleanup_safety.conf`: Safe and protected accounts
- `cleanup_services.conf`: Service enable/disable settings  
- `cleanup_ui.conf`: UI preferences and color schemes

## 🎪 Advanced Features

### 🔄 Profile Switching
Switch between AWS profiles without restarting:
- Interactive profile menu
- Account verification for each profile
- Session state preservation

### 📈 Progress Tracking
- Real-time progress bars
- Deletion status indicators
- Resource counters
- Time estimates

### 🎨 Customization
- Multiple color schemes
- Configurable animations
- Adjustable effects speed
- Toggle easter eggs on/off

## 🚨 Warning

⚠️ **This tool permanently deletes AWS resources!**

- Always test with `--dry-run` first
- Verify account information carefully
- Review dependencies before deletion
- Have backups of important data
- Use appropriate IAM permissions

## 🤝 Contributing

Want to add more retro features?

1. **New Services**: Add to `src/awscleanup/services/`
2. **Color Schemes**: Add to `src/awscleanup/ui/colors.py`
3. **Visual Effects**: Add to `src/awscleanup/ui/terminal.py`
4. **Easter Eggs**: Add to `src/awscleanup/ui/retro_ui.py`

## 🎵 Soundtrack Recommendations

For the full 80s experience, play these while using the tool:

- "Take On Me" - a-ha
- "Sweet Dreams" - Eurythmics  
- "Tainted Love" - Soft Cell
- "Blue Monday" - New Order
- Any synthwave playlist! 🎹

## 📜 License

This project is open source and totally rad! 🤘

---

**Built with ❤️ and lots of neon in the terminal** 

*"Welcome to the Machine" - Pink Floyd*