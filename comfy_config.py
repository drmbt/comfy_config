#!/usr/bin/env python3
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.style import Style
from rich import print as rprint
from rich.prompt import Prompt
from rich.columns import Columns
import time
import shutil

# Load environment variables
load_dotenv()

# Create a single console instance
console = Console()

# Configure logging to use the same console
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

# Get the root directory
ROOT_DIR = Path(__file__).parent.absolute()

# At the top with other globals
start_time = None
last_step_time = None

def print_time_diff(step_name: str, is_final: bool = False):
    """Print time difference since last step and optionally total time"""
    global last_step_time, start_time
    now = time.time()
    
    # Initialize start time if not set
    if start_time is None:
        start_time = now
    
    # Print step time if we have a last step
    if last_step_time is not None:
        step_diff = now - last_step_time
        logger.info(f"{step_name} completed in {step_diff:.1f} seconds")
    
    # Print total time if this is the final step
    if is_final:
        total_time = now - start_time
        logger.info(f"Total configuration time: {total_time:.1f} seconds")
    
    last_step_time = now

def print_section(title: str):
    """Print a visually distinct section header"""
    console.print()
    console.print(Panel(
        title,
        style="bold magenta",
        border_style="magenta",
        expand=True
    ))
    console.print()

def get_user_confirmation(message: str, skip_prompt: bool = False) -> bool:
    """Get user confirmation for an action"""
    if skip_prompt:
        return True
    
    response = console.input(f"[cyan]{message}[/cyan] (Y/n): ").lower().strip()
    return response != 'n'

def check_comfy_cli_installed() -> bool:
    """Check if comfy-cli is installed and available"""
    try:
        with console.status("[bold blue]Checking for comfy-cli installation..."):
            result = subprocess.run(['comfy', '--version'], 
                                capture_output=True, 
                                text=True)
            if result.returncode == 0:
                logger.info(f"Found comfy-cli version: {result.stdout.strip()}")
            return result.returncode == 0
    except FileNotFoundError:
        return False

def install_comfy_cli(skip_prompt: bool = False) -> bool:
    """Install comfy-cli using pip"""
    if not skip_prompt:
        if not get_user_confirmation("comfy-cli not found. Would you like to install it?"):
            logger.info("User declined comfy-cli installation")
            return False
    
    try:
        with console.status("[bold blue]Installing comfy-cli..."):
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'comfy-cli'],
                                capture_output=True,
                                text=True)
            if result.returncode == 0:
                logger.info("Successfully installed comfy-cli")
                return True
            else:
                logger.error(f"Failed to install comfy-cli: {result.stderr}")
                return False
    except Exception as e:
        logger.error(f"Error installing comfy-cli: {e}")
        return False

def get_comfy_workspace() -> Optional[str]:
    """Get current ComfyUI workspace path using 'comfy which'"""
    try:
        logger.info("Checking for active ComfyUI workspace...")
        result = subprocess.run(['comfy', 'which'],
                            capture_output=True,
                            text=True)
        if result.returncode == 0:
            workspace = result.stdout.strip()
            # Extract actual path from warning message if present
            if "Target ComfyUI path:" in workspace:
                workspace = workspace.split("Target ComfyUI path:")[-1].strip()
            
            # Verify the workspace path exists and is valid
            workspace_path = Path(workspace)
            if workspace_path.exists() and (workspace_path / "main.py").exists():
                logger.info(f"Found valid workspace at: {workspace}")
                return workspace
            else:
                logger.warning(f"Found workspace configuration pointing to invalid path: {workspace}")
                return None
        
        logger.warning("No active workspace found")
        return None
    except Exception as e:
        logger.error(f"Error getting workspace: {e}")
        return None

