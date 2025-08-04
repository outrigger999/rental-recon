# Image Optimization Scripts

This directory contains scripts for managing and optimizing property images.

## optimize_existing_images.py

This script optimizes all existing property images in the database by reducing their file size and converting them to a consistent format (JPEG).

### Features

- Optimizes all images in the `app/static/images/property_*` directories
- Converts HEIC/HEIF images to JPEG
- Reduces file size while maintaining visual quality
- Updates database references to point to the optimized images
- Supports dry-run mode for testing

### Usage

```bash
# Run with default settings (makes actual changes)
python scripts/optimize_existing_images.py

# Dry run (shows what would be changed without making any changes)
python scripts/optimize_existing_images.py --dry-run

# Specify a custom images directory
python scripts/optimize_existing_images.py --dir /path/to/images
```

### Output

The script logs its progress to both the console and a file named `optimize_images.log` in the current directory.

### Requirements

- Python 3.7+
- Dependencies listed in `requirements.txt`

## Best Practices

1. **Backup your database** before running the script in production
2. Test with `--dry-run` first to see what changes would be made
3. Run the script during off-peak hours for large image collections
4. Monitor the log file for any errors during processing

## Note

This script is designed to be idempotent - it can be run multiple times without causing issues. It will skip already optimized files (those with `_optimized` in the filename).
