// Global variables
let allProperties = [];
let filteredProperties = [];

// Color scheme for distance ranking
const distanceColors = [
    '#28a745', // Green - Closest
    '#20c997', // Teal - 2nd
    '#ffc107', // Yellow - 3rd
    '#fd7e14', // Orange - 4th
    '#dc3545'  // Red - 5th
];

async function loadProperties() {
    try {
        const response = await fetch('/api/properties/');
        if (!response.ok) {
            throw new Error('Failed to fetch properties');
        }
        
        const properties = await response.json();
        allProperties = properties;
        filteredProperties = properties;
        
        // Rank properties by distance and display them
        rankPropertiesByDistance(properties);
        displayProperties(properties);
    } catch (error) {
        console.error('Error loading properties:', error);
        document.getElementById('propertyListContainer').innerHTML = 
            '<div class="col-12 text-center py-5"><div class="alert alert-danger">Error loading properties. Please try again later.</div></div>';
    }
}

function rankPropertiesByDistance(properties) {
    // Filter properties that have travel time data
    const propertiesWithTimes = properties.filter(p => 
        p.travel_time_830am !== null && 
        p.travel_time_830am !== undefined && 
        !isNaN(p.travel_time_830am)
    );
    
    // Sort by Monday 8:30 AM travel time (ascending - shortest first)
    propertiesWithTimes.sort((a, b) => a.travel_time_830am - b.travel_time_830am);
    
    // Assign colors to top 5 closest properties
    propertiesWithTimes.slice(0, 5).forEach((property, index) => {
        property.distanceRank = index;
        property.distanceColor = distanceColors[index];
    });
    
    console.log('Ranked properties:', propertiesWithTimes.map(p => ({
        address: p.address,
        travel_time: p.travel_time_830am,
        rank: p.distanceRank,
        color: p.distanceColor
    })));
}

function displayProperties(properties) {
    const container = document.getElementById('propertyListContainer');
    container.innerHTML = '';
    
    if (properties.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <p>No properties found. <a href="/properties/new">Add your first property</a>.</p>
            </div>
        `;
        return;
    }
    
    const template = document.getElementById('propertyCardTemplate');
    
    properties.forEach(property => {
        const clone = template.content.cloneNode(true);
        
        // Set property details
        clone.querySelector('.property-address').textContent = property.address;
        clone.querySelector('.property-type').textContent = property.property_type;
        clone.querySelector('.property-price').textContent = `$${property.price_per_month.toLocaleString()}/month`;
        clone.querySelector('.property-sqft').textContent = property.square_footage.toLocaleString();
        
        // Make entire card clickable
        const card = clone.querySelector('.property-card');
        card.addEventListener('click', () => {
            window.location.href = `/properties/${property.id}`;
        });
        
        // Add hover effects
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'scale(0.88)';
            card.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'scale(0.85)';
            card.style.boxShadow = '';
        });
        
        // Set amenities
        if (property.cat_friendly) {
            clone.querySelector('.amenity.cat-friendly').classList.remove('d-none');
        }
        if (property.air_conditioning) {
            clone.querySelector('.amenity.air-conditioning').classList.remove('d-none');
        }
        if (property.on_premises_parking) {
            clone.querySelector('.amenity.parking').classList.remove('d-none');
        }
        
        // Set image if available
        const mainImage = property.images.find(img => img.is_main);
        const imgElement = clone.querySelector('.property-image');
        const noImageElement = clone.querySelector('.no-image');
        
        if (mainImage) {
            imgElement.src = `/static/images/property_${property.id}/${mainImage.filename}`;
            imgElement.classList.add('visible');
            noImageElement.classList.add('d-none');
        } else {
            imgElement.classList.remove('visible');
            noImageElement.classList.remove('d-none');
        }
        
        // Set distance indicator - THIS IS THE KEY PART
        const distanceIndicator = clone.querySelector('.distance-indicator');
        if (property.distanceRank !== undefined && property.distanceColor) {
            distanceIndicator.style.backgroundColor = property.distanceColor;
            distanceIndicator.style.display = 'inline-block';
            console.log(`Setting color for property ${property.id}: ${property.distanceColor}`);
        } else {
            console.log(`No color for property ${property.id}, rank: ${property.distanceRank}, color: ${property.distanceColor}`);
        }
        
        container.appendChild(clone);
    });
}

// Search functionality
window.performSearch = function(query, searchType) {
    const searchQuery = query.toLowerCase();
    
    if (!searchQuery) {
        filteredProperties = allProperties;
    } else {
        filteredProperties = allProperties.filter(property => {
            switch(searchType) {
                case 'address':
                    return property.address.toLowerCase().includes(searchQuery);
                case 'type':
                    return property.property_type.toLowerCase().includes(searchQuery);
                case 'rent':
                    return property.price_per_month.toString().includes(searchQuery);
                case 'size':
                    return property.square_footage.toString().includes(searchQuery);
                case 'all':
                default:
                    return property.address.toLowerCase().includes(searchQuery) ||
                           property.property_type.toLowerCase().includes(searchQuery) ||
                           property.price_per_month.toString().includes(searchQuery) ||
                           property.square_footage.toString().includes(searchQuery);
            }
        });
    }
    
    // Re-rank the filtered properties
    rankPropertiesByDistance(filteredProperties);
    displayProperties(filteredProperties);
};

// Handle URL search parameters
function handleSearchParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const searchQuery = urlParams.get('search');
    const searchType = urlParams.get('type') || 'all';
    
    if (searchQuery) {
        // Update search form if it exists
        const searchInput = document.getElementById('searchInput');
        const searchTypeSelect = document.getElementById('searchType');
        
        if (searchInput) searchInput.value = searchQuery;
        if (searchTypeSelect) searchTypeSelect.value = searchType;
        
        // Perform search
        window.performSearch(searchQuery, searchType);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', async function() {
    await loadProperties();
    handleSearchParams();
});

// Scroll to bottom functionality
document.addEventListener('DOMContentLoaded', function() {
    const scrollBtn = document.getElementById('scrollToBottomBtn');
    if (scrollBtn) {
        scrollBtn.addEventListener('click', () => {
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: 'smooth'
            });
        });
    }
});