def get_gpu_selection(skip_prompt: bool = False) -> str:
    """Get GPU selection from args, env, or user input"""
    # Check command line args first
    if '--nvidia' in sys.argv:
        logger.info("Using NVIDIA GPU (from command line args)")
        return 'nvidia'
    elif '--amd' in sys.argv:
        logger.info("Using AMD GPU (from command line args)")
        return 'amd'
    elif '--intel_arc' in sys.argv:
        logger.info("Using Intel Arc GPU (from command line args)")
        return 'intel_arc'
    
    # Check environment variabley
    default_gpu = os.getenv('DEFAULT_GPU')
    if default_gpu:
        if skip_prompt:
            logger.info(f"Using {default_gpu.upper()} (from DEFAULT_GPU environment variable)")
            return default_gpu.lower()
        else:
            # In interactive mode, use as default option
            options = ['nvidia', 'amd', 'intel_arc']
            default_idx = options.index(default_gpu.lower()) if default_gpu.lower() in options else 0
            
            console.print("What GPU do you have?")
            for i, option in enumerate(options, 1):
                prefix = '»' if i == default_idx + 1 else ' '
                console.print(f" {prefix} {option}")
            
            response = console.input("Select GPU option", prompt_suffix=" (default: 1): ").strip()
            if not response:
                return options[default_idx]
            try:
                idx = int(response) - 1
                if 0 <= idx < len(options):
                    return options[idx]
                else:
                    logger.warning(f"Invalid selection {response}, using default ({options[default_idx]})")
                    return options[default_idx]
            except ValueError:
                logger.warning(f"Invalid input {response}, using default ({options[default_idx]})")
                return options[default_idx]
    
    # No default set, prompt user in interactive mode or use nvidia as fallback
    if skip_prompt:
        logger.info("No GPU preference specified, using NVIDIA as default")
        return 'nvidia'
    else:
        options = ['nvidia', 'amd', 'intel_arc']
        console.print("\nWhat GPU do you have?")
        for i, option in enumerate(options):
            prefix = '»' if option == 'nvidia' else ' '
            console.print(f" {prefix} {option}")
        
        choice = Prompt.ask(
            "Select GPU option",
            choices=["1", "2", "3"],
            default="1"
        )
        if not choice:
            return 'nvidia'
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            else:
                logger.warning("Invalid selection, using NVIDIA as default")
                return 'nvidia'
        except ValueError:
            logger.warning("Invalid input, using NVIDIA as default")
            return 'nvidia'

