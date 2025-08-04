#!/bin/bash

# Moving Box Tracker Sync Script
# Version 2.6
#
# This script syncs the project files to the Raspberry Pi and restarts the service
# It includes a dry-run option, better error handling, conda environment support,
# branch detection, and reverse sync for database and backups

# Configuration
LOCAL_DIR="/Volumes/Projects/Python Projects/moving/" # Updated to current project path
REMOTE_HOST="movingdb"  # Using hostname for SSH authentication
REMOTE_IP="192.168.10.10"  # Actual IP for direct URL access
REMOTE_USER="smashimo"  # Username for SSH connection when using IP directly
REMOTE_DIR="~/moving_box_tracker/"  # Updated to use underscores instead of hyphens
CONDA_ENV="movingbox"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Constants
VERSION="2.6"

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
    echo -e "${GREEN}║${NC}  Moving Box Tracker Sync Script v${VERSION}       ${GREEN}║${NC}"
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
    print_message "Performing a dry run (no changes will be made)"
else
    
    # Confirm before proceeding
    read -p "This will sync files to $REMOTE_HOST and restart the service. Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message "Operation cancelled"
        exit 0
    fi
fi

# First, sync critical data FROM Pi to local (database and backups)
if [ "$DRY_RUN" = true ]; then
    print_message "DRY RUN: Database and backup files that would be synced FROM Pi:"
    # Show what database file would be synced from Pi
    ssh $REMOTE_HOST "ls -la ~/moving_box_tracker/moving_boxes.db 2>/dev/null || echo 'No database file found on Pi'"
    # Show what backup files would be synced from Pi
    ssh $REMOTE_HOST "ls -la ~/moving_box_tracker/backups/ 2>/dev/null || echo 'No backups directory found on Pi'"
else
    print_message "Syncing database and backups FROM $REMOTE_HOST to local..."
    
    # Sync database file from Pi (if it exists and is newer)
    if ssh $REMOTE_HOST "test -f ~/moving_box_tracker/moving_boxes.db"; then
        print_message "Found database on Pi, syncing to local..."
        rsync -avz --update -e ssh "$REMOTE_HOST:$REMOTE_DIR/moving_boxes.db" "$LOCAL_DIR"
        if [ $? -eq 0 ]; then
            print_message "Database synced successfully from Pi"
        else
            print_warning "Failed to sync database from Pi, but continuing..."
        fi
    else
        print_warning "No database file found on Pi"
    fi
    
    # Sync backups directory from Pi (if it exists)
    if ssh $REMOTE_HOST "test -d ~/moving_box_tracker/backups"; then
        print_message "Found backups directory on Pi, syncing to local..."
        # Create backups directory locally if it doesn't exist
        mkdir -p "${LOCAL_DIR}backups"
        rsync -avz --update -e ssh "$REMOTE_HOST:$REMOTE_DIR/backups/" "${LOCAL_DIR}backups/"
        if [ $? -eq 0 ]; then
            print_message "Backups synced successfully from Pi"
        else
            print_warning "Failed to sync backups from Pi, but continuing..."
        fi
    else
        print_warning "No backups directory found on Pi"
    fi
    
    # Sync logs directory from Pi (if it exists)
    if ssh $REMOTE_HOST "test -d ~/moving_box_tracker/logs"; then
        print_message "Found logs directory on Pi, syncing to local..."
        # Create logs directory locally if it doesn't exist
        mkdir -p "${LOCAL_DIR}logs"
        rsync -avz --update -e ssh "$REMOTE_HOST:$REMOTE_DIR/logs/" "${LOCAL_DIR}logs/"
        if [ $? -eq 0 ]; then
            print_message "Logs synced successfully from Pi"
        else
            print_warning "Failed to sync logs from Pi, but continuing..."
        fi
    else
        print_warning "No logs directory found on Pi"
    fi
fi

# Now perform the main sync TO Pi
if [ "$DRY_RUN" = true ]; then
    print_message "DRY RUN: Files that would be synced TO Pi:"
    rsync -avzn --delete \
        --exclude 'venv' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.git' \
        --exclude '*.db' \
        --exclude 'backups/' \
        --exclude 'logs/' \
        --exclude '.last_req_checksum' \
        --exclude '.conda/' \
        -e ssh \
        "$LOCAL_DIR" \
        "$REMOTE_HOST:$REMOTE_DIR"
