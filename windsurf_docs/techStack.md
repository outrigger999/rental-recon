# Rental Recon Tech Stack

## Backend Technologies

### Python FastAPI
- **Version**: 0.95.0
- **Purpose**: API framework providing the core backend functionality
- **Justification**: FastAPI offers high performance with automatic OpenAPI documentation, data validation via Pydantic, and is well-suited for Python applications running on limited hardware like Raspberry Pi

### SQLAlchemy
- **Version**: 2.0.9
- **Purpose**: ORM (Object-Relational Mapping) for database interactions
- **Justification**: Provides a powerful and flexible way to interact with the SQLite database while maintaining clean, Pythonic code

### SQLite
- **Purpose**: Lightweight database for storing property and image data
- **Justification**: File-based database requiring no server setup, perfect for Raspberry Pi deployment while still providing reliable data storage

### Uvicorn
- **Version**: 0.21.1
- **Purpose**: ASGI server to run the FastAPI application
- **Justification**: Lightweight, fast Python ASGI server with good compatibility with FastAPI

### Python-Multipart
- **Version**: 0.0.6
- **Purpose**: Handling form data and file uploads
- **Justification**: Required for processing form submissions and image uploads

## Frontend Technologies

### Jinja2
- **Version**: 3.1.2
- **Purpose**: Template engine for rendering HTML pages
- **Justification**: Integrates well with FastAPI and provides powerful templating features

### Bootstrap 5
- **Purpose**: Frontend CSS framework for responsive UI design
- **Justification**: Provides a consistent, mobile-friendly UI that works well across different devices

### JavaScript (Vanilla)
- **Purpose**: Client-side interactivity and AJAX requests
- **Justification**: Provides necessary frontend functionality without requiring heavy frameworks

## Development & Deployment

### Conda Environment
- **Python Version**: 3.9
- **Purpose**: Isolated environment for running the application
- **Justification**: Conda provides excellent package management and environment isolation, especially important on Raspberry Pi

### Pillow
- **Version**: 9.5.0
- **Purpose**: Image processing library
- **Justification**: Handles image manipulation and processing for uploaded and pasted images

## Testing

### Pytest
- **Version**: 7.3.1
- **Purpose**: Testing framework for API endpoints and functionality
- **Justification**: Simple, scalable testing framework for Python applications

### HTTPX
- **Version**: 0.24.0
- **Purpose**: HTTP client for testing API endpoints
- **Justification**: Modern, fully featured HTTP client for Python with async support

## External APIs and Services

### Google Maps Distance Matrix API
- **Purpose**: Accurate travel time calculations with real traffic data
- **Implementation**: TravelTimeService class handles API calls and fallback logic
- **Features**: 
  - Range-based travel times (e.g., "10-18 min")
  - Traffic-aware calculations for 8:30 AM Monday departures
  - Conservative planning using upper range values
- **Security**: API key stored as environment variable (`GOOGLE_MAPS_API_KEY`)
- **Fallback**: OpenStreetMap Nominatim geocoding for basic distance estimation

### OpenStreetMap Nominatim
- **Purpose**: Fallback geocoding service when Google Maps API is unavailable
- **Implementation**: Used for basic distance calculations without API key
- **Justification**: Free alternative ensuring app functionality without paid API
