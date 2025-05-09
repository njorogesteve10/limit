from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from PIL import Image, ImageDraw
import traceback
import uuid
import time
from werkzeug.utils import secure_filename
import sys
import logging

# Add compatibility for ANTIALIAS or LANCZOS
try:
    # For Pillow 9.0.0 and newer
    from PIL import Image, ImageOps
    LANCZOS = Image.Resampling.LANCZOS
except (ImportError, AttributeError):
    # For Pillow 8.x.x and older
    LANCZOS = Image.ANTIALIAS

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app with proper static folder configuration
app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Create necessary directories
os.makedirs('uploads', exist_ok=True)
os.makedirs('outputs', exist_ok=True)
os.makedirs('assets', exist_ok=True)

# Ensure static directory exists and is properly configured
static_dir = os.path.join(os.getcwd(), 'static')
os.makedirs(static_dir, exist_ok=True)
logger.info(f"Static directory: {static_dir}")
logger.info(f"Static directory exists: {os.path.exists(static_dir)}")

# Create outputs subdirectory in static for videos
videos_dir = os.path.join(app.static_folder, 'videos')
os.makedirs(videos_dir, exist_ok=True)
logger.info(f"Videos directory: {videos_dir}")
logger.info(f"Videos directory exists: {os.path.exists(videos_dir)}")

# Add route for videos
@app.route('/videos/<filename>')
def serve_video(filename):
    """
    Serve video files from the videos directory.
    """
    try:
        # Get the full path to the video file
        file_path = os.path.join(videos_dir, filename)
        logger.info(f"=== Video Request ===")
        logger.info(f"Requested filename: {filename}")
        logger.info(f"Full path: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found at path: {file_path}")
            return jsonify({'error': 'File not found'}), 404
            
        # Serve the file with proper headers
        response = send_file(
            file_path,
            mimetype='video/mp4',
            as_attachment=False,
            download_name=filename,
            conditional=True,
            max_age=0
        )
        
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"=== Error Serving Video ===")
        logger.error(f"Error: {str(e)}")
        logger.error(error_details)
        return jsonify({
            'error': f'Failed to serve video: {str(e)}',
            'details': error_details
        }), 500

# Add route for favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Create test Pepe image if it doesn't exist
def create_test_pepe_image():
    pepe_path = os.path.join('pepe_chainsaw.jpg')
    if not os.path.exists(pepe_path):
        logger.info("Creating test Pepe image...")
        img = Image.new('RGBA', (400, 400), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), "Test Pepe Image", fill=(255, 255, 255, 255))
        img.save(pepe_path, 'JPEG')
        logger.info(f"Created test Pepe image at: {pepe_path}")
        # Add chainsaw effect
        draw.rectangle([150, 150, 250, 250], outline=(255, 0, 0, 255), width=10)
        img.save(pepe_path, 'PNG')
        logger.info(f"Created test Pepe image at: {pepe_path}")

# Create test image at startup
create_test_pepe_image()

# Debug logging
logger.info("\n=== Flask Application Starting ===")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Static folder: {app.static_folder}")
logger.info(f"Pepe chainsaw image: {os.path.exists('pepe_chainsaw.jpg')}")

# Add before_request handler to log all requests
@app.before_request
def log_request():
    print(f"\n=== Request ===")
    print(f"Method: {request.method}")
    print(f"Path: {request.path}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Data: {request.get_data(as_text=True)}")
    print(f"=== End Request ===\n")

# Create and verify all necessary folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ASSETS_FOLDER = 'assets'

# Create directories if they don't exist
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, ASSETS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)
    print(f"{folder} directory exists: {os.path.exists(folder)}")

# Set up paths
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['ASSETS_FOLDER'] = ASSETS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Check for required files
required_files = [
    os.path.join(ASSETS_FOLDER, 'pepe_chainsaw.png'),
    os.path.join(ASSETS_FOLDER, 'chainsaw_sound.mp3')
]

for file_path in required_files:
    if not os.path.exists(file_path):
        print(f"Warning: Required file not found: {file_path}")
    else:
        print(f"Found required file: {file_path}")

# Import the animation generation function after monkey patch
from pepe_slash import create_slash_animation

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/')
def index():
    """Serve the static index.html file."""
    return app.send_static_file('index.html')

