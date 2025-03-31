#!/bin/bash
set -e  # Exit on error

# Basic logging functions (no Python dependencies)
log_basic() {
    local level=$1
    local msg=$2
    case "$level" in
        "info")  echo -e "\033[0;32m[INFO]\033[0m $msg" ;;
        "warn")  echo -e "\033[0;33m[WARN]\033[0m $msg" ;;
        "error") echo -e "\033[0;31m[ERROR]\033[0m $msg" ;;
        "cmd")   echo -e "\033[0;34m[CMD]\033[0m $msg" ;;
        "section")
            echo
            echo -e "\033[0;35m====================================\033[0m"
            echo -e "\033[0;35m $msg \033[0m"
            echo -e "\033[0;35m====================================\033[0m"
            echo
            ;;
    esac
}

# Logging functions
log_info() { log_basic "info" "$1"; }
log_warn() { log_basic "warn" "$1"; }
log_error() { log_basic "error" "$1"; }
log_cmd() { log_basic "cmd" "$1"; }
print_section() { log_basic "section" "$1"; }

# Helper functions
get_confirmation() {
    if [[ "$*" == *"--skip-prompt"* ]]; then
        return 0
    fi
    printf "\033[0;36m%s\033[0m (Y/n): " "$1"
    read -r response
    case "$response" in
        [nN]) return 1 ;;
        *) return 0 ;;
    esac
}

check_package_installed() {
    local package=$1
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import $package" &>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Start main script execution
print_section "ComfyUI Setup Script"

# Check for --skip-prompt flag first
skip_prompt=false
for arg in "$@"; do
    if [[ $arg == "--skip-prompt" ]]; then
        skip_prompt=true
        break
    fi
done

# Load .env file first if it exists
if [ -f .env ]; then
    log_info "Loading .env file"
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and empty lines
        if [[ $line =~ ^[[:space:]]*# ]] || [[ -z $line ]]; then
            continue
        fi
        
        # Extract key and value
        key=$(echo "$line" | cut -d'=' -f1)
        value=$(echo "$line" | cut -d'=' -f2-)
        
        # Only set the value if it's not empty
        if [ -n "$value" ]; then
            export "$key=$value"
        fi
    done < .env
fi

# Check for --comfy-path argument (highest priority)
for arg in "$@"; do
    if [[ $arg == --comfy-path=* ]]; then
        export COMFY_PATH="${arg#*=}"
        break
    fi
done

# If not skipping prompts, ask for path first
if [ "$skip_prompt" = false ]; then
    # Get default path from environment or use ~/ComfyUI
    default_path="${COMFY_PATH:-$HOME/ComfyUI}"
    # Expand any ~ in the default path
    default_path=$(eval echo "$default_path")
    printf "\033[0;36mEnter ComfyUI path\033[0m (default: %s): " "$default_path"
    read -r user_input
    if [ -n "$user_input" ]; then
        export COMFY_PATH="$user_input"
    else
        export COMFY_PATH="$default_path"
    fi
elif [ -z "$COMFY_PATH" ] || [ "$COMFY_PATH" = '""' ]; then
    # If skipping prompts and no path set, use default
    export COMFY_PATH="$HOME/ComfyUI"
    log_info "Using default ComfyUI path (--skip-prompt)"
fi

# Ensure COMFY_PATH is properly expanded and not empty
if [ -z "$COMFY_PATH" ]; then
    export COMFY_PATH="$HOME"
fi
COMFY_PATH=$(eval echo "$COMFY_PATH")
COMFY_PATH="${COMFY_PATH%/}"  # Remove trailing slash if present
log_info "Using ComfyUI path: $COMFY_PATH"

# Create parent directories if they don't exist
parent_dir=$(dirname "$COMFY_PATH")
if [ ! -d "$parent_dir" ]; then
    log_info "Creating parent directory: $parent_dir"
    log_cmd "mkdir -p $parent_dir"
    mkdir -p "$parent_dir"
fi

# Setup Python environment
print_section "Python Environment Setup"

# Handle venv setup if specified or if not skipping prompts
if [ "$skip_prompt" = false ] || [[ "$*" == *"--venv"* ]]; then
    # First ask if we want to create a venv
    if [ "$skip_prompt" = false ]; then
        if ! get_confirmation "Do you want to create a virtual environment?"; then
            log_info "Skipping virtual environment creation"
            exit 0
        fi
    fi
    
    # Get venv name from args or prompt
    venv_name="venv"
    for arg in "$@"; do
        if [[ $arg == --venv=* ]]; then
            venv_name="${arg#*=}"
            break
        fi
    done
    
    if [ "$skip_prompt" = false ] && [ "$venv_name" = "venv" ]; then
        printf "\033[0;36mEnter virtual environment name\033[0m (default: venv): "
        read -r user_input
        if [ -n "$user_input" ]; then
            venv_name="$user_input"
        fi
    fi
    
    # Create venv in the same directory as COMFY_PATH
    venv_path="$COMFY_PATH/$venv_name"
    
    # Check if venv exists
    if [ -d "$venv_path" ] && [ -f "$venv_path/bin/activate" ]; then
        log_info "Found existing virtual environment at: $venv_path"
    else
        log_info "Creating new virtual environment at: $venv_path"
        log_cmd "python -m venv $venv_path"
        python -m venv "$venv_path"
    fi
    
    log_info "Activating virtual environment"
    log_cmd "source $venv_path/bin/activate"
    source "$venv_path/bin/activate"
    
    # Verify activation
    if [ -n "$VIRTUAL_ENV" ]; then
        log_info "Successfully activated virtual environment: $venv_path"
    else
        log_error "Failed to activate virtual environment: $venv_path"
        exit 1
    fi
else
    # Only reach here if --skip-prompt is used without specifying an environment
    log_info "Proceeding without virtual environment (--skip-prompt)"
fi

# Now that we have our environment (if specified), check requirements
print_section "Installing Requirements"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    log_error "requirements.txt not found"
    exit 1
fi

# Install requirements
log_info "Installing requirements"
log_cmd "python -m pip install -r requirements.txt"
python -m pip install -r requirements.txt

# Run comfy_config.py
print_section "Running Configuration Script"
log_info "Running comfy_config.py"
log_cmd "python comfy_config.py $@"
python comfy_config.py "$@" 