def setup_default_workspace(skip_prompt: bool = False) -> Optional[str]:
    """Setup default ComfyUI workspace at ~/ComfyUI"""
    # First check if COMFY_PATH is set in environment
    comfy_path = os.getenv('COMFY_PATH')
    if comfy_path:
        path = Path(comfy_path)
        if path.exists() and (path / "main.py").exists():
            logger.info(f"Using ComfyUI path from environment: {comfy_path}")
            return comfy_path
        else:
            logger.warning(f"COMFY_PATH environment variable points to invalid path: {comfy_path}")
    
    # If no valid COMFY_PATH, check default location
    home = Path.home()
    default_path = home / 'ComfyUI'
    
    if default_path.exists():
        logger.info(f"Found existing ComfyUI installation at {default_path}")
        if not skip_prompt:
            if not get_user_confirmation(f"Would you like to set {default_path} as the default workspace?"):
                logger.info("User declined to set default workspace")
                return None
        
        try:
            logger.info(f"Setting {default_path} as default workspace...")
            subprocess.run(['comfy', 'set-default', str(default_path)], check=True)
            logger.info(f"Set {default_path} as default workspace")
            return str(default_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set default workspace: {e}")
            return None
    else:
        logger.info(f"No ComfyUI installation found at {default_path}")
        if not skip_prompt:
            if not get_user_confirmation(f"Would you like to install ComfyUI at {default_path}?"):
                logger.info("User declined ComfyUI installation")
                return None
        
        logger.info(f"Installing ComfyUI at {default_path}")
        
        # Build install command
        install_cmd = ['comfy', '--workspace', str(default_path), 'install']
        
        # Only add --skip-prompt and GPU flags if skip_prompt is true
        if skip_prompt:
            install_cmd.append('--skip-prompt')
            # Add GPU flag based on environment variable only in skip_prompt mode
            if default_gpu := os.getenv('DEFAULT_GPU'):
                if default_gpu.lower() in ['nvidia', 'amd', 'intel_arc', 'cpu']:
                    install_cmd.append(f'--{default_gpu.lower()}')
        
        # Run install command
        subprocess.run(install_cmd, check=True)
        subprocess.run(['comfy', 'set-default', str(default_path)], check=True)
        
        # Verify installation
        workspace = get_comfy_workspace()
        if workspace:
            logger.info(f"Successfully installed and configured ComfyUI at {workspace}")
            return workspace
        else:
            logger.error("Failed to verify workspace after installation")
            return None

def get_symlink_defaults() -> dict:
    """Get default symlink paths from environment variables"""
    return {
        'input': os.getenv('INPUT_DIR'),
        'output': os.getenv('OUTPUT_DIR'),
        'models': os.getenv('MODELS_DIR'),
        'snapshots': os.getenv('SNAPSHOT_DIR'),
        'workflows': os.getenv('WORKFLOW_DIR'),
    }

def get_symlink_script_path() -> Optional[Path]:
    """Get path to setup_symlinks.py script in _utils folder"""
    script_path = Path(__file__).parent / '_utils' / 'setup_symlinks.py'
    return script_path if script_path.exists() else None

def _copy_settings_files(source_dir: str, target_dir: Path) -> None:
    """Copy all JSON files from source to target directory."""
    source_path = Path(source_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    for json_file in source_path.glob('*.json'):
        target_file = target_dir / json_file.name
        if target_file.exists():
            logger.info(f"Overwriting existing {json_file.name}")
        shutil.copy2(json_file, target_file)
        logger.info(f"Copied {json_file.name}")

def copy_user_settings(workspace: str, skip_prompt: bool = False) -> None:
    """Copy user settings files to ComfyUI workspace."""
    default_settings_dir = os.getenv('USER_SETTINGS_DIR')
    target_dir = Path(workspace) / 'user' / 'default'
    
    if skip_prompt:
        if not default_settings_dir:
            logger.info("No USER_SETTINGS_DIR specified, skipping settings copy")
            return
        
        settings_dir = os.path.expanduser(default_settings_dir)
        if not Path(settings_dir).exists():
            logger.info(f"Settings directory {settings_dir} not found, skipping settings copy")
            return
        
        json_files = list(Path(settings_dir).glob('*.json'))
        if not json_files:
            logger.info(f"No JSON files found in {settings_dir}, skipping settings copy")
            return
        
        logger.info(f"Copying user settings from {settings_dir}")
        _copy_settings_files(settings_dir, target_dir)
    else:
        if default_settings_dir:
            expanded_default = os.path.expanduser(default_settings_dir)
            prompt = f"Copy user settings from (default: {expanded_default}): "
        else:
            prompt = "Copy user settings from (empty to skip): "
        
        response = input(prompt).strip()
        
        if default_settings_dir and not response:
            settings_dir = os.path.expanduser(default_settings_dir)
        elif response:
            settings_dir = os.path.expanduser(response)
        else:
            return
        
        if not Path(settings_dir).exists():
            logger.warning(f"Settings directory {settings_dir} does not exist")
            return
        
        json_files = list(Path(settings_dir).glob('*.json'))
        if not json_files:
            logger.warning(f"No JSON files found in {settings_dir}")
            return
        
        logger.info(f"Copying user settings from {settings_dir}")
        _copy_settings_files(settings_dir, target_dir)

def handle_manager_setup(workspace: str, skip_prompt: bool = False):
    """Handle ComfyUI-Manager configuration and snapshot restore."""
    manager_script = ROOT_DIR / '_utils' / 'manager_utils.py'
    if not manager_script.exists():
        logger.warning("Manager utilities script not found")
        return
    
    # Check if we have a default config and verify it exists
    manager_config = os.getenv('MANAGER_CONFIG')
    logger.info(f"MANAGER_CONFIG from env: {manager_config}")
    
    if manager_config:
        expanded_config = os.path.expanduser(manager_config)
        logger.info(f"Expanded config path: {expanded_config}")
        config_path = Path(expanded_config)
        logger.info(f"Checking if config exists at: {config_path}")
        
        if config_path.is_file():
            config_msg = f" (default config: {expanded_config})"
            logger.info("Default config file found")
        else:
            logger.warning(f"Default config specified but not found at: {expanded_config}")
            manager_config = None
            config_msg = ""
    else:
        config_msg = ""
    
    if get_user_confirmation(f"Would you like to configure ComfyUI-Manager{config_msg}?"):
        manager_args = [sys.executable, str(manager_script), '--comfy-path', workspace]
        
        # Add manager config from env or args if available
        if manager_config:
            expanded_config = os.path.expanduser(manager_config)
            manager_args.extend(['--manager-config', expanded_config])
            logger.info(f"Passing manager config path: {expanded_config}")
        
        # Add snapshot from env or args if available
        if snapshot := os.getenv('SNAPSHOT_PATH'):
            manager_args.extend(['--snapshot', snapshot])
        
        if skip_prompt:
            manager_args.append('--skip-prompt')
        
        logger.info("Launching ComfyUI-Manager configuration utility")
        # Pass the current environment to the subprocess
        subprocess.run(manager_args, env=os.environ)

def main():
    """Main entry point"""
    print_section("ComfyUI Configuration Tool")
    print_time_diff("Initialization")
    
    # Check for --skip-prompt flag
    skip_prompt = '--skip-prompt' in sys.argv
    if skip_prompt:
        logger.info("Running in non-interactive mode (--skip-prompt)")
    
    # Check if comfy-cli is installed
    print_section("Checking Dependencies")
    if not check_comfy_cli_installed():
        logger.info("comfy-cli not found, attempting to install...")
        if not install_comfy_cli(skip_prompt):
            logger.error("Failed to install comfy-cli. Exiting.")
            sys.exit(1)
        print_time_diff("comfy-cli installation")
    
    # Check for existing workspace
    print_section("Workspace Configuration")
    
    # First check if COMFY_PATH is set in environment
    comfy_path = os.getenv('COMFY_PATH')
    if not comfy_path:
        logger.info("No COMFY_PATH specified in environment")
        workspace = get_comfy_workspace()
        if not workspace:
            workspace = setup_default_workspace(skip_prompt)
            if not workspace:
                logger.error("Failed to setup default workspace. Exiting.")
                sys.exit(1)
            print_time_diff("ComfyUI installation")
    else:
        # Verify the path exists and is valid
        path = Path(comfy_path)
        if path.exists() and (path / "main.py").exists():
            logger.info(f"Using ComfyUI path from environment: {comfy_path}")
            workspace = comfy_path
        else:
            logger.warning(f"COMFY_PATH environment variable points to invalid path: {comfy_path}")
            workspace = get_comfy_workspace()
            if not workspace:
                workspace = setup_default_workspace(skip_prompt)
                if not workspace:
                    logger.error("Failed to setup default workspace. Exiting.")
                    sys.exit(1)
                print_time_diff("ComfyUI installation")
    
    # Set COMFY_PATH in environment
    os.environ['COMFY_PATH'] = workspace
    logger.info(f"Using ComfyUI workspace: {workspace}")
    
    print_section("Configuration Complete")
    print_time_diff("Final step", is_final=True)
    
    # Handle symlink configuration
    symlink_script = get_symlink_script_path()
    if not symlink_script:
        logger.warning("Symlink configuration script not found in _utils folder")
    else:
        # Get defaults from .env
        symlink_defaults = get_symlink_defaults()
        
        if skip_prompt:
            # Build args list, using command line args or .env values
            symlink_args = ['--comfy-path', workspace]
            for key, default_value in symlink_defaults.items():
                # Check for command line arg first
                arg_value = next((arg.split('=')[1] for arg in sys.argv if arg.startswith(f'--{key}=')), None)
                # If no arg provided but we have an env value, use that
                if not arg_value and default_value:
                    arg_value = default_value
                if arg_value:
                    symlink_args.extend([f'--{key}', arg_value])
            
            if len(symlink_args) > 2:  # If we have more than just comfy-path
                logger.info("Configuring symlinks with provided paths")
                subprocess.run([sys.executable, str(symlink_script)] + symlink_args)
        else:
            if get_user_confirmation("Would you like to configure symlinks for ComfyUI assets?"):
                # In interactive mode, pass .env values as defaults
                symlink_args = ['--comfy-path', workspace]
                for key, value in symlink_defaults.items():
                    if value:
                        symlink_args.extend([f'--{key}', value])
                
                logger.info("Launching symlink configuration utility")
                subprocess.run([sys.executable, str(symlink_script)] + symlink_args)
    
    # Add user settings copy prompt here
    if get_user_confirmation("Would you like to copy user settings?"):
        copy_user_settings(workspace, skip_prompt)
    
    # Handle ComfyUI-Manager setup
    print_section("ComfyUI-Manager Configuration")
    handle_manager_setup(workspace, skip_prompt)
    
    # Print exit message
    logger.info("To use ComfyUI:")
    logger.info("1. Launch ComfyUI: comfy launch")
    
    sys.exit(0)

if __name__ == "__main__":
    main() 