import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
from utils.settings import config



def create_fancy_thumbnail(image, text, thumbnail_path, text_color, padding, wrap=35):
    print(f"Creating fancy thumbnail for: {text}")
    font_title_size = 47
    font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), font_title_size)
    image_width, image_height = image.size
    lines = textwrap.wrap(text, width=wrap)
    
    # Calculate text height using getbbox instead of getsize
    text_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]) + (len(lines) - 1) * padding
    y = (image_height / 2) - (text_height / 2) + 30
    
    draw = ImageDraw.Draw(image)
    username_font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), 30)
    draw.text((205, 825), config["settings"]["channel_name"], font=username_font, fill=text_color, align="left")

    if len(lines) == 3:
        lines = textwrap.wrap(text, width=wrap + 10)
        font_title_size = 40
        font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), font_title_size)
        text_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]) + (len(lines) - 1) * padding
        y = (image_height / 2) - (text_height / 2) + 35
    elif len(lines) == 4:
        lines = textwrap.wrap(text, width=wrap + 10)
        font_title_size = 35
        font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), font_title_size)
        text_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]) + (len(lines) - 1) * padding
        y = (image_height / 2) - (text_height / 2) + 40
    elif len(lines) > 4:
        lines = textwrap.wrap(text, width=wrap + 10)
        font_title_size = 30
        font = ImageFont.truetype(os.path.join("fonts", "Roboto-Bold.ttf"), font_title_size)
        text_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]) + (len(lines) - 1) * padding
        y = (image_height / 2) - (text_height / 2) + 30

    for line in lines:
        bbox = font.getbbox(line)
        line_height = bbox[3] - bbox[1]
        draw.text((120, y), line, font=font, fill=text_color, align="left")
        y += line_height + padding
    
    image.save(thumbnail_path)
    
    print ("Fancy thumbnail created successfully!")


def crop_and_resize_image(input_image_path: str, output_image_path: str, target_size=(1920, 1080)):
    
    with Image.open(input_image_path) as img:
        # Convert image to RGBA (if not already in that mode)
        img = img.convert("RGBA")
        
        # Get the bounding box of the non-blank area
        bbox = img.getbbox()
        cropped_img = img.crop(bbox)
        
        # Resize to target size
        resized_img = cropped_img.resize(target_size, Image.LANCZOS)
        resized_img.save(output_image_path)
    
    print(f"Cropped and resized image saved to {output_image_path}")