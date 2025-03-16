#!/usr/bin/env python3
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the root directory
ROOT_DIR = Path(__file__).parent.absolute()

def get_user_confirmation(message: str, skip_prompt: bool = False) -> bool:
    """Get user confirmation for an action"""
    if skip_prompt:
        return True
    
    response = input(f"{message} (y/N): ").lower().strip()
    return response == 'y'

def check_comfy_cli_installed() -> bool:
    """Check if comfy-cli is installed and available"""
    try:
        result = subprocess.run(['comfy', '--version'], 
                              capture_output=True, 
                              text=True)
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
        logger.info("Installing comfy-cli...")
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
        result = subprocess.run(['comfy', 'which'],
                              capture_output=True,
                              text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception as e:
        logger.error(f"Error getting workspace: {e}")
        return None

def setup_default_workspace(skip_prompt: bool = False) -> Optional[str]:
    """Setup default ComfyUI workspace at ~/ComfyUI"""
    home = Path.home()
    default_path = home / 'ComfyUI'
    
    # Check if ~/ComfyUI exists
    if default_path.exists():
        logger.info(f"Found existing ComfyUI installation at {default_path}")
        if not skip_prompt:
            if not get_user_confirmation(f"Would you like to set {default_path} as the default workspace?"):
                logger.info("User declined to set default workspace")
                return None
        
        try:
            # Set as default workspace
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
        try:
            # Install ComfyUI with --skip-prompt
            subprocess.run(['comfy', '--workspace', str(default_path), '--skip-prompt', 'install', '--nvidia'], check=True)
            # Set as default
            subprocess.run(['comfy', 'set-default', str(default_path)], check=True)
            # Verify installation
            workspace = get_comfy_workspace()
            if workspace:
                logger.info(f"Successfully installed and configured ComfyUI at {workspace}")
                return workspace
            else:
                logger.error("Failed to verify workspace after installation")
                return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install ComfyUI: {e}")
            return None

def main():
    """Main entry point"""
    # Check for --skip-prompt flag
    skip_prompt = '--skip-prompt' in sys.argv
    
    # Check if comfy-cli is installed
    if not check_comfy_cli_installed():
        logger.info("comfy-cli not found, attempting to install...")
        if not install_comfy_cli(skip_prompt):
            logger.error("Failed to install comfy-cli. Exiting.")
            sys.exit(1)
    
    # Check for existing workspace
    workspace = get_comfy_workspace()
    if not workspace:
        logger.info("No active workspace found, attempting to setup default workspace...")
        workspace = setup_default_workspace(skip_prompt)
        if not workspace:
            logger.error("Failed to setup default workspace. Exiting.")
            sys.exit(1)
    
    logger.info(f"Using ComfyUI workspace: {workspace}")
    os.environ['COMFY_PATH'] = workspace
    
    # Temporary exit for debugging
    logger.info("DEBUG: Initialization complete. Exiting for debug purposes.")
    sys.exit(0)
    
    # The rest of the script will be added back later
    # ... (ConfigManager and other functionality) ...

if __name__ == "__main__":
    main() 