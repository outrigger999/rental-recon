import os
import io
from pathlib import Path
from typing import Tuple, Optional, Union, BinaryIO
from PIL import Image, ImageOps

class ImageProcessor:
    """
    Handles image processing tasks including optimization and format conversion.
    """
    
    # Target formats and their settings
    FORMAT_SETTINGS = {
        'JPEG': {
            'quality': 85,  # Quality setting (1-100)
            'optimize': True,
            'progressive': True,
            'dpi': (72, 72)  # Standard screen DPI
        },
        'PNG': {
            'optimize': True,
            'compress_level': 6,  # 1-9, 9 being most compressed
            'dpi': (72, 72)
        },
        'WEBP': {
            'quality': 80,
            'method': 6,  # 0-6, higher is better compression but slower
            'lossless': False
        }
    }
    
    # Maximum dimensions for images (maintains aspect ratio)
    MAX_DIMENSIONS = (1920, 1080)  # Full HD resolution
    
    @classmethod
    def get_format(cls, filename: str) -> str:
        """Get the image format from filename."""
        ext = Path(filename).suffix.lower()
        if ext in ['.jpg', '.jpeg']:
            return 'JPEG'
        elif ext == '.png':
            return 'PNG'
        elif ext == '.webp':
            return 'WEBP'
        return 'JPEG'  # Default to JPEG
    
    @classmethod
    def optimize_image(
        cls,
        image_data: Union[bytes, BinaryIO],
        target_format: Optional[str] = None,
        max_dimensions: Optional[Tuple[int, int]] = None
    ) -> bytes:
        """
        Optimize an image by resizing and compressing it.
        
        Args:
            image_data: Binary image data or file-like object
            target_format: Target format ('JPEG', 'PNG', 'WEBP')
            max_dimensions: Optional max (width, height) to resize to
            
        Returns:
            Optimized image data as bytes
        """
        if max_dimensions is None:
            max_dimensions = cls.MAX_DIMENSIONS
            
        # Open the image
        img = Image.open(io.BytesIO(image_data) if isinstance(image_data, bytes) else image_data)
        
        # Convert to RGB if needed (for JPEG)
        if img.mode in ('RGBA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if needed
        img.thumbnail(max_dimensions, Image.LANCZOS)
        
        # Determine output format
        if target_format is None:
            target_format = 'JPEG'  # Default to JPEG
        target_format = target_format.upper()
        
        # Get format settings
        format_settings = cls.FORMAT_SETTINGS.get(target_format, cls.FORMAT_SETTINGS['JPEG'])
        
        # Save to bytes buffer
        output = io.BytesIO()
        img.save(
            output,
            format=target_format,
            **{k: v for k, v in format_settings.items() if k != 'dpi'}
        )
        
        # If we have DPI settings, apply them
        if 'dpi' in format_settings:
            img.info['dpi'] = format_settings['dpi']
        
        return output.getvalue()
    
    @classmethod
    def process_uploaded_file(
        cls,
        file: 'UploadFile',
        target_format: Optional[str] = None,
        max_dimensions: Optional[Tuple[int, int]] = None
    ) -> Tuple[bytes, str, dict]:
        """
        Process an uploaded file and optimize it for web use.
        
        Args:
            file: FastAPI UploadFile object
            target_format: Target format ('JPEG', 'PNG', 'WEBP')
            max_dimensions: Optional max (width, height) to resize to
            
        Returns:
            Tuple of (optimized_image_data, new_filename, metadata_dict)
            where metadata_dict contains: width, height, format, size_kb, is_optimized, original_format
        """
        from io import BytesIO
        from PIL import Image as PILImage
        
        # Read the file data
        file_data = file.file.read()
        
        # Get original image info
        original_format = cls.get_format(file.filename)
        with BytesIO(file_data) as img_io:
            with PILImage.open(img_io) as img:
                original_width, original_height = img.size
        
        # Determine the target format
        if target_format is None:
            target_format = cls.get_format(file.filename)
        
        # Optimize the image
        optimized_data = cls.optimize_image(
            file_data,
            target_format=target_format,
            max_dimensions=max_dimensions
        )
        
        # Get optimized image info
        with BytesIO(optimized_data) as img_io:
            with PILImage.open(img_io) as img:
                optimized_width, optimized_height = img.size
        
        # Create new filename with correct extension
        filename = Path(file.filename).stem + f'.{target_format.lower()}'
        
        # Prepare metadata
        metadata = {
            'width': optimized_width,
            'height': optimized_height,
            'format': target_format.upper(),
            'size_kb': len(optimized_data) / 1024,  # Convert to KB
            'is_optimized': True,
            'original_format': original_format.upper() if original_format.upper() != target_format.upper() else None
        }
        
        return optimized_data, filename, metadata
    @classmethod
    def process_base64_image(
        cls,
        base64_data: str,
        target_format: str = 'JPEG',
        max_dimensions: Optional[Tuple[int, int]] = None
    ) -> Tuple[bytes, dict]:
        """
        Process a base64 encoded image.
        
        Args:
            base64_data: Base64 encoded image data (with or without data URL)
            target_format: Target format ('JPEG', 'PNG', 'WEBP')
            max_dimensions: Optional max (width, height) to resize to
            
        Returns:
            Tuple of (optimized_image_data, metadata_dict)
            where metadata_dict contains: width, height, format, size_kb, is_optimized
        """
        from io import BytesIO
        from PIL import Image as PILImage
        
        # Remove data URL prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',', 1)[1]
            
        # Decode base64
        image_data = base64.b64decode(base64_data)
        
        # Get original image info
        with BytesIO(image_data) as img_io:
            with PILImage.open(img_io) as img:
                original_format = img.format or 'UNKNOWN'
                original_width, original_height = img.size
        
        # Optimize the image
        optimized_data = cls.optimize_image(
            image_data,
            target_format=target_format,
            max_dimensions=max_dimensions
        )
        
        # Get optimized image info
        with BytesIO(optimized_data) as img_io:
            with PILImage.open(img_io) as img:
                optimized_width, optimized_height = img.size
        
        # Prepare metadata
        metadata = {
            'width': optimized_width,
            'height': optimized_height,
            'format': target_format.upper(),
            'size_kb': len(optimized_data) / 1024,  # Convert to KB
            'is_optimized': True,
            'original_format': original_format.upper() if original_format.upper() != target_format.upper() else None
        }
        
        return optimized_data, metadata

    @classmethod
    def process_existing_image(
        cls,
        image_path: str,
        target_format: Optional[str] = None,
        max_dimensions: Optional[Tuple[int, int]] = None
    ) -> bytes:
        """
        Process an existing image file on disk.
        
        Args:
            image_path: Path to the image file
            target_format: Target format ('JPEG', 'PNG', 'WEBP')
            max_dimensions: Optional max (width, height) to resize to
            
        Returns:
            Optimized image data as bytes
        """
        if target_format is None:
            target_format = cls.get_format(image_path)
            
        with open(image_path, 'rb') as f:
            return cls.optimize_image(f, target_format=target_format, max_dimensions=max_dimensions)
