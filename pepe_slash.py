import requests
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from io import BytesIO
import moviepy.editor as mpy
import os
import numpy as np
import xml.etree.ElementTree as ET
import re
import math
import random
import tempfile

def fetch_profile_image(x_handle, target_size=(300, 300)):
    """
    Fetches the profile image with improved error handling and fallbacks.
    """
    try:
        # Remove @ if present
        x_handle = x_handle.replace('@', '')
        
        # Try different profile image URLs (from highest to lowest quality)
        urls = [
            f"https://pbs.twimg.com/profile_images/{x_handle}/400x400.jpg",
            f"https://pbs.twimg.com/profile_images/{x_handle}/bigger.jpg",
            f"https://pbs.twimg.com/profile_images/{x_handle}/normal.jpg",
            f"https://unavatar.io/twitter/{x_handle}",  # Backup service
            f"https://images.weserv.nl/?url=https://twitter.com/{x_handle}/profile_image?size=original"
        ]
        
        last_error = None
        for url in urls:
            try:
                print(f"Trying to fetch profile image from: {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Try to open the image to verify it's valid
                img = Image.open(BytesIO(response.content))
                if img.size[0] < 50 or img.size[1] < 50:  # Skip tiny images
                    raise ValueError("Image too small")
                
                # Convert to RGBA and resize
                img = img.convert("RGBA")
                
                # Resize to our target size while maintaining aspect ratio
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Create a new image with exact target size and paste the thumbnail
                new_img = Image.new('RGBA', target_size, (0, 0, 0, 0))
                offset = ((target_size[0] - img.size[0]) // 2,
                         (target_size[1] - img.size[1]) // 2)
                new_img.paste(img, offset)
                
                print(f"Successfully fetched profile image for @{x_handle}")
                return np.array(new_img)
                
            except Exception as e:
                print(f"Failed to fetch from {url}: {str(e)}")
                last_error = e
                continue
        
        # Try one more time with a different URL format
        try:
            url = f"https://twitter.com/{x_handle}/photo"
            print(f"Trying direct profile page: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Extract image URL from HTML
            if 'profile-image' in response.text:
                img_url = re.search(r'src="(https://pbs.twimg.com/[^\"]+)"', response.text)
                if img_url:
                    img_url = img_url.group(1)
                    print(f"Found profile image URL: {img_url}")
                    img_response = requests.get(img_url, headers=headers, timeout=10)
                    img_response.raise_for_status()
                    img = Image.open(BytesIO(img_response.content))
                    img = img.convert("RGBA")
                    img.thumbnail(target_size, Image.Resampling.LANCZOS)
                    new_img = Image.new('RGBA', target_size, (0, 0, 0, 0))
                    offset = ((target_size[0] - img.size[0]) // 2,
                             (target_size[1] - img.size[1]) // 2)
                    new_img.paste(img, offset)
                    print(f"Successfully fetched profile image for @{x_handle}")
                    return np.array(new_img)
        except Exception as e:
            print(f"Failed to fetch from profile page: {str(e)}")
            last_error = e
            
        raise last_error or Exception("All URLs failed")
        
    except Exception as e:
        print(f"Failed to fetch profile image for @{x_handle}: {str(e)}")
        return create_placeholder_image((300, 300), x_handle)

def create_placeholder_image(size=(150, 150), username=""):
    """
    Creates a placeholder image when profile image fetch fails.
    """
    img = Image.new('RGBA', size, (29, 161, 242, 255))  # Twitter Blue background
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([0, 0, size[0]-1, size[1]-1], outline=(255, 255, 255, 255), width=3)
    
    # Draw text
    if username:
        text = f"@{username}"
        text_x = size[0] // 4
        text_y = size[1] // 2 - 10
        draw.text((text_x, text_y), text, fill=(255, 255, 255, 255))
    
    # Draw placeholder avatar circle
    circle_size = min(size[0], size[1]) // 2
    circle_pos = ((size[0] - circle_size) // 2, (size[1] - circle_size) // 2)
    draw.ellipse([circle_pos[0], circle_pos[1], 
                  circle_pos[0] + circle_size, circle_pos[1] + circle_size],
                 outline=(255, 255, 255, 255), width=3)
    
    return np.array(img)

def split_image_in_half(img):
    """
    Splits a PIL Image into left and right halves.
    """
    width, height = img.size
    left = img.crop((0, 0, width//2, height))
    right = img.crop((width//2, 0, width, height))
    return left, right

import random

def add_blood_drops(img, x, y, width, height):
    """Add realistic blood drops falling from the bottom of the chopping area"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Limit to 1-2 drops at a time
    num_drops = random.randint(1, 2)
    
    for i in range(num_drops):
        # Position drops at the bottom of the chopping area
        drop_x = x + random.randint(-width//4, width//4)  # Narrower range
        drop_y = y + height + random.randint(-10, 10)  # Start from bottom
        
        # Make drops more realistic
        drop_width = random.randint(12, 18)  # Smaller width
        drop_height = random.randint(25, 35)  # More natural height
        red = random.randint(200, 255)  # Slightly darker red
        alpha = random.randint(220, 255)  # More opaque
        
        # Draw main drop
        draw.ellipse(
            [drop_x, drop_y, drop_x + drop_width, drop_y + drop_height],
            fill=(red, 0, 0, alpha)
        )
        
        # Add small trail if this isn't the last frame
        if i < num_drops - 1:
            trail_length = random.randint(5, 10)
            trail_width = random.randint(2, 4)
            draw.line(
                [(drop_x + drop_width // 2, drop_y + drop_height),
                 (drop_x + drop_width // 2, drop_y + drop_height + trail_length)],
                fill=(red, 0, 0, alpha - 30),  # Slightly transparent trail
                width=trail_width
            )
    
    # Apply a very slight blur for realism
    img = img.filter(ImageFilter.GaussianBlur(0.3))
    
    # Add a subtle glow to make drops stand out
    glow = Image.new('RGBA', img.size, (255, 0, 0, 10))
    img = Image.alpha_composite(img, glow)
    return img

def create_slash_animation(profile_path_or_handle, pepe_image_path, output_path=None, duration=5.0):
    """
    Creates a 5-second animation with:
    - Optimized memory usage
    - Smooth performance
    - Engaging effects
    - Automatic saving to outputs folder with timestamp
    """
    try:
        # Set up animation parameters with optimized sizes
        canvas_width = 1280  # Reduced from 1920
        canvas_height = 720  # Reduced from 1080
        fps = 30  # Reduced from 60 to save memory
        total_frames = int(duration * fps)
        frames = []
        
        # Calculate timing for different phases
        approach_duration = duration * 0.2
        approach_frames = int(approach_duration * fps)
        
        chainsaw_duration = duration * 0.2
        chainsaw_frames = int(chainsaw_duration * fps)
        
        cut_duration = duration * 0.2
        cut_frames = int(cut_duration * fps)
        
        split_duration = duration * 0.4
        split_frames = int(split_duration * fps)
        
        # Create canvas and position elements
        profile_size = (300, 300)  # Reduced from 400
        
        # Load background image from root directory
        background = Image.open(pepe_image_path).convert("RGBA")
        
        # Resize background to fit canvas
        bg_width = int(canvas_width * 0.8)  # 80% of canvas width
        bg_height = int(background.size[1] * (bg_width / background.size[0]))
        background = background.resize((bg_width, bg_height), Image.Resampling.LANCZOS)
        
        # Add subtle glow effect to background
        glow = Image.new('RGBA', background.size, (255, 255, 255, 10))
        background = Image.alpha_composite(background, glow)
        
        # Position background
        bg_pos = (canvas_width // 2 - bg_width // 2, canvas_height // 2 - bg_height // 2)
        
        # Load Pepe image with optimized processing
        pepe_pil = Image.open(pepe_image_path).convert("RGBA")
        pepe_height = int(profile_size[1] * 1.2)  # Reduced from 1.5
        pepe_width = int(pepe_pil.size[0] * (pepe_height / pepe_pil.size[1]))
        pepe_pil = pepe_pil.resize((pepe_width, pepe_height), Image.Resampling.LANCZOS)
        
        # Add glow effect to Pepe with reduced intensity
        glow = Image.new('RGBA', pepe_pil.size, (255, 255, 255, 20))  # Reduced from 30
        pepe_img = Image.alpha_composite(pepe_pil, glow)
        
        # Load saw image
        saw_path = 'saww.jpg'
        if os.path.exists(saw_path):
            saw_img = Image.open(saw_path).convert("RGBA")
            # Make saw larger and more prominent
            saw_width = int(profile_size[1] * 0.8)  # 80% of profile height
            saw_height = int(saw_img.size[1] * (saw_width / saw_img.size[0]))
            saw_img = saw_img.resize((saw_width, saw_height), Image.Resampling.LANCZOS)
            
            # Add stronger glow effect to saw
            glow = Image.new('RGBA', saw_img.size, (255, 255, 255, 40))
            saw_img = Image.alpha_composite(saw_img, glow)
        else:
            logger.warning("Saw image not found, using default chainsaw effect")
            saw_img = None
        
        # Add glow effect to Pepe with reduced intensity
        glow = Image.new('RGBA', pepe_pil.size, (255, 255, 255, 20))  # Reduced from 30
        pepe_img = Image.alpha_composite(pepe_pil, glow)
        
        # Position Pepe (start from right side)
        pepe_pos = (canvas_width - pepe_width - 50, canvas_height - pepe_height - 50)
        
        # Fetch user's profile image (larger size)
        if os.path.exists(profile_path_or_handle):
            profile_img = Image.open(profile_path_or_handle).convert("RGBA")
            # Make profile bigger
            profile_size = (500, 500)
            profile_img = profile_img.resize(profile_size, Image.Resampling.LANCZOS)
        else:
            profile_img = Image.fromarray(fetch_profile_image(profile_path_or_handle, target_size=(500, 500)))
        
        # Position profile on chair (bottom of screen, moved up and right)
        profile_pos = (canvas_width // 2 + 50 - profile_size[0] // 2, canvas_height - profile_size[1] - 300)
        
        # Split the profile image into left and right halves
        left_half, right_half = split_image_in_half(profile_img)
        
        # Generate animation frames
        temp_dir = tempfile.mkdtemp()
        print(f"Created temporary directory: {temp_dir}")
        
        try:
            # Frame generation loop
            for i in range(total_frames):
                progress = i / total_frames
                frame_path = os.path.join(temp_dir, f'frame_{i:04d}.png')
                
                # Create a new canvas for this frame
                canvas = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 255))
                
                # Draw background image first
                canvas.paste(background, bg_pos, background)
                
                # Draw background Pepe (remove duplicate)
                # Only draw background Pepe once at the start
                if progress < 0.1:  # Only draw background Pepe in first frame
                    canvas.paste(pepe_img, pepe_pos, pepe_img)
                
                # Animation phases
                if progress < 0.2:  # Approach phase
                    phase_progress = progress / 0.2
                    
                    # Add subtle camera shake
                    shake_x = random.randint(-5, 5)
                    shake_y = random.randint(-5, 5)
                    canvas = canvas.transform(canvas.size, Image.AFFINE, (1, 0, shake_x, 0, 1, shake_y))
                    
                elif progress < 0.4:  # Profile approach phase
                    phase_progress = (progress - 0.2) / 0.2
                    
                    # Profile moves from right to bottom (slower and limited to half screen)
                    # Only move 50% of the way across the screen
                    profile_x = profile_pos[0] - ((canvas_width // 2) - profile_pos[0]) * phase_progress * 0.6
                    canvas.paste(profile_img, (int(profile_x), profile_pos[1]), profile_img)
                    
                elif progress < 0.6:  # Cutting phase
                    phase_progress = (progress - 0.4) / 0.2
                    
                    # Profile is now on the chair
                    canvas.paste(profile_img, profile_pos, profile_img)
                    
                    # Vertical cutting now
                    if saw_img:
                        # Position saw on profile
                        saw_x = profile_pos[0] + profile_size[0] // 2 - saw_width // 2
                        saw_y = profile_pos[1] + profile_size[1] // 2 - saw_height // 2
                        
                        # Animate saw moving vertically (slower)
                        saw_offset = int(10 * phase_progress)  # Slower movement
                        saw_x += int(5 * math.sin(phase_progress * math.pi))  # Side-to-side motion
                        
                        # Rotate saw slightly
                        saw_angle = math.sin(phase_progress * math.pi * 2) * 5
                        saw_rotated = saw_img.rotate(saw_angle, expand=True)
                        
                        # Add saw to canvas
                        canvas.paste(saw_rotated, (saw_x, saw_y + saw_offset), saw_rotated)
                        
                    # Add saw to canvas
                    canvas.paste(saw_rotated, (saw_x, saw_y + saw_offset), saw_rotated)
                    
                else:  # Split phase
                    phase_progress = (progress - 0.6) / 0.4
                    
                    # Split vertically
                    left_half = profile_img.crop((0, 0, profile_size[0] // 2, profile_size[1]))
                    right_half = profile_img.crop((profile_size[0] // 2, 0, profile_size[0], profile_size[1]))
                    
                    # Move halves apart horizontally with falling motion
                    offset = int(profile_size[0] * phase_progress)
                    
                    # Add rotation for dramatic effect
                    left_half = left_half.rotate(-10, expand=True)
                    right_half = right_half.rotate(10, expand=True)
                    
                    # Calculate falling positions
                    fall_offset = int(150 * phase_progress)  # Pieces fall 150 pixels
                    
                    # Add rotation that increases with falling
                    left_rotate = -10 - (phase_progress * 20)  # Rotate more as it falls
                    right_rotate = 10 + (phase_progress * 20)
                    
                    # Apply rotation
                    left_half = left_half.rotate(left_rotate, expand=True)
                    right_half = right_half.rotate(right_rotate, expand=True)
                    
                    canvas.paste(left_half, (profile_pos[0] - offset, profile_pos[1] + fall_offset), left_half)
                    canvas.paste(right_half, (profile_pos[0] + offset, profile_pos[1] + fall_offset), right_half)
                    
                    # Add blood drops
                    blood_progress = phase_progress
                    canvas = add_blood_drops(canvas, profile_pos[0], profile_pos[1], profile_size[0], profile_size[1])
                
                # Save frame with proper error handling
                try:
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(frame_path), exist_ok=True)
                    
                    # Save with proper quality settings
                    canvas.save(frame_path, 'PNG', quality=95)
                    frames.append(frame_path)
                    print(f"Generated frame {i+1}/{total_frames}")
                except Exception as e:
                    print(f"Error saving frame {i}: {str(e)}")
                    raise
                finally:
                    # Clear canvas memory
                    canvas.close()
            
            # Create video from frames
            try:
                # Ensure all frames exist before creating video
                for frame in frames:
                    if not os.path.exists(frame):
                        raise FileNotFoundError(f"Frame file not found: {frame}")
                
                video = mpy.ImageSequenceClip(frames, fps=fps)
                video.write_videofile(output_path, codec='libx264', fps=fps)
                print(f"Animation saved to {output_path}")
                return output_path
            except Exception as e:
                print(f"Error creating video: {str(e)}")
                raise
        except Exception as e:
            print(f"Error creating animation: {str(e)}")
            raise
        finally:
            # Clean up temporary files
            for frame in frames:
                try:
                    os.remove(frame)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass
    except Exception as e:
        print(f"Error in create_slash_animation: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # Check if required arguments are provided
        if len(sys.argv) < 3:
            print("Usage: python pepe_slash.py <profile_handle_or_path> <pepe_image_path> [output_path]")
            sys.exit(1)

        # Parse command line arguments
        profile_path_or_handle = sys.argv[1]
        pepe_image_path = sys.argv[2]
        
        # Create outputs directory if it doesn't exist
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"pepe_slash_{timestamp}.mp4")

        # Create animation
        create_slash_animation(profile_path_or_handle, pepe_image_path, output_path)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)