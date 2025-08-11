# QuickBatch
A multifunctional utility for video file processing, offering standardized renaming and audio-video merging.

## Features
The script provides two main functions:
1. **Batch File Renaming**: Renames video files based on their language prefix, resolution, and duration.
2. **Batch Audio-Video Merging**: Combines audio and video files in bulk.

## How to Use
Run the `.bat` file to execute the Python script. Ensure your video files are located in the same directory as the `.bat` file.

## Logic Rules
- All files will be moved to folders based on their language prefix.
- The language prefix is determined by the first two characters of the file name (e.g., `de_asddas.mp4` is assigned the `DE` language prefix).
- If a file does not have a language prefix, it is automatically assigned the `EN` prefix.
- Audio file have to be located above language prefix folders 

## Example
Suppose you have a video file named `de_asddas.mp4` with a duration of 90 seconds and a resolution of 1920x1080. After running the renaming function, the file will be renamed to `my_custom_name_90s_de_1920x1080.mp4`.
