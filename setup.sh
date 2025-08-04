#!/bin/bash

# Rental Recon Setup Script
echo "Setting up Rental Recon application..."

# Create conda environment if it doesn't exist
if ! conda info --envs | grep -q rental_recon; then
    echo "Creating conda environment 'rental_recon'..."
    conda create -y -n rental_recon python=3.9
else
    echo "Conda environment 'rental_recon' already exists."
fi

# Activate environment and install dependencies
echo "Installing dependencies..."
eval "$(conda shell.bash hook)"
conda activate rental_recon
pip install -r requirements.txt

# Create necessary directories if they don't exist
mkdir -p app/static/images
mkdir -p data

# Initialize database
echo "Initializing database..."
python -c "from app.database import Base, engine; from app.models.property import Property, PropertyImage; Base.metadata.create_all(bind=engine)"

echo "Setup complete!"
echo "To run the application, use: bash run.sh"
