#!/usr/bin/env python3
"""
Script to optimize all existing property images in the database.

This script will:
1. Find all property images in the database
2. Optimize each image for web use
3. Replace the original with the optimized version
4. Update the database with the new filename if the format changed
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('optimize_images.log')
    ]
)
logger = logging.getLogger(__name__)

# Import database models after setting up the path
from app.database import SessionLocal, engine
from app.models.property import Property, PropertyImage
from app.services.image_processor import ImageProcessor

class ImageOptimizer:
    """Handles optimization of existing images."""
    
    def __init__(self, base_dir: str = "app/static/images"):
        """Initialize with the base directory for property images."""
        self.base_dir = os.path.abspath(base_dir)
        self.image_processor = ImageProcessor()
        self.db = SessionLocal()
        
    def get_all_property_dirs(self) -> List[str]:
        """Get all property image directories."""
        try:
            return [
                os.path.join(self.base_dir, d) 
                for d in os.listdir(self.base_dir) 
                if d.startswith('property_') and os.path.isdir(os.path.join(self.base_dir, d))
            ]
        except FileNotFoundError:
            logger.error(f"Base directory not found: {self.base_dir}")
            return []
    
    def get_images_in_dir(self, dir_path: str) -> List[Tuple[str, str]]:
        """Get all image files in a directory."""
        if not os.path.exists(dir_path):
            return []
            
        image_exts = {'.jpg', '.jpeg', '.png', '.webp'}
        return [
            (f, os.path.join(dir_path, f)) 
            for f in os.listdir(dir_path)
            if os.path.splitext(f)[1].lower() in image_exts
        ]
    
    def optimize_image(self, image_path: str) -> Optional[Tuple[bytes, str]]:
        """Optimize a single image file."""
        try:
            # Skip already optimized files (assuming they end with _optimized)
            if '_optimized' in image_path:
                return None
                
            # Read the image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Process the image
            processed_data = self.image_processor.optimize_image(
                image_data,
                target_format='JPEG',  # for consistency
            )
            
            # Generate new filename
            old_filename = os.path.basename(image_path)
            name, ext = os.path.splitext(old_filename)
            new_filename = f"{name}_optimized.jpg"
            
            return processed_data, new_filename
            
        except Exception as e:
            logger.error(f"Error optimizing {image_path}: {str(e)}")
            return None
    
    def update_database_references(
        self, 
        property_id: int, 
        old_filename: str, 
        new_filename: str,
        image_data: bytes = None,
        original_format: str = None
    ) -> bool:
        """
        Update the database with the new filename and metadata.
        
        Args:
            property_id: ID of the property
            old_filename: Original filename in the database
            new_filename: New filename after optimization
            image_data: The processed image data (for extracting metadata)
            original_format: Original format of the image if it was converted
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Find the image in the database
            db_image = self.db.query(PropertyImage).filter(
                PropertyImage.property_id == property_id,
                PropertyImage.filename == old_filename
            ).first()
            
            if not db_image:
                logger.warning(f"No database entry found for {old_filename}")
                return False
                
            # Update the filename
            db_image.filename = new_filename
            
            # If we have image data, extract and update metadata
            if image_data is not None:
                try:
                    # Open the image to get dimensions
                    from io import BytesIO
                    from PIL import Image
                    
                    img = Image.open(BytesIO(image_data))
                    width, height = img.size
                    
                    # Update metadata fields
                    db_image.width = width
                    db_image.height = height
                    db_image.format = img.format.upper() if hasattr(img, 'format') and img.format else 'JPEG'
                    db_image.size_kb = len(image_data) / 1024.0  # Convert to KB
                    db_image.is_optimized = True
                    db_image.original_format = original_format.upper() if original_format else None
                    
                    logger.info(f"Updated metadata for {new_filename}: {width}x{height}px, {db_image.format}, {db_image.size_kb:.1f}KB")
                    
                except Exception as e:
                    logger.error(f"Error extracting metadata for {new_filename}: {str(e)}")
                    # Don't fail the whole operation if metadata extraction fails
            
            self.db.commit()
            logger.info(f"Updated database reference: {old_filename} -> {new_filename}")
            return True
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating database for {old_filename}: {str(e)}")
            return False
    
    def process_all_images(self, dry_run: bool = False) -> None:
        """Process all images in all property directories."""
        property_dirs = self.get_all_property_dirs()
        logger.info(f"Found {len(property_dirs)} property directories to process")
        
        total_processed = 0
        total_optimized = 0
        total_errors = 0
        
        for prop_dir in property_dirs:
            try:
                # Extract property ID from directory name
                prop_id = int(prop_dir.split('_')[-1])
                logger.info(f"Processing property {prop_id} - {prop_dir}")
                
                # Get all images in the directory
                images = self.get_images_in_dir(prop_dir)
                logger.info(f"Found {len(images)} images to process")
                
                for filename, full_path in images:
                    total_processed += 1
                    logger.info(f"Processing {filename}")
                    
                    # Skip already optimized files
                    if '_optimized' in filename:
                        logger.info(f"Skipping already optimized file: {filename}")
                        continue
                    
                    # Optimize the image
                    try:
                        # Get the original format before optimization
                        original_ext = os.path.splitext(filename)[1].lower().lstrip('.')
                        if original_ext in ['heic', 'heif']:
                            original_format = original_ext.upper()
                        else:
                            original_format = None
                            
                        # Optimize the image
                        result = self.optimize_image(full_path)
                        if not result:
                            logger.warning(f"Skipping {filename} (optimization failed or not needed)")
                            total_errors += 1
                            continue
                        
                        processed_data, new_filename = result
                        new_path = os.path.join(prop_dir, new_filename)
                    except Exception as e:
                        logger.error(f"Error processing {filename}: {str(e)}")
                        total_errors += 1
                        continue
                    
                    if dry_run:
                        logger.info(f"[DRY RUN] Would optimize {filename} -> {new_filename}")
                        continue
                        
                    # Save the optimized image
                    try:
                        with open(new_path, 'wb') as f:
                            f.write(processed_data)
                        
                        # Update database references with metadata
                        if self.update_database_references(
                            prop_id, 
                            filename, 
                            new_filename,
                            image_data=processed_data,
                            original_format=original_format
                        ):
                            # Remove the old file if optimization was successful and database updated
                            try:
                                os.remove(full_path)
                                logger.info(f"Removed original file: {filename}")
                            except Exception as e:
                                logger.error(f"Error removing original file {filename}: {str(e)}")
                        
                        total_optimized += 1
                        logger.info(f"Successfully optimized {filename} -> {new_filename}")
                        
                    except Exception as e:
                        logger.error(f"Error saving optimized image {new_filename}: {str(e)}")
                        total_errors += 1
            
            except Exception as e:
                logger.error(f"Error processing property directory {prop_dir}: {str(e)}")
                total_errors += 1
        
        # Print summary
        logger.info("\n=== Optimization Complete ===")
        logger.info(f"Total images processed: {total_processed}")
        logger.info(f"Total images optimized: {total_optimized}")
        logger.info(f"Total errors: {total_errors}")
        
        if dry_run:
            logger.info("\nThis was a dry run. No changes were made to files or database.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimize all property images.')
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Run without making any changes to files or database'
    )
    parser.add_argument(
        '--dir',
        type=str,
        default="app/static/images",
        help='Base directory containing property image folders'
    )
    
    args = parser.parse_args()
    
    optimizer = ImageOptimizer(base_dir=args.dir)
    optimizer.process_all_images(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
