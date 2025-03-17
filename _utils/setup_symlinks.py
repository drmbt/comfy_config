#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import List, Optional

def get_user_path(folder_name: str, default_path: Optional[str] = None) -> Optional[str]:
    """Get path from user with optional default."""
    if default_path:
        expanded_default = os.path.expanduser(default_path)
        prompt = f"Enter path for {folder_name} (default: {expanded_default}): "
    else:
        prompt = f"Enter path for {folder_name} (empty to skip): "
    
    response = input(prompt).strip()
    
    # If we have a default path
    if default_path:
        if response:  # User entered something
            return os.path.expanduser(response)
        return os.path.expanduser(default_path)  # User hit enter, use default
    
    # No default path
    if response:  # User entered something
        return os.path.expanduser(response)
    return None  # User hit enter with no default, skip

def setup_symlinks(comfy_path: str, **paths) -> None:
    """Set up symlinks between source directories and ComfyUI workspace."""
    if not comfy_path:
        raise ValueError("ComfyUI workspace path not provided")
    
    comfy_path = os.path.expanduser(comfy_path)
    print(f"\nSetting up symlinks for ComfyUI workspace at: {comfy_path}")
    
    # Collect all paths first
    symlinks_to_create = {}
    for folder_name, default_path in paths.items():
        source_path = get_user_path(folder_name, default_path)
        if source_path:
            symlinks_to_create[folder_name] = source_path
    
    # Create all symlinks after collecting paths
    for folder_name, source_path in symlinks_to_create.items():
        source = Path(source_path)
        
        # Handle special paths for workflows and snapshots
        if folder_name == 'workflows':
            target = Path(comfy_path) / 'user' / 'default' / 'workflows'
        elif folder_name == 'snapshots':
            target = Path(comfy_path) / 'user' / 'default' / 'ComfyUI-Manager' / 'snapshots'
        else:
            target = Path(comfy_path) / folder_name
        
        # Create parent directories if they don't exist
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Create source directory if it doesn't exist
        if not source.exists():
            print(f"Creating directory: {source}")
            source.mkdir(parents=True, exist_ok=True)
        
        # Handle existing target
        if target.exists() or target.is_symlink():
            print(f"Removing existing {target}")
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        
        print(f"Creating symlink: {target} -> {source}")
        target.symlink_to(source, target_is_directory=True)

def _setup_directory_symlinks(comfy_path: str, project_root: Path, dirs: List[str]) -> None:
    """Create symlinks for main directories."""
    for dir_name in dirs:
        target = Path(comfy_path) / dir_name
        source = project_root / dir_name
        
        # Remove existing symlink/directory
        if target.exists() or target.is_symlink():
            print(f"Removing existing {target}")
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        
        # Create symlink if source exists
        if source.is_dir():
            print(f"Creating symlink for {dir_name}")
            target.symlink_to(source, target_is_directory=True)
        else:
            print(f"Warning: Source directory {source} does not exist")

def _setup_settings_symlinks(comfy_path: str, project_root: Path) -> None:
    """Set up symlinks for settings files and workflows."""
    user_default_target = Path(comfy_path) / "user" / "default"
    user_default_source = project_root / "user" / "default"
    
    # Create target directory
    user_default_target.mkdir(parents=True, exist_ok=True)
    
    # Handle workflows directory
    workflows_source = user_default_source / "workflows"
    workflows_target = user_default_target / "workflows"
    
    if workflows_source.is_dir():
        if workflows_target.exists() or workflows_target.is_symlink():
            print(f"Removing existing {workflows_target}")
            if workflows_target.is_dir() and not workflows_target.is_symlink():
                shutil.rmtree(workflows_target)
            else:
                workflows_target.unlink()
        
        print("Creating symlink for user/default/workflows")
        workflows_target.symlink_to(workflows_source, target_is_directory=True)
    else:
        print("Warning: Workflows directory does not exist in source")
    
    # Handle settings files
    settings_files = ["comfy.settings.json", "jnodes.settings.json"]
    for settings_file in settings_files:
        source_file = user_default_source / settings_file
        target_file = user_default_target / settings_file
        
        if source_file.is_file():
            if target_file.exists() or target_file.is_symlink():
                print(f"Removing existing {target_file}")
                target_file.unlink()
            
            print(f"Creating symlink for user/default/{settings_file}")
            target_file.symlink_to(source_file)
        else:
            print(f"Warning: Settings file {settings_file} does not exist in source")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Set up symlinks between project directories and ComfyUI workspace'
    )
    
    parser.add_argument('--comfy-path', required=True, help='Path to ComfyUI workspace')
    parser.add_argument('--input', help='Path to input directory')
    parser.add_argument('--output', help='Path to output directory')
    parser.add_argument('--models', help='Path to models directory')
    parser.add_argument('--snapshots', help='Path to snapshots directory')
    parser.add_argument('--workflows', help='Path to workflows directory')
    
    return parser.parse_args()

def main():
    """Main function."""
    try:
        args = parse_args()
        # Convert args to dictionary and remove None values
        paths = {k: v for k, v in vars(args).items() if v is not None and k != 'comfy_path'}
        setup_symlinks(args.comfy_path, **paths)
        print("\nSymlink setup completed successfully!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 