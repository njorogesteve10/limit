# Pepe Slash Animation Generator

This application generates a dynamic animation where Pepe the Frog uses a chainsaw to cut through a profile image. The animation includes realistic blood effects and falling pieces.

## Requirements

- Python 3.8 or higher
- Required Python packages:
  - PIL (Pillow)
  - moviepy
  - requests

## Installation

1. Install Python 3.8 or higher from https://www.python.org/downloads/

2. Install the required packages using pip:
```bash
pip install Pillow moviepy requests
```

## Usage

The script automatically saves animations to an "outputs" folder in the project directory. You only need to provide two command line arguments:

1. Profile Image Path: Path to the profile image you want to use
2. Pepe Image Path: Path to the Pepe chainsaw image

The output video will be automatically saved in the "outputs" folder with a timestamp in the filename, making it easy to keep track of different animations.

### Example Usage

```bash
python pepe_slash.py "path/to/profile.jpg" "path/to/pepe.jpg" "output.mp4"
```

### Using with Twitter/X Profile

If you want to use a Twitter/X profile image, you can provide the username as the first argument:

```bash
python pepe_slash.py "x_username" "path/to/pepe.jpg" "output.mp4"
```

The script will automatically fetch the profile image from Twitter/X.

## Features

- Dynamic animation with Pepe using a chainsaw
- Realistic blood drop effects
- Profile image splitting and falling motion
- Optimized performance and memory usage
- Automatic profile image fetching from Twitter/X
- Customizable output

## Output

The script will generate an MP4 video file at the specified output path (or "output.mp4" if not specified). The video will be 5 seconds long and show:
1. Pepe with chainsaw
2. Profile image approaching
3. Cutting animation with blood effects
4. Split pieces falling

## Troubleshooting

- If the profile image fails to load, make sure the path is correct
- If Twitter/X profile fetching fails, ensure you have internet connection
- If the output video is not created, check if you have write permissions in the output directory

## Notes

- The script uses optimized frame generation to save memory
- The animation is designed to be 1280x720 resolution
- The blood effects are designed to be realistic and natural-looking

## License

This project is for personal use only. Please respect copyright laws and terms of service when using this script.
#   l i m i t  
 # limit
