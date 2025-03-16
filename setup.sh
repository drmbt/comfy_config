#!/bin/bash
set -e  # Exit on error

# Colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get user confirmation
get_confirmation() {
    if [[ "$*" == *"--skip-prompt"* ]]; then
        return 0
    fi
    
    read -p "$1 (y/N): " response
    case "$response" in
        [yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# Function to get user choice
get_user_choice() {
    local prompt=$1
    local options=("${@:2}")
    
    if [[ "$*" == *"--skip-prompt"* ]]; then
        echo "none"
        return
    fi
    
    echo "$prompt"
    select opt in "${options[@]}"; do
        case $opt in
            *) echo "$opt"; break ;;
        esac
    done
}

# Function to check if a Python package is installed
check_package_installed() {
    local package=$1
    if python -c "import pkg_resources; pkg_resources.require('$package')" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check and install requirements
check_and_install_requirements() {
    local skip_prompt=$1
    local missing_packages=()
    
    # Read requirements.txt and check each package
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and empty lines
        if [[ $line =~ ^[[:space:]]*# ]] || [[ -z $line ]]; then
            continue
        fi
        
        # Extract package name without version specifier
        package=$(echo "$line" | cut -d'>' -f1 | cut -d'<' -f1 | cut -d'=' -f1 | cut -d'[' -f1 | tr -d ' ')
        
        if ! check_package_installed "$package"; then
            missing_packages+=("$package")
        fi
    done < requirements.txt
    
    # If there are missing packages
    if [ ${#missing_packages[@]} -gt 0 ]; then
        log_warn "Missing packages: ${missing_packages[*]}"
        
        if [ "$skip_prompt" = "true" ]; then
            log_info "Installing missing packages (--skip-prompt)"
            python -m pip install -r requirements.txt
        else
            if get_confirmation "Would you like to install missing packages?"; then
                log_info "Installing missing packages..."
                python -m pip install -r requirements.txt
            else
                log_error "Required packages are missing and installation was declined"
                exit 1
            fi
        fi
    else
        log_info "All required packages are already installed"
    fi
}

# Function to find existing venv
find_existing_venv() {
    local venv_paths=()
    
    # Check COMFY_PATH first if it exists
    if [ -n "$COMFY_PATH" ] && [ -d "$COMFY_PATH/.venv" ]; then
        venv_paths+=("$COMFY_PATH/.venv")
    fi
    
    # Check home directory
    if [ -d "$HOME/.venv" ]; then
        venv_paths+=("$HOME/.venv")
    fi
    
    # Return space-separated list of found venvs
    echo "${venv_paths[*]}"
}

# Function to check if we're in a virtual environment
check_active_venv() {
    if [ -n "$VIRTUAL_ENV" ]; then
        log_info "Using active virtual environment: $VIRTUAL_ENV"
        return 0
    fi
    return 1
}

# Function to check if we're in a conda environment
check_active_conda() {
    if [ -n "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" != "base" ]; then
        log_info "Using active conda environment: $CONDA_DEFAULT_ENV"
        return 0
    fi
    return 1
}

# Function to install conda if needed
install_conda() {
    if ! command -v conda &> /dev/null; then
        log_warn "Conda not found, installing Miniconda..."
        
        # Download Miniconda installer
        wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
        
        # Install Miniconda
        bash miniconda.sh -b -p "$HOME/miniconda"
        
        # Add to PATH
        export PATH="$HOME/miniconda/bin:$PATH"
        
        # Initialize conda
        conda init bash
        
        # Cleanup
        rm miniconda.sh
        
        log_info "Conda installed successfully"
    fi
}

# Function to setup virtual environment
setup_venv() {
    local skip_prompt=$1
    
    # If we're already in a venv, use it
    if check_active_venv; then
        return 0
    fi
    
    # Find existing venvs
    local existing_venvs=($(find_existing_venv))
    
    if [ ${#existing_venvs[@]} -gt 0 ]; then
        if [ "$skip_prompt" = "true" ]; then
            log_info "Found existing venv, using: ${existing_venvs[0]}"
            source "${existing_venvs[0]}/bin/activate"
            return 0
        fi
        
        # Ask user which venv to use
        log_info "Found existing virtual environments:"
        select venv in "${existing_venvs[@]}" "Create new"; do
            case $venv in
                "Create new")
                    break
                    ;;
                *)
                    if [ -n "$venv" ]; then
                        log_info "Using existing venv: $venv"
                        source "$venv/bin/activate"
                        return 0
                    fi
                    ;;
            esac
        done
    fi
    
    # Create new venv if needed
    VENV_PATH="${PYTHON_VENV:-.venv}"
    
    if [ ! -d "$VENV_PATH" ]; then
        if [ "$skip_prompt" = "true" ]; then
            log_info "Creating virtual environment at $VENV_PATH"
            python -m venv "$VENV_PATH"
        else
            if get_confirmation "Create virtual environment at $VENV_PATH?"; then
                log_info "Creating virtual environment at $VENV_PATH"
                python -m venv "$VENV_PATH"
            else
                log_error "User declined virtual environment creation"
                exit 1
            fi
        fi
    fi
    
    log_info "Activating virtual environment"
    source "$VENV_PATH/bin/activate"
}

# Function to setup conda environment
setup_conda() {
    local skip_prompt=$1
    
    # If we're already in a conda env, use it
    if check_active_conda; then
        return 0
    fi
    
    # Install conda if needed
    install_conda
    
    # Set default conda env name if not specified
    CONDA_ENV="${CONDA_ENV:-comfy_env}"
    
    # Create conda environment if it doesn't exist
    if ! conda env list | grep -q "^${CONDA_ENV} "; then
        if [ "$skip_prompt" = "true" ]; then
            log_info "Creating conda environment: $CONDA_ENV"
            conda create -n "$CONDA_ENV" python=3.10 -y
        else
            if get_confirmation "Create conda environment: $CONDA_ENV?"; then
                log_info "Creating conda environment: $CONDA_ENV"
                conda create -n "$CONDA_ENV" python=3.10 -y
            else
                log_error "User declined conda environment creation"
                exit 1
            fi
        fi
    fi
    
    # Activate conda environment
    log_info "Activating conda environment: $CONDA_ENV"
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV"
}

# Load .env file if it exists, but don't override existing env vars
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
        
        # Only set if not already set in environment
        if [ -z "${!key}" ]; then
            export "$key=$value"
        fi
    done < .env
fi

# Check for active environments and handle environment selection
if ! check_active_venv && ! check_active_conda; then
    if [[ "$*" == *"--skip-prompt"* ]]; then
        log_warn "No active or specified environment found, proceeding without virtualization"
    else
        env_choice=$(get_user_choice "Select environment type:" "venv" "conda" "none")
        case $env_choice in
            "venv")
                setup_venv "$@"
                ;;
            "conda")
                setup_conda "$@"
                ;;
            "none")
                log_warn "Proceeding without virtualization"
                ;;
        esac
    fi
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    log_error "requirements.txt not found"
    exit 1
fi

# Install/upgrade pip
log_info "Upgrading pip"
python -m pip install --upgrade pip

# Check and install requirements
check_and_install_requirements "$([[ "$*" == *"--skip-prompt"* ]] && echo true || echo false)"

# Run comfy_config.py with all arguments passed through
log_info "Running comfy_config.py"
python comfy_config.py "$@" 