@app.route('/generate', methods=['POST'])
def generate_animation():
    """
    Endpoint to generate a Pepe slash animation.
    Accepts either an X handle or an uploaded image.
    """
    try:
        logger.info("=== Starting animation generation ===")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request data: {request.get_json()}")
        logger.info(f"Request form: {dict(request.form)}")
        logger.info(f"Request files: {dict(request.files)}")
        
        # Check if form data with file upload
        if request.files and 'profile_image' in request.files:
            profile_file = request.files['profile_image']
            logger.info(f"Received file upload: {profile_file.filename}")
            logger.info(f"File content type: {profile_file.content_type}")
            
            # If no file selected
            if profile_file.filename == '':
                logger.error("No file selected")
                return jsonify({'error': 'No file selected'}), 400
                
            # If file is valid
            if profile_file and allowed_file(profile_file.filename):
                # Secure the filename and save the file
                filename = secure_filename(profile_file.filename)
                timestamp = int(time.time())
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Check if upload directory exists
                upload_dir = os.path.dirname(file_path)
                if not os.path.exists(upload_dir):
                    logger.warning(f"Creating upload directory: {upload_dir}")
                    os.makedirs(upload_dir, exist_ok=True)
                
                profile_file.save(file_path)
                logger.info(f"Saved uploaded file to: {file_path}")
                logger.info(f"File size: {os.path.getsize(file_path)} bytes")
                logger.info(f"File exists: {os.path.exists(file_path)}")
                
                # Use the uploaded file for animation
                profile_source = file_path
                source_type = "uploaded_image"
            else:
                logger.error("Invalid file type")
                return jsonify({'error': 'File type not allowed. Please upload a PNG, JPG, JPEG, or GIF'}), 400
        else:
            # Check for JSON data with X handle
            data = request.get_json() or {}
            x_handle = data.get('x_handle', '').strip()
            logger.info(f"Received X handle: {x_handle}")
            
            # Validate X handle
            if not x_handle:
                logger.error("No X handle provided")
                return jsonify({'error': 'Either an X handle or an image upload is required'}), 400
            if x_handle.startswith('@'):
                x_handle = x_handle[1:]  # Remove @ if present
            
            # Use X handle for animation
            profile_source = x_handle
            source_type = "x_handle"
        
        # Get Pepe image path
        pepe_image_path = os.path.join('pepe_chainsaw.jpg')
        logger.info(f"Using Pepe image: {pepe_image_path}")
        logger.info(f"Pepe image exists: {os.path.exists(pepe_image_path)}")
        
        # Create unique output filename
        output_filename = f"pepe_slash_{uuid.uuid4()}.mp4"
        # Save in videos subdirectory of static for proper serving
        output_path = os.path.join(videos_dir, output_filename)
        logger.info(f"Creating animation at: {output_path}")
        logger.info(f"Absolute output path: {os.path.abspath(output_path)}")
        logger.info(f"Videos directory exists: {os.path.exists(videos_dir)}")
        
        # Ensure the videos directory exists and is writable
        if not os.path.exists(videos_dir):
            logger.error(f"Videos directory does not exist: {videos_dir}")
            return jsonify({
                'error': 'Videos directory not found',
                'details': f'Could not find or create videos directory: {videos_dir}'
            }), 500
            
        # Generate the animation
        create_slash_animation(profile_source, pepe_image_path, output_path, duration=5.0)
        logger.info(f"Animation generated successfully: {output_path}")
        logger.info(f"Output file exists: {os.path.exists(output_path)}")
        
        # Check output directory permissions
        if os.path.exists(OUTPUT_FOLDER):
            logger.info(f"Output directory permissions: {oct(os.stat(OUTPUT_FOLDER).st_mode)}")
            logger.info(f"Output directory contents: {os.listdir(OUTPUT_FOLDER)}")
            # Check if we can write to the directory
            test_file = os.path.join(OUTPUT_FOLDER, 'test_write.txt')
            try:
                with open(test_file, 'w') as f:
                    f.write('Test write')
                logger.info(f"Successfully wrote test file to {test_file}")
                os.remove(test_file)
            except Exception as write_error:
                logger.error(f"Error testing write permissions: {str(write_error)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise Exception(f"Cannot write to output directory: {str(write_error)}")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(app.static_folder):
            logger.warning(f"Creating static directory: {app.static_folder}")
            os.makedirs(app.static_folder, exist_ok=True)
        
        # Generate the animation
        pepe_image_path = 'pepe_chainsaw.jpg'
        logger.info(f"Using Pepe image: {pepe_image_path}")
        logger.info(f"Pepe image exists: {os.path.exists(pepe_image_path)}")
        
        # Check if Pepe image exists
        if not os.path.exists(pepe_image_path):
            logger.error(f"Pepe image not found at {pepe_image_path}")
            return jsonify({
                'error': 'Pepe chainsaw image not found',
                'details': f'Could not find Pepe image at {pepe_image_path}'
            }), 500
            
        create_slash_animation(profile_source, pepe_image_path, output_path, duration=5.0)
        logger.info(f"Animation generated successfully: {output_path}")
        logger.info(f"Output file exists: {os.path.exists(output_path)}")
        
        # Return the video URL
        video_url = f'/videos/{output_filename}'
        logger.info(f"Returning video URL: {video_url}")
        logger.info(f"Video file exists: {os.path.exists(output_path)}")
        
        # Verify the file was created
        if not os.path.exists(output_path):
            return jsonify({
                'error': 'Failed to generate video',
                'details': f'Video file not found at: {output_path}'
            }), 500
        
        return jsonify({
            'success': True,
            'source': x_handle,
            'source_type': source_type,
            'video_url': video_url
        })
        
    except Exception as e:
        logger.error(f"Error during animation generation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': f'Failed to generate animation: {str(e)}',
            'details': traceback.format_exc()
        }), 500

