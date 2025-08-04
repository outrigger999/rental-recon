#!/bin/bash

# Rental Recon Sync Script
# Version 1.1
#
# Changelog:
# 1.1 - Added detailed server restart logging and version display
# 1.0 - Initial version
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
VERSION="1.1"

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
    # ---
# REMOTE SERVER SETUP, RESTART & VERIFICATION (EXAMPLES STYLE, ALL LOGS STREAMED LOCALLY)
# ---
ORANGE='\033[38;5;208m'
VERSION="1.1"

print_message "Checking remote requirements.txt..."
ssh $REMOTE_HOST 'test -f ~/rental-recon/requirements.txt' || { print_error "requirements.txt not found on Pi!"; exit 1; }
print_message "requirements.txt found."

print_message "Activating conda environment and installing dependencies on Pi..."
ssh $REMOTE_HOST 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate rental-recon && pip install -r ~/rental-recon/requirements.txt'

print_message "Checking/updating systemd service file on Pi..."
ssh $REMOTE_HOST 'if [ ! -f /etc/systemd/system/rental-recon.service ]; then echo "Creating service file..."; sudo tee /etc/systemd/system/rental-recon.service > /dev/null << EOF2
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
EOF2
sudo systemctl daemon-reload; else echo "Service file exists."; fi'

print_message "Enabling rental-recon service on Pi if not already enabled..."
ssh $REMOTE_HOST 'sudo systemctl enable rental-recon.service 2>/dev/null && echo "Service enabled."'

# --- SERVER RESTART & VERIFICATION ---
echo -e "\n${ORANGE}[INFO] ====== BEGIN SERVER RESTART & VERIFICATION ======${NC}"
echo -e "${ORANGE}[INFO] Version: ${VERSION} - Image Metadata Update${NC}"
echo -e "${ORANGE}[INFO] Current time: $(date)${NC}"
echo -e "${ORANGE}[INFO] Stopping service...${NC}"
ssh $REMOTE_HOST 'sudo systemctl stop rental-recon.service && echo "Service stopped successfully."'
sleep 2
echo -e "${ORANGE}[INFO] Starting service...${NC}"
ssh $REMOTE_HOST 'sudo systemctl start rental-recon.service && echo "Service started successfully."'
sleep 2
SERVICE_STATUS=$(ssh $REMOTE_HOST 'systemctl is-active rental-recon.service')
if [ "$SERVICE_STATUS" = "active" ]; then
    echo -e "${GREEN}[INFO] ✓ Service is running on Pi${NC}"
    SERVICE_START_TIME=$(ssh $REMOTE_HOST 'systemctl show -p ActiveEnterTimestamp rental-recon.service | cut -d= -f2-')
    SERVICE_START_EPOCH=$(date -j -f "%a %Y-%m-%d %H:%M:%S %Z" "$SERVICE_START_TIME" +%s 2>/dev/null || date -d "$SERVICE_START_TIME" +%s)
    CURRENT_EPOCH=$(date +%s)
    TIME_DIFF=$((CURRENT_EPOCH - SERVICE_START_EPOCH))
    UPTIME=$(ssh $REMOTE_HOST 'systemctl status rental-recon.service | grep -oP "(?<=active \(running\) ).*" | cut -d " " -f1')
    echo -e "${GREEN}[INFO] Service start time: $SERVICE_START_TIME${NC}"
    echo -e "${GREEN}[INFO] Current time:       $(date)${NC}"
    echo -e "${GREEN}[INFO] Uptime: $UPTIME (${TIME_DIFF} seconds ago)${NC}"
    if [ $TIME_DIFF -le 60 ]; then
        echo -e "${GREEN}[INFO] ✓ Service was restarted successfully!${NC}"
        echo -e "${GREEN}[INFO] ✓ Server version: ${VERSION} - Image Metadata Update${NC}"
        echo -e "${GREEN}[INFO] Verifying API accessibility...${NC}"
        API_RESPONSE=$(ssh $REMOTE_HOST 'curl -s http://localhost:8000/api/health')
        if [ -n "$API_RESPONSE" ]; then
            echo -e "${GREEN}[INFO] ✓ API is responding: $API_RESPONSE${NC}"
        else
            echo -e "${YELLOW}[WARNING] Could not verify API response${NC}"
        fi
    else
        echo -e "${YELLOW}[WARNING] Service was not recently restarted (${TIME_DIFF} seconds old).${NC}"
        echo -e "${YELLOW}[WARNING]              The server may not be running the latest code.${NC}"
    fi
    echo -e "${GREEN}[INFO] === SERVICE STATUS ===${NC}"
    ssh $REMOTE_HOST 'systemctl status rental-recon.service --no-pager -l | head -15'
else
    echo -e "${RED}[ERROR] Service is not running after restart attempt!${NC}"
    echo -e "${YELLOW}[INFO] Service logs:${NC}"
    ssh $REMOTE_HOST 'journalctl -u rental-recon.service --no-pager -l | tail -20'
    exit 1
fi
echo -e "${GREEN}[SUCCESS] Deployment completed successfully!${NC}"
echo -e "${GREEN}[INFO] Application should be accessible at http://192.168.10.10:8000"
echo -e "${GREEN}[INFO] ====== END SERVER RESTART & VERIFICATION ======${NC}\n"


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
