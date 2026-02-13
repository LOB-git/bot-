import argparse
import os
import logging
from PIL import Image

def process_image_frame(img, target_size):
    """
    Helper function: Crops an image to fill the target_size (Zoom to Fill).
    Returns the processed PIL Image.
    """
    # Calculate aspect ratios
    target_ratio = target_size[0] / target_size[1]
    img_ratio = img.width / img.height
    
    if img_ratio > target_ratio:
        # Image is wider than target: Crop width
        new_width = int(img.height * target_ratio)
        offset = (img.width - new_width) // 2
        img = img.crop((offset, 0, offset + new_width, img.height))
    else:
        # Image is taller than target: Crop height
        new_height = int(img.width / target_ratio)
        offset = (img.height - new_height) // 2
        img = img.crop((0, offset, img.width, offset + new_height))
        
    # Resize to final high-res dimensions
    img = img.resize(target_size, Image.LANCZOS)
    
    return img

def create_instagram_story(input_path, output_path):
    """
    Converts an image to Instagram Story format (9:16)
    by cropping it to fill the screen.
    """
    try:
        # Open the image
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            # Target dimensions for Instagram Story
            target_size = (2160, 3840)
            
            final_image = process_image_frame(img, target_size)
            
            # Save
            final_image.save(output_path, format="JPEG", quality=95, subsampling=0)
            dest = output_path if isinstance(output_path, str) else "memory buffer"
            logging.info(f"Success! Saved to: {dest}")
        
    except Exception as e:
        logging.error(f"Error: {e}")

def create_two_pic_story(input1, input2, output_path):
    """
    Creates a vertical split layout with two images.
    """
    try:
        with Image.open(input1) as img1, Image.open(input2) as img2:
            img1 = img1.convert("RGB")
            img2 = img2.convert("RGB")
            
            # Full canvas size
            canvas_size = (2160, 3840)
            # Half height for each picture
            half_size = (2160, 1920)
            
            # Process both images
            top_image = process_image_frame(img1, half_size)
            bottom_image = process_image_frame(img2, half_size)
            
            # Create canvas and paste
            canvas = Image.new("RGB", canvas_size)
            canvas.paste(top_image, (0, 0))
            canvas.paste(bottom_image, (0, 1920))
            
            # Save
            canvas.save(output_path, format="JPEG", quality=95, subsampling=0)
            dest = output_path if isinstance(output_path, str) else "memory buffer"
            logging.info(f"Success! Saved 2-layout to: {dest}")
            
    except Exception as e:
        logging.error(f"Error in 2-layout: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    parser = argparse.ArgumentParser(description="Convert image to Instagram Story (9:16)")
    parser.add_argument("input", nargs="?", help="Input image path")
    parser.add_argument("output", nargs="?", help="Output image path")
    args = parser.parse_args()
    
    # Interactive mode
    in_path = args.input or input("Drag and drop your image here: ").strip('"\' ')
    out_path = args.output
    
    if not out_path:
        # Auto-generate output name
        filename, ext = os.path.splitext(in_path)
        out_path = f"{filename}_story.jpg"
        
    create_instagram_story(in_path, out_path)
    input("\nDone. Press Enter to exit...")