@app.route('/videos/<filename>', methods=['GET'])
def download_file(filename):
    """
    Endpoint to serve the generated video file.
    """
    try:
        # Get the full path to the video file
        file_path = os.path.join(app.static_folder, 'videos', filename)
        logger.info(f"=== Video Request ===")
        logger.info(f"Requested filename: {filename}")
        logger.info(f"Full path: {file_path}")
        logger.info(f"File exists: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found at path: {file_path}")
            return jsonify({'error': 'File not found'}), 404
            
        # Serve the file with proper headers
        response = send_file(
            file_path,
            mimetype='video/mp4',
            as_attachment=False,
            download_name=filename,
            conditional=True,
            max_age=0
        )
        
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"=== Error Serving Video ===")
        logger.error(f"Error: {str(e)}")
        logger.error(error_details)
        return jsonify({
            'error': f'Failed to serve video: {str(e)}',
            'details': error_details
        }), 500
    """
    Endpoint to serve the generated video file.
    """
    try:
        file_path = os.path.join(app.static_folder, filename)
        print(f"=== Download Request ===")
        print(f"Requested filename: {filename}")
        print(f"Full path: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path):
            print(f"File not found at path: {file_path}")
            return jsonify({'error': 'File not found'}), 404
            
        # Get file details
        file_size = os.path.getsize(file_path)
        mod_time = os.path.getmtime(file_path)
        print(f"File size: {file_size} bytes")
        print(f"File modified: {time.ctime(mod_time)}")
        
        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1)  # Read first byte to verify file is readable
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return jsonify({'error': f'Cannot read file: {str(e)}'}), 500
        
        # Serve the file with proper headers
        response = send_file(
            file_path,
            mimetype='video/mp4',
            as_attachment=False,
            download_name=filename,
            conditional=True,
            max_age=0
        )
        
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"=== Error Serving File ===")
        print(f"Error: {str(e)}")
        print(error_details)
        return jsonify({
            'error': f'Failed to serve file: {str(e)}',
            'details': error_details
        }), 500

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """
    Endpoint to clean up old files (can be called periodically).
    """
    try:
        # Get current time
        current_time = time.time()
        # Files older than 24 hours will be deleted
        max_age = 24 * 60 * 60
        
        # Clean up uploads folder
        files_removed = 0
        for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    # Check file age
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age:
                        os.remove(file_path)
                        files_removed += 1        
        return jsonify({
            'success': True,
            'message': f'Cleanup completed. {files_removed} files removed.'
        })
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error during cleanup: {str(e)}")
        print(error_details)
        return jsonify({
            'error': f'Failed to clean up files: {str(e)}',
            'details': error_details
        }), 500

if __name__ == "__main__":
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5001)