# Rental Recon Project Roadmap

## Project Goals
- [x] Create a rental property tracking application using Python, FastAPI, and SQLite
- [x] Support capturing property details (address, type, price, etc.)
- [x] Implement image pasting from websites and additional image uploads
- [x] Make the app responsive and user-friendly
- [ ] Ensure the application runs reliably on a Raspberry Pi 4 in a conda environment

## Key Features
- [x] Property listing entry form with all required fields
- [x] Image pasting from clipboard (main image)
- [x] Multiple image upload support
- [x] Property listing overview
- [x] Property detail view
- [x] Edit and delete functionality
- [x] Travel time range display (e.g., "10-18 min") below input fields, matching Google Maps UI and always using 8:30 AM Monday for consistency
- [x] Commute route map rendered using Google Maps API (shows route between property and global address)
- [ ] Data backup/export feature (future enhancement)
- [ ] Sorting and filtering options (future enhancement)

## Completion Criteria
- [x] Application runs locally
- [x] All CRUD operations for properties work correctly
- [x] Image paste and upload functionality works
- [x] Responsive UI that works on different devices
- [x] Travel time range (min-max) is displayed for each commute slot, with conservative (max) value used for planning
- [x] Google Maps API key is set up securely via `.env` file using python-dotenv (NOT via shell profile or setup_api_key.sh)
- [x] Commute route map renders correctly in property details view
- [ ] Successfully runs on Raspberry Pi 4
- [ ] Installation process is straightforward using conda

## Critical Requirements

### Travel Time Range Display (CRITICAL)
- **Always show travel time ranges** below each input field on property details page
- **Backend Contract**: Must provide `*_display` fields (e.g., `travel_time_830am_display`) for each time slot
- **Frontend Contract**: Must display ranges on page load AND after auto-calculation
- **Format**: Show range (e.g., "10-18 min") below input, with conservative (upper) value in input field
- **Fallback**: If no backend range data, calculate estimated range from conservative value
- **Implementation**: Range display logic in both `displayPropertyDetails()` and `calculateTravelTimes()` functions

### Google Maps API Integration
- **API Key Management**: Stored securely in `.env` file using `python-dotenv`
- **⚠️ CRITICAL**: NEVER set system environment variable `GOOGLE_MAPS_API_KEY` - it overrides .env file
- **Required APIs**: Distance Matrix API, Maps JavaScript API, Directions API
- **Google Cloud Console**: Set API restrictions to these 3 APIs only, Application restrictions to "None" for development
- **Billing**: Must be enabled in Google Cloud Console for all Maps APIs
- **Backend**: Loads key from .env via python-dotenv and injects into templates
- **Frontend**: Uses injected key for map rendering and route display
- **Route Display**: Shows highlighted path from property to Alaska Airlines HQ (19300 International Blvd, SeaTac, WA)
- **Troubleshooting**: If API issues occur, check `echo $GOOGLE_MAPS_API_KEY` should be empty, then restart server

## Completed Tasks
- [x] Set up FastAPI project structure
- [x] Design SQLite database schema for properties and images
- [x] Implement backend endpoints for property CRUD operations
- [x] Implement backend endpoints for image upload/paste
- [x] Create frontend form for property entry
- [x] Implement image pasting (main image) with visual confirmation
- [x] Implement UI for adding multiple images
- [x] Generate requirements.txt for deployment on Raspberry Pi
- [x] Create setup and run scripts for easy deployment
