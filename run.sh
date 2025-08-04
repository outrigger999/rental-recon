#!/bin/bash

# Activate the conda environment
eval "$(conda shell.bash hook)"
conda activate rental_recon

# Run the FastAPI application
echo "Starting Rental Recon application..."
echo "Access the web interface at http://localhost:8000 or your Raspberry Pi's IP address"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