else
    # First sync files TO Pi
    print_message "Syncing files TO $REMOTE_HOST..."
    rsync -avz --delete \
        --exclude 'venv' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.git' \
        --exclude '*.db' \
        --exclude 'backups/' \
        --exclude 'logs/' \
        --exclude '.last_req_checksum' \
        --exclude '.conda/' \
        -e ssh \
        "$LOCAL_DIR" \
        "$REMOTE_HOST:$REMOTE_DIR"
    
    if [ $? -ne 0 ]; then
        print_error "Failed to sync files to $REMOTE_HOST"
        exit 1
    fi
    
    print_message "Pulling latest changes from branch '$TARGET_BRANCH', updating dependencies, fixing permissions, and restarting service on $REMOTE_HOST..."

    # ---
    # NOTE: Permissions fix logic is now run INSIDE the main SSH block below.
    # This avoids nested SSH calls, which can break SSH authentication context (esp. with agents).
    # Do NOT call fix_pi_permissions.sh from your Mac; keep it on the Pi for manual fixes if needed.
    # ---

    ssh $REMOTE_HOST UPDATE_CONDA=$UPDATE_CONDA TARGET_BRANCH="$TARGET_BRANCH" << 'EOF'
        # Define colors directly in the SSH session
        GREEN='\033[0;32m'
        YELLOW='\033[1;33m'
        RED='\033[0;31m'
        NC='\033[0m' # No Color
        
        echo -e "${GREEN}[INFO]${NC} Activating conda environment $CONDA_ENV..."
        # Source conda setup script
        source ~/miniconda3/etc/profile.d/conda.sh || { echo -e "${RED}[ERROR]${NC} Failed to source ~/miniconda3/etc/profile.d/conda.sh"; exit 1; }
        conda activate movingbox || { echo -e "${RED}[ERROR]${NC} Failed to activate conda env movingbox"; exit 1; }

        echo -e "${GREEN}[INFO]${NC} Changing to project directory ~/moving_box_tracker..."
        cd ~/moving_box_tracker  # Updated to use underscores instead of hyphens

        # Explicitly tell Git to use the SSH key
        export GIT_SSH_COMMAND="ssh -i ~/.ssh/id_rsa"

        # Reset any local changes and pull latest from Git
        echo -e "${GREEN}[INFO]${NC} Resetting local changes..."
        git reset --hard HEAD
        git clean -fd
        echo -e "${GREEN}[INFO]${NC} Pulling latest changes from branch '$TARGET_BRANCH'..."
        git pull origin "$TARGET_BRANCH" || { echo -e "${RED}[ERROR]${NC} Git pull failed for branch '$TARGET_BRANCH'!"; exit 1; }
        echo -e "${GREEN}[INFO]${NC} Git pull from branch '$TARGET_BRANCH' successful."

        # ---
        # PERMISSIONS FIX: This block ensures static files and parent dirs are accessible to Nginx
        # Fixed in v2.6: Extended to include templates directory and improved verification
        # ---
        echo -e "${GREEN}[INFO]${NC} Fixing static and template file permissions..."
        cd ~/moving_box_tracker || { echo -e "${RED}[ERROR]${NC} Could not cd to project directory!"; exit 1; }
        
        # Fix directory permissions (755 = rwxr-xr-x) for both static and templates
        echo -e "${GREEN}[INFO]${NC} Setting directory permissions to 755..."
        find static templates -type d -exec chmod 755 {} \; || { echo -e "${RED}[ERROR]${NC} Failed to set directory permissions!"; exit 1; }
        
        # Fix file permissions (644 = rw-r--r--) for both static and templates
        echo -e "${GREEN}[INFO]${NC} Setting file permissions to 644..."
        find static templates -type f -exec chmod 644 {} \; || { echo -e "${RED}[ERROR]${NC} Failed to set file permissions!"; exit 1; }
        
        # Fix ownership for both static and templates
        echo -e "${GREEN}[INFO]${NC} Setting correct ownership..."
        sudo chown -R smashimo:www-data ~/moving_box_tracker/static/ ~/moving_box_tracker/templates/ || { echo -e "${RED}[ERROR]${NC} Failed to set ownership!"; exit 1; }
        sudo chmod -R g+r ~/moving_box_tracker/static/ ~/moving_box_tracker/templates/ || { echo -e "${RED}[ERROR]${NC} Failed to set group read permissions!"; exit 1; }
        
        # Fix parent directory permissions
        echo -e "${GREEN}[INFO]${NC} Setting parent directory permissions..."
        sudo chmod o+rx ~ || { echo -e "${RED}[ERROR]${NC} Failed to set home directory permissions!"; exit 1; }
        sudo chmod o+rx ~/moving_box_tracker || { echo -e "${RED}[ERROR]${NC} Failed to set project directory permissions!"; exit 1; }
        
        # Verify permissions were set correctly
        echo -e "${GREEN}[INFO]${NC} Verifying permissions..."
        
        # Check static directory permissions
        STATIC_DIR_PERMS=$(ls -ld ~/moving_box_tracker/static | awk '{print $1}')
        if [[ "$STATIC_DIR_PERMS" != "drwxr-xr-x"* ]]; then
            echo -e "${RED}[ERROR]${NC} Static directory permissions verification failed!"
            echo -e "${RED}[ERROR]${NC} Current permissions: $STATIC_DIR_PERMS (should be drwxr-xr-x)"
            exit 1
        fi
        
        # Check templates directory permissions
        TEMPLATES_DIR_PERMS=$(ls -ld ~/moving_box_tracker/templates | awk '{print $1}')
        if [[ "$TEMPLATES_DIR_PERMS" != "drwxr-xr-x"* ]]; then
            echo -e "${RED}[ERROR]${NC} Templates directory permissions verification failed!"
            echo -e "${RED}[ERROR]${NC} Current permissions: $TEMPLATES_DIR_PERMS (should be drwxr-xr-x)"
            exit 1
        fi
        
        # Check a sample file from each directory
        STATIC_FILE_PERMS=$(ls -l ~/moving_box_tracker/static/js/main.js 2>/dev/null | awk '{print $1}')
        if [[ -f ~/moving_box_tracker/static/js/main.js && "$STATIC_FILE_PERMS" != "-rw-r--r--"* ]]; then
            echo -e "${RED}[ERROR]${NC} Static file permissions verification failed!"
            echo -e "${RED}[ERROR]${NC} main.js permissions: $STATIC_FILE_PERMS (should be -rw-r--r--)"
            exit 1
        fi
        
        TEMPLATE_FILE_PERMS=$(ls -l ~/moving_box_tracker/templates/create.html 2>/dev/null | awk '{print $1}')
        if [[ -f ~/moving_box_tracker/templates/create.html && "$TEMPLATE_FILE_PERMS" != "-rw-r--r--"* ]]; then
            echo -e "${RED}[ERROR]${NC} Template file permissions verification failed!"
            echo -e "${RED}[ERROR]${NC} create.html permissions: $TEMPLATE_FILE_PERMS (should be -rw-r--r--)"
            exit 1
        fi
        
        echo -e "${GREEN}[SUCCESS]${NC} Permissions and ownership fixed and verified for both static and templates directories."
        # ---

        # Check if schema needs to be applied
        echo -e "${GREEN}[INFO]${NC} Checking database schema..."
        if [ ! -f moving_boxes.db ]; then
            echo -e "${GREEN}[INFO]${NC} Database not found, initializing schema..."
            sqlite3 moving_boxes.db < schema.sql
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}[INFO]${NC} Schema initialized successfully."
            else
                echo -e "${RED}[ERROR]${NC} Failed to initialize schema!"; 
                exit 1
            fi
        fi

        # Run database migration script
        echo -e "${GREEN}[INFO]${NC} Running database migration script..."
        python migrate_categories.py || { echo -e "${RED}[ERROR]${NC} Database migration failed!"; exit 1; }
        echo -e "${GREEN}[INFO]${NC} Database migration completed."

        # Only update conda environment if --conda flag is used
        if [ "$UPDATE_CONDA" = true ]; then
            # Export conda environment to ensure all packages are installed
            echo -e "${GREEN}[INFO]${NC} Exporting conda environment requirements..."
            conda env export --no-builds | grep -v "^prefix: " > environment.yml
            
            # Update conda environment with all required packages
            echo -e "${GREEN}[INFO]${NC} Updating conda environment..."
            conda env update -f environment.yml
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}[INFO]${NC} Conda environment updated successfully."
            else
                echo -e "${RED}[ERROR]${NC} Failed to update conda environment!"
                exit 1
            fi
            
            # Also install pip requirements for any packages not in conda
            echo -e "${GREEN}[INFO]${NC} Installing pip requirements..."
            pip install -r requirements.txt
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}[INFO]${NC} Pip requirements installed successfully."
            else
                echo -e "${RED}[ERROR]${NC} Failed to install pip requirements!"
                exit 1
            fi
        fi

        # Check if Flask is running manually (not as systemd service)
        echo -e "${GREEN}[INFO]${NC} Checking Flask process status..."
        MANUAL_FLASK_PID=$(pgrep -f "python.*simplified_app.py" || echo "")
        SYSTEMD_ACTIVE=$(systemctl is-active moving_boxes.service 2>/dev/null || echo "inactive")
        
        if [ -n "$MANUAL_FLASK_PID" ]; then
            echo -e "${YELLOW}[WARNING]${NC} Flask is running manually (PID: $MANUAL_FLASK_PID). Stopping it..."
            kill $MANUAL_FLASK_PID || echo -e "${YELLOW}[WARNING]${NC} Failed to kill manual Flask process"
            sleep 2
            # Check if process is still running
            if pgrep -f "python.*simplified_app.py" > /dev/null; then
                echo -e "${YELLOW}[WARNING]${NC} Process still running, force killing..."
                pkill -9 -f "python.*simplified_app.py" || echo -e "${YELLOW}[WARNING]${NC} Failed to force kill"
                sleep 1
            fi
            echo -e "${GREEN}[INFO]${NC} Manual Flask process stopped."
        fi

        # Check if the service file in the project directory is newer than the one in systemd
        # This assumes moving_boxes.service is tracked in Git in the project root
        PROJECT_SERVICE_FILE="/home/smashimo/moving_box_tracker/moving_boxes.service"
        SYSTEMD_SERVICE_FILE="/etc/systemd/system/moving_boxes.service"
        SERVICE_FILE_UPDATED=false

        if [ -f "$PROJECT_SERVICE_FILE" ]; then
            if sudo test "$PROJECT_SERVICE_FILE" -nt "$SYSTEMD_SERVICE_FILE" 2>/dev/null; then
                echo -e "${GREEN}[INFO]${NC} Project service file is newer, updating systemd service file..."
                sudo cp "$PROJECT_SERVICE_FILE" "$SYSTEMD_SERVICE_FILE" || { echo -e "${RED}[ERROR]${NC} Failed to copy service file!"; exit 1; }
                echo -e "${GREEN}[INFO]${NC} Systemd service file updated."
                SERVICE_FILE_UPDATED=true
            else
                echo -e "${GREEN}[INFO]${NC} Systemd service file is up-to-date."
            fi
        else
            echo -e "${YELLOW}[WARNING]${NC} Project service file ($PROJECT_SERVICE_FILE) not found. Cannot update systemd service file automatically."
        fi

        # Reload systemd daemon if the service file was updated
        if [ "$SERVICE_FILE_UPDATED" = true ]; then
            echo -e "${GREEN}[INFO]${NC} Reloading systemd daemon..."
            sudo systemctl daemon-reload || { echo -e "${RED}[ERROR]${NC} Failed to reload systemd daemon!"; exit 1; }
            echo -e "${GREEN}[INFO]${NC} Systemd daemon reloaded."
        fi

        # Permissions are now handled by the separate fix_pi_permissions.sh script
        # This section has been intentionally removed in v2.1

        # Update nginx configuration
        echo -e "${GREEN}[INFO]${NC} Updating nginx configuration..."
        sudo cp nginx.conf /etc/nginx/sites-available/moving_boxes || { echo -e "${RED}[ERROR]${NC} Failed to copy nginx config!"; exit 1; }
        sudo ln -sf /etc/nginx/sites-available/moving_boxes /etc/nginx/sites-enabled/moving_boxes
        sudo nginx -t || { echo -e "${RED}[ERROR]${NC} Nginx config test failed!"; exit 1; }
        sudo systemctl restart nginx || { echo -e "${RED}[ERROR]${NC} Failed to restart nginx!"; exit 1; }
        echo -e "${GREEN}[INFO]${NC} Nginx configuration updated and restarted."

        # Restart the service or start Flask manually based on how it was running
        if [ -n "$MANUAL_FLASK_PID" ]; then
            echo -e "${GREEN}[INFO]${NC} Flask was running manually, restarting it manually..."
            echo -e "${GREEN}[INFO]${NC} Starting Flask in background..."
            nohup python simplified_app.py > flask.log 2>&1 &
            FLASK_PID=$!
            echo -e "${GREEN}[INFO]${NC} Flask started with PID: $FLASK_PID"
            
            # Wait a moment and check if it's still running
            sleep 3
            if ps -p $FLASK_PID > /dev/null; then
                echo -e "${GREEN}[SUCCESS]${NC} Flask is running successfully."
            else
                echo -e "${RED}[ERROR]${NC} Flask failed to start. Check flask.log for details."
                tail -20 flask.log
                exit 1
            fi
        elif [ "$SYSTEMD_ACTIVE" == "active" ] || systemctl list-unit-files | grep -q "moving_boxes.service"; then
            echo -e "${GREEN}[INFO]${NC} Using systemd service..."
            sudo systemctl restart moving_boxes.service || { echo -e "${RED}[ERROR]${NC} Failed to restart service!"; exit 1; }
            echo -e "${GREEN}[INFO]${NC} Service restart command sent."

            # Check service status with retry
            echo -e "${GREEN}[INFO]${NC} Waiting for service to become active..."
            RETRY_COUNT=0
            MAX_RETRIES=10 # Try for ~30 seconds
            DELAY=3       # Seconds between retries

            while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
                SERVICE_STATUS=$(systemctl is-active moving_boxes.service)
                if [ "$SERVICE_STATUS" == "active" ]; then
                     echo -e "${GREEN}[SUCCESS]${NC} Service is active."
                     break
                fi
                # Add a check for failed state
                SERVICE_FAILED=$(systemctl is-failed moving_boxes.service)
                if [ "$SERVICE_FAILED" == "failed" ]; then
                     echo -e "${RED}[ERROR]${NC} Service entered failed state."
                     sudo journalctl -u moving_boxes.service -n 20 --no-pager # Show logs on failure
                     exit 1 # Exit SSH sub-shell with error
                fi
                
                echo -e "${GREEN}[INFO]${NC} Service status: $SERVICE_STATUS. Retrying in $DELAY seconds..."
                sleep $DELAY
                RETRY_COUNT=$((RETRY_COUNT + 1))
            done

            # Check final status
            FINAL_STATUS=$(systemctl is-active moving_boxes.service)
            if [ "$FINAL_STATUS" != "active" ]; then
                echo -e "${RED}[ERROR]${NC} Service failed to become active after $MAX_RETRIES retries."
                echo -e "${RED}[INFO]${NC} Final status: $FINAL_STATUS"
                sudo journalctl -u moving_boxes.service -n 20 --no-pager # Show logs on timeout
                exit 1 # Exit SSH sub-shell with error
            fi
        else
            echo -e "${YELLOW}[WARNING]${NC} No Flask process was running and no systemd service found."
            echo -e "${GREEN}[INFO]${NC} Starting Flask manually..."
            nohup python simplified_app.py > flask.log 2>&1 &
            FLASK_PID=$!
            echo -e "${GREEN}[INFO]${NC} Flask started with PID: $FLASK_PID"
            
            # Wait a moment and check if it's still running
            sleep 3
            if ps -p $FLASK_PID > /dev/null; then
                echo -e "${GREEN}[SUCCESS]${NC} Flask is running successfully."
            else
                echo -e "${RED}[ERROR]${NC} Flask failed to start. Check flask.log for details."
                tail -20 flask.log
                exit 1
            fi
        fi
EOF

    # Check the exit status of the SSH command block
    SSH_EXIT_CODE=$?
    if [ $SSH_EXIT_CODE -ne 0 ]; then
        print_error "SSH command block failed (Git pull/update/restart service) with exit code $SSH_EXIT_CODE"
        exit 1
    fi

    print_message "Deployment completed successfully!"
    print_message "You can access the application at http://$REMOTE_IP"
fi
