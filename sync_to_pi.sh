#!/bin/bash

# Rental Recon Sync Script
# Version 1.0
#
# This script syncs the project files to the Raspberry Pi and restarts the service
# It includes a dry-run option, better error handling, conda environment support,
# branch detection, and reverse sync for database and backups

# Configuration
LOCAL_DIR="/Volumes/Projects/Python Projects/rental_recon/" # Updated to current project path
REMOTE_HOST="movingdb"  # Using hostname for SSH authentication
REMOTE_IP="192.168.10.10"  # Actual IP for direct URL access
REMOTE_USER="smashimo"  # Username for SSH connection when using IP directly
REMOTE_DIR="~/rental-recon/"  # Updated to rental-recon directory
CONDA_ENV="rental-recon"  # Updated to rental-recon conda environment

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Constants
VERSION="1.0"

# Function to display messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Display banner function
print_banner() {
    echo -e "\n${GREEN}╔═════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}  Rental Recon Sync Script v${VERSION}           ${GREEN}║${NC}"
    echo -e "${GREEN}╚═════════════════════════════════════════════╝${NC}\n"
}

# Parse command line arguments
DRY_RUN=false
UPDATE_CONDA=false
TARGET_BRANCH=""

# Get the current branch by default
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

print_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --dry-run          Show what would be synced without making changes"
    echo "  --conda            Update conda environment (slower but ensures all dependencies)"
    echo "  --branch=BRANCH    Specify which branch to deploy (default: current branch '$CURRENT_BRANCH')"
    echo "  --help             Show this help message"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --conda)
            UPDATE_CONDA=true
            shift
            ;;
        --branch=*)
            TARGET_BRANCH="${1#*=}"
            print_message "Using branch: $TARGET_BRANCH"
            shift
            ;;
        --help)
            print_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

# Display the script banner first thing
print_banner

# If no branch was specified, use the current branch
if [ -z "$TARGET_BRANCH" ]; then
    TARGET_BRANCH="$CURRENT_BRANCH"
    print_message "Using current branch: $TARGET_BRANCH"
fi

if [ "$DRY_RUN" = true ]; then
    print_warning "DRY RUN MODE - No changes will be made"
    echo ""
    
    print_message "Would sync files from: $LOCAL_DIR"
    print_message "Would sync files to: $REMOTE_HOST:$REMOTE_DIR"
    print_message "Would use branch: $TARGET_BRANCH"
    print_message "Would use conda environment: $CONDA_ENV"
    
    if [ "$UPDATE_CONDA" = true ]; then
        print_message "Would update conda environment"
    fi
    
    # Show what files would be synced
    print_message "Files that would be synced:"
    rsync -avz --dry-run --delete \
        --exclude 'venv' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.git' \
        --exclude '.DS_Store' \
        --exclude 'node_modules' \
        --exclude '.env' \
        --exclude 'windsurf_server.log' \
        --exclude 'console.log' \
        --exclude 'new_console.log' \
        --exclude 'backups/' \
        --exclude 'data/rental_recon.db' \
        "$LOCAL_DIR" "$REMOTE_HOST:$REMOTE_DIR"
    
    print_message "Dry run complete. Use without --dry-run to actually sync."
    exit 0
