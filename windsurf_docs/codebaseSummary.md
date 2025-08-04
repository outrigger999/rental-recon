# Codebase Summary

## Key Components and Their Interactions
- **app/**: Main FastAPI application, with subfolders for models, routers, services, schemas, static files, and templates.
- **scripts/**: Utility scripts, e.g., for optimizing images.
- **sync_to_pi.sh**: Bash script for syncing and deploying the app to a Raspberry Pi.
- **requirements.txt**: Python dependencies.
- **windsurf_docs/**: Project documentation and roadmap.

## Data Flow
- User interacts with frontend (Jinja2 + Bootstrap templates)
- Backend (FastAPI) handles API and page requests
- Data stored in SQLite via SQLAlchemy ORM
- Image uploads processed with Pillow, metadata extracted and stored in DB

## External Dependencies
- FastAPI, SQLAlchemy, Pillow, python-dotenv, Bootstrap, Google Maps API, OpenStreetMap Nominatim, Uvicorn, Pytest, HTTPX

## Recent Significant Changes
- Google Maps API key moved to `.env` file
- Travel time range display logic improved
- Image upload and pasting features implemented
- Setup and run scripts for Raspberry Pi deployment added

## User Feedback Integration
- Improved travel time range UI per user feedback
- Enhanced onboarding and API key management per user feedback

## Additional Reference Docs
- See `projectRoadmap.md`, `currentTask.md`, and `techStack.md` for more details.

## Development Workflow
- **Git Branching**: All new features and bug fixes should be developed in a separate feature branch (e.g., `feature/add-new-thing`, `fix/bug-report`). Code will be merged into the `main` branch only after completion and testing.
- **Command Execution**: All terminal commands, including `ssh` commands to the Raspberry Pi and `git` operations, will be executed directly by the AI. The user will review and approve these commands before they are run.

## Execution Environment and Remote Access
- **Execution Environment**: All backend code runs exclusively on a Raspberry Pi 4. Development is done on a local macOS machine, but the application itself is only executed on the Pi.
- **Deployment**: The `sync_to_pi.sh` script is used to synchronize the latest code from the local machine to the Raspberry Pi and restart the server.
- **Remote Access**: For remote access (e.g., from an iPhone), the application is accessed through a Tailscale VPN. 
- **Known Issue & Workaround**: There is a known issue where using the internal domain name (`rental.box`) causes problems with API calls for property details, likely due to an interaction with NGINX and Tailscale. The current workaround is to access the application directly via the Raspberry Pi's IP address: `http://192.168.10.10:8000`.