else
    # First sync files TO Pi
    print_message "Syncing files TO $REMOTE_HOST..."
    rsync -avz --delete \
        --exclude 'venv' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.git' \
        --exclude '.DS_Store' \
        --exclude 'node_modules' \
        --exclude '.env' \
        --exclude 'windsurf_server.log' \
        --exclude 'console.log' \
        --exclude 'new_console.log' \
        --exclude 'backups/' \
        --exclude 'data/rental_recon.db' \
        "$LOCAL_DIR" "$REMOTE_HOST:$REMOTE_DIR"
    
    if [ $? -ne 0 ]; then
        print_error "File sync failed!"
        exit 1
    fi
    
    print_message "File sync completed successfully."
    
    # Execute commands on the Pi
    print_message "Executing setup commands on $REMOTE_HOST..."
    ssh $REMOTE_HOST UPDATE_CONDA=$UPDATE_CONDA TARGET_BRANCH="$TARGET_BRANCH" << 'EOF'
        # Define colors directly in the SSH session
        GREEN='\033[0;32m'
        YELLOW='\033[1;33m'
        RED='\033[0;31m'
        NC='\033[0m'
        
        # Navigate to the project directory
        cd ~/rental-recon/
        
        # Check if we're in the right directory
        if [ ! -f "requirements.txt" ]; then
            echo -e "${RED}[ERROR]${NC} Not in the correct project directory or requirements.txt not found!"
            exit 1
        fi
        
        echo -e "${GREEN}[INFO]${NC} Current directory: $(pwd)"
        
        # Initialize conda for bash if not already done
        if ! command -v conda &> /dev/null; then
            echo -e "${YELLOW}[WARNING]${NC} Conda not found in PATH, attempting to initialize..."
            source ~/miniconda3/etc/profile.d/conda.sh
        fi
        
        # Activate the conda environment
        echo -e "${GREEN}[INFO]${NC} Activating conda environment: rental-recon"
        conda activate rental-recon
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}[ERROR]${NC} Failed to activate conda environment 'rental-recon'!"
            exit 1
        fi
        
        # Verify Python version
        PYTHON_VERSION=$(python --version 2>&1)
        echo -e "${GREEN}[INFO]${NC} Using Python: $PYTHON_VERSION"
        
        # Update conda environment if requested
        if [ "$UPDATE_CONDA" = "true" ]; then
            echo -e "${GREEN}[INFO]${NC} Updating conda environment..."
            conda env update -f environment.yml || echo -e "${YELLOW}[WARNING]${NC} No environment.yml found, skipping conda update"
        fi
        
        # Install/update Python dependencies
        echo -e "${GREEN}[INFO]${NC} Installing/updating Python dependencies..."
        pip install -r requirements.txt
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}[ERROR]${NC} Failed to install Python dependencies!"
            exit 1
        fi
        
        # Check if we need to switch branches
        if [ -n "$TARGET_BRANCH" ] && [ "$TARGET_BRANCH" != "main" ] && [ "$TARGET_BRANCH" != "master" ]; then
            echo -e "${GREEN}[INFO]${NC} Switching to branch: $TARGET_BRANCH"
            git checkout "$TARGET_BRANCH" || {
                echo -e "${YELLOW}[WARNING]${NC} Failed to switch to branch $TARGET_BRANCH, continuing with current branch"
            }
        fi
        
        # Create necessary directories if they don't exist
        mkdir -p data
        mkdir -p backups
        
        # Set proper permissions for the application directory
        chmod -R 755 ~/rental-recon/
        
        # Verify key files exist and have correct permissions
        if [ -f "app/main.py" ]; then
            echo -e "${GREEN}[INFO]${NC} Main application file found: app/main.py"
            chmod 644 app/main.py
        else
            echo -e "${RED}[ERROR]${NC} Main application file not found: app/main.py"
            exit 1
        fi
        
        # Check for template files
        TEMPLATE_COUNT=$(find app/templates -name "*.html" 2>/dev/null | wc -l)
        if [ "$TEMPLATE_COUNT" -gt 0 ]; then
            echo -e "${GREEN}[INFO]${NC} Found $TEMPLATE_COUNT template files"
            chmod 644 app/templates/*.html 2>/dev/null || true
        else
            echo -e "${YELLOW}[WARNING]${NC} No template files found in app/templates/"
        fi
        
        # Check for static files
        if [ -d "app/static" ]; then
            echo -e "${GREEN}[INFO]${NC} Static files directory found"
            chmod -R 644 app/static/* 2>/dev/null || true
        fi
        
        # Create or update systemd service file
        SERVICE_FILE="/etc/systemd/system/rental-recon.service"
        SERVICE_FILE_UPDATED=false
        
        # Check if service file exists and if it needs updating
        if [ ! -f "$SERVICE_FILE" ] || ! grep -q "rental-recon" "$SERVICE_FILE" 2>/dev/null; then
            echo -e "${GREEN}[INFO]${NC} Creating/updating systemd service file..."
            sudo tee "$SERVICE_FILE" > /dev/null << 'SERVICE_EOF'
[Unit]
Description=Rental Recon FastAPI Application
After=network.target

[Service]
Type=simple
User=smashimo
WorkingDirectory=/home/smashimo/rental-recon
Environment=PATH=/home/smashimo/miniconda3/envs/rental-recon/bin
ExecStart=/home/smashimo/miniconda3/envs/rental-recon/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE_EOF
            SERVICE_FILE_UPDATED=true
            echo -e "${GREEN}[INFO]${NC} Service file created/updated."
        else
            echo -e "${GREEN}[INFO]${NC} Service file already exists and appears correct."
        fi
        
        # Reload systemd daemon if service file was updated
        if [ "$SERVICE_FILE_UPDATED" = true ]; then
            echo -e "${GREEN}[INFO]${NC} Reloading systemd daemon..."
            sudo systemctl daemon-reload || { echo -e "${RED}[ERROR]${NC} Failed to reload systemd daemon!"; exit 1; }
            echo -e "${GREEN}[INFO]${NC} Systemd daemon reloaded."
        fi
        
        # Enable the service if not already enabled
        if ! sudo systemctl is-enabled rental-recon.service &>/dev/null; then
            echo -e "${GREEN}[INFO]${NC} Enabling rental-recon service..."
            sudo systemctl enable rental-recon.service || { echo -e "${RED}[ERROR]${NC} Failed to enable service!"; exit 1; }
            echo -e "${GREEN}[INFO]${NC} Service enabled."
        else
            echo -e "${GREEN}[INFO]${NC} Service already enabled."
        fi
        
        # Stop the service if it's running
        if sudo systemctl is-active rental-recon.service &>/dev/null; then
            echo -e "${GREEN}[INFO]${NC} Stopping rental-recon service..."
            sudo systemctl stop rental-recon.service || { echo -e "${YELLOW}[WARNING]${NC} Failed to stop service gracefully"; }
        fi
        
        # Start the service
        echo -e "${GREEN}[INFO]${NC} Starting rental-recon service..."
        sudo systemctl start rental-recon.service
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[INFO]${NC} Service started successfully."
        else
            echo -e "${RED}[ERROR]${NC} Failed to start service!"
            echo -e "${YELLOW}[INFO]${NC} Checking service status..."
            sudo systemctl status rental-recon.service --no-pager -l
            exit 1
        fi
        
        # Wait a moment and check if the service is still running
        sleep 3
        if sudo systemctl is-active rental-recon.service &>/dev/null; then
            echo -e "${GREEN}[SUCCESS]${NC} Rental Recon service is running!"
            echo -e "${GREEN}[INFO]${NC} Service status:"
            sudo systemctl status rental-recon.service --no-pager -l | head -10
        else
            echo -e "${RED}[ERROR]${NC} Service failed to stay running!"
            echo -e "${YELLOW}[INFO]${NC} Service logs:"
            sudo journalctl -u rental-recon.service --no-pager -l | tail -20
            exit 1
        fi
        
        echo -e "${GREEN}[SUCCESS]${NC} Deployment completed successfully!"
        echo -e "${GREEN}[INFO]${NC} Application should be accessible at http://192.168.10.10:8000"
EOF

    # Check the exit status of the SSH command block
    SSH_EXIT_CODE=$?
    if [ $SSH_EXIT_CODE -ne 0 ]; then
        print_error "Remote setup failed with exit code $SSH_EXIT_CODE"
        exit 1
    fi
    
    # Sync database and backups FROM Pi (if they exist)
    print_message "Syncing database and backups FROM $REMOTE_HOST..."
    rsync -avz "$REMOTE_HOST:$REMOTE_DIR/data/" "$LOCAL_DIR/data/" 2>/dev/null || print_warning "No remote data directory found"
    rsync -avz "$REMOTE_HOST:$REMOTE_DIR/backups/" "$LOCAL_DIR/backups/" 2>/dev/null || print_warning "No remote backups directory found"
    
    print_message "Deployment completed successfully!"
    print_message "Application should be accessible at http://$REMOTE_IP:8000"
fi
