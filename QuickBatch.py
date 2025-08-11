#!/usr/bin/env python3
"""
Video Renamer Script
Renames video files to format: customname_90s_en_1080x1920.mp4
and sorts them into language folders (EN, RU, etc.)
"""

import os
import re
import subprocess
import shutil
import sys
import tempfile
from pathlib import Path
from moviepy.editor import VideoFileClip


def get_video_metadata(file_path):
    """
    Gets video metadata: resolution and duration
    
    Args:
        file_path (str): Path to video file
        
    Returns:
        tuple: (resolution_str, duration_seconds) or (None, None) on error
    """
    try:
        with VideoFileClip(file_path) as clip:
            width = int(clip.w)
            height = int(clip.h)
            duration = int(clip.duration)
            
            resolution = f"{width}x{height}"
            return resolution, duration
    except Exception as e:
        print(f"Error getting metadata for {file_path}: {e}")
        return None, None


def extract_language_prefix(filename):
    """
    Extracts language prefix from filename.
    Supports two formats:
    1. XX_filename.mp4 (two letters + underscore at the beginning)  
    2. customname_30s_lang_1920x1080.mp4 (language between duration and resolution)
    Priority: first check format 2, then format 1
    If not found, returns "en" (English by default)
    
    Args:
        filename (str): Filename
        
    Returns:
        str: Language code in lowercase
    """
    name_without_ext = Path(filename).stem
    
    # Format 2 (HIGHEST PRIORITY): Look for _XXs_lang_XXXXxXXXX pattern anywhere in the name
    # This pattern should ALWAYS take precedence over prefix matching
    match_format = re.search(r'_(\d+s)_([a-zA-Z]{2,})_(\d+x\d+)', name_without_ext)
    if match_format:
        return match_format.group(2).lower()  # Return language code
    
    # Format 1: Only if format 2 not found, look for two letters + underscore at beginning
    match_prefix = re.match(r'^([a-zA-Z]{2})_', name_without_ext)
    if match_prefix:
        return match_prefix.group(1).lower()
    
    # If no pattern found, use English by default
    return "en"


def format_duration(seconds):
    """
    Formats duration in seconds as string
    
    Args:
        seconds (int): Duration in seconds
        
    Returns:
        str: Formatted duration (e.g., "90s")
    """
    return f"{seconds}s"


def generate_new_filename(custom_name, duration, lang_code, resolution):
    """
    Generates new filename in format: customname_90s_en_1080x1920.mp4
    
    Args:
        custom_name (str): Custom name
        duration (int): Duration in seconds
        lang_code (str): Language code (lowercase)
        resolution (str): Resolution in format "1920x1080"
        
    Returns:
        str: New filename
    """
    duration_str = format_duration(duration)
    new_name = f"{custom_name}_{duration_str}_{lang_code}_{resolution}.mp4"
    return new_name


def handle_duplicate_names(target_path):
    """
    Handles duplicate names by adding suffix _1, _2, etc.
    
    Args:
        target_path (Path): Target file path
        
    Returns:
        Path: Unique file path
    """
    if not target_path.exists():
        return target_path
    
    base_name = target_path.stem
    extension = target_path.suffix
    parent_dir = target_path.parent
    
    counter = 1
    while True:
        new_name = f"{base_name}_{counter}{extension}"
        new_path = parent_dir / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def create_language_folder(lang_code):
    """
    Creates folder for language (uppercase letters)
    
    Args:
        lang_code (str): Language code
        
    Returns:
        Path: Path to created folder
    """
    folder_name = lang_code.upper()
    folder_path = Path.cwd() / folder_name
    folder_path.mkdir(exist_ok=True)
    return folder_path


def organize_by_language(file_path, lang_code):
    """
    Moves file to corresponding language folder
    
    Args:
        file_path (Path): Path to file
        lang_code (str): Language code
        
    Returns:
        Path: New file path
    """
    lang_folder = create_language_folder(lang_code)
    target_path = lang_folder / file_path.name
    target_path = handle_duplicate_names(target_path)
    
    file_path.rename(target_path)
    return target_path


def extract_duration_from_audio_name(filename):
    """
    Extracts duration from audio filename
    Supports formats: 9s, 30s, 45sec, 90sec
    
    Args:
        filename (str): Audio filename
        
    Returns:
        str or None: Duration marker or None if not found
    """
    name_without_ext = Path(filename).stem
    # Look for pattern: digits + s or sec
    match = re.search(r'(\d+(?:s|sec))', name_without_ext, re.IGNORECASE)
    
    if match:
        duration = match.group(1).lower()
        # Normalize format (sec -> s)
        if duration.endswith('sec'):
            duration = duration.replace('sec', 's')
        return duration
    return None


def extract_duration_from_video_name(filename):
    """
    Extracts duration from video filename
    
    Args:
        filename (str): Video filename
        
    Returns:
        str or None: Duration marker or None if not found
    """
    name_without_ext = Path(filename).stem
    # Look for pattern: digits + s in video name
    match = re.search(r'(\d+s)', name_without_ext)
    
    if match:
        return match.group(1)
    return None


def find_audio_files():
    """
    Finds all .wav files in current folder and extracts their durations
    
    Returns:
        dict: {duration: [audio_files_list]} or {None: [audio_files_list]}
    """
    current_dir = Path.cwd()
    wav_files = list(current_dir.glob("*.wav"))
    
    audio_by_duration = {}
    
    for wav_file in wav_files:
        duration = extract_duration_from_audio_name(wav_file.name)
        
        if duration not in audio_by_duration:
            audio_by_duration[duration] = []
        audio_by_duration[duration].append(wav_file)
    
    return audio_by_duration


def find_video_files_in_subfolders():
    """
    Finds all video files in subfolders and groups by duration
    
    Returns:
        dict: {duration: [video_files_list]} or {None: [video_files_list]}
    """
    current_dir = Path.cwd()
    video_files = []
    
    # Look for .mp4 files in all subfolders
    for subfolder in current_dir.iterdir():
        if subfolder.is_dir():
            video_files.extend(list(subfolder.glob("*.mp4")))
    
    video_by_duration = {}
    
    for video_file in video_files:
        duration = extract_duration_from_video_name(video_file.name)
        
        if duration not in video_by_duration:
            video_by_duration[duration] = []
        video_by_duration[duration].append(video_file)
    
    return video_by_duration


def check_ffmpeg():
    """
    Checks for ffmpeg availability in system
    
    Returns:
        bool: True if ffmpeg is available, False otherwise
    """
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def create_backup_folder(video_path):
    """
    Creates backup folder structure one level above language folders
    
    Args:
        video_path (Path): Path to video file
        
    Returns:
        Path: Path to corresponding folder in backup
    """
    # Determine main folder (where language folders are located)
    main_dir = video_path.parent.parent  # If video in EN/, then main_dir = testfield/
    lang_folder_name = video_path.parent.name  # Language folder name (EN, RU, etc.)
    
    # Create structure backup/EN/, backup/RU/, etc.
    backup_main_dir = main_dir / "backup"
    backup_lang_dir = backup_main_dir / lang_folder_name
    
    backup_lang_dir.mkdir(parents=True, exist_ok=True)
    return backup_lang_dir


def merge_audio_video(video_path, audio_path):
    """
    Replaces audio in video file via FFmpeg (faster than moviepy)
    Saves original file to backup folder, then replaces with new one
    
    Args:
        video_path (Path): Path to video file (will be replaced)
        audio_path (Path): Path to audio file  
        
    Returns:
        bool: True if successful, False on error
    """
    temp_path = None
    
    try:
        # Create temporary file in same folder as video (on same disk)
        video_dir = video_path.parent
        with tempfile.NamedTemporaryFile(suffix='.mp4', dir=str(video_dir), delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        # FFmpeg command to replace audio in video
        cmd = [
            'ffmpeg',
            '-i', str(video_path),      # Input video
            '-i', str(audio_path),      # Input audio
            '-c:v', 'copy',             # Copy video without re-encoding
            '-c:a', 'aac',              # Encode audio to AAC
            '-map', '0:v:0',            # Take video from first file
            '-map', '1:a:0',            # Take audio from second file
            '-y',                       # Overwrite output file if exists
            str(temp_path)
        ]
        
        # Execute ffmpeg command
        result = subprocess.run(cmd, 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL,
                              check=True)
        
        # Create corresponding backup folder
        backup_dir = create_backup_folder(video_path)
        
        # Path for backup
        backup_path = backup_dir / video_path.name
        
        # If backup already exists - DON'T TOUCH it (preserve first original)
        if backup_path.exists():
            # Simply delete current file and place new one
            video_path.unlink()
            shutil.move(str(temp_path), str(video_path))
        else:
            # Backup doesn't exist - save original
            shutil.move(str(video_path), str(backup_path))  # Original to backup
            shutil.move(str(temp_path), str(video_path))     # New file to original location
        
        return True
        
    except subprocess.CalledProcessError as e:
        # Delete temporary file on error
        if temp_path and temp_path.exists():
            temp_path.unlink()
        print(f"FFmpeg error processing {video_path.name}")
        return False
    except Exception as e:
        # Delete temporary file on error
        if temp_path and temp_path.exists():
            temp_path.unlink()
        print(f"Error processing {video_path.name}: {e}")
        return False


def sound_merge_mode():
    """
    Sound merging mode with video
    """
    print("=== Sound Merge - Audio merging with video ===")
    
    # Check for ffmpeg availability
    if not check_ffmpeg():
        print("❌ ERROR: FFmpeg not found in system!")
        print("Install FFmpeg and add it to PATH:")
        print("https://ffmpeg.org/download.html")
        return
    
    print("✅ FFmpeg found")
    print("Searching for .wav files in current folder...")
    print("Searching for .mp4 files in subfolders...\n")
    
    # Find audio and video files
    audio_by_duration = find_audio_files()
    video_by_duration = find_video_files_in_subfolders()
    
    if not audio_by_duration:
        print("❌ No .wav files found in current folder!")
        return
    
    if not video_by_duration:
        print("❌ No .mp4 files found in subfolders!")
        return
    
    total_audio = sum(len(files) for files in audio_by_duration.values())
    total_video = sum(len(files) for files in video_by_duration.values())
    
    print(f"Found audio files: {total_audio}")
    print(f"Found video files: {total_video}")
    
    # Determine merging logic
    audio_durations = [d for d in audio_by_duration.keys() if d is not None]
    
    processed_count = 0
    
    if len(audio_durations) == 0:
        # All audio without duration marker - merge with all videos
        audio_files = audio_by_duration[None]
        all_videos = []
        for video_list in video_by_duration.values():
            all_videos.extend(video_list)
            
        for audio_file in audio_files:
            for video_file in all_videos:
                if merge_audio_video(video_file, audio_file):
                    processed_count += 1
                    
    elif len(audio_durations) == 1 and None not in audio_by_duration:
        # One audio with marker - merge with corresponding videos + without marker
        duration = audio_durations[0]
        audio_files = audio_by_duration[duration]
        
        target_videos = video_by_duration.get(duration, [])
        if None in video_by_duration:
            target_videos.extend(video_by_duration[None])
            
        for audio_file in audio_files:
            for video_file in target_videos:
                if merge_audio_video(video_file, audio_file):
                    processed_count += 1
                    
    else:
        # Multiple audio with markers - strict matching
        for duration in audio_durations:
            audio_files = audio_by_duration[duration]
            video_files = video_by_duration.get(duration, [])
            
            for audio_file in audio_files:
                for video_file in video_files:
                    if merge_audio_video(video_file, audio_file):
                        processed_count += 1
    
    print(f"\n=== MERGING RESULTS ===")
    print(f"✅ Replaced audio in {processed_count} video files")
    print("📦 Original files saved to backup/ folders")
    print("🎵 Files updated with new audio!")
    print("Done!")


def video_rename_mode():
    """
    Video file renaming mode
    """
    print("=== Video File Renamer ===")
    print("Format: customname_90s_en_1080x1920.mp4")
    print("Sorting by folders: EN, RU, SC, KR, etc.\n")
    
    # Get custom name from user
    custom_name = input("Enter custom name for files: ").strip()
    if not custom_name:
        print("Error: Must enter a name!")
        return
    
    # Find all .mp4 files in current folder
    current_dir = Path.cwd()
    mp4_files = list(current_dir.glob("*.mp4"))
    
    if not mp4_files:
        print("No .mp4 files found in current folder!")
        return
    
    # Filter files with WIP in name
    filtered_files = []
    wip_count = 0
    
    for video_file in mp4_files:
        if "WIP" in video_file.name.upper():
            wip_count += 1
        else:
            filtered_files.append(video_file)
    
    print(f"Found {len(mp4_files)} .mp4 files")
    if wip_count > 0:
        print(f"⏸️  Skipped WIP files: {wip_count}")
    print(f"To process: {len(filtered_files)} files")
    print("Processing files...")
    
    processed_count = 0
    error_count = 0
    languages_found = set()
    
    for video_file in filtered_files:
        # Extract language prefix
        lang_code = extract_language_prefix(video_file.name)
        languages_found.add(lang_code.upper())
        
        # Get video metadata
        resolution, duration = get_video_metadata(str(video_file))
        
        if resolution is None or duration is None:
            error_count += 1
            continue
        
        # Generate new name
        new_filename = generate_new_filename(custom_name, duration, lang_code, resolution)
        
        # Rename file
        new_path = video_file.parent / new_filename
        new_path = handle_duplicate_names(new_path)
        
        try:
            video_file.rename(new_path)
            
            # Move to language folder
            final_path = organize_by_language(new_path, lang_code)
            
            processed_count += 1
            
        except Exception as e:
            error_count += 1
    
    print("\n=== PROCESSING RESULTS ===")
    print(f"✅ Successfully processed: {processed_count} files")
    if error_count > 0:
        print(f"❌ Errors: {error_count}")
    if languages_found:
        print(f"📁 Created folders: {', '.join(sorted(languages_found))}")
    print("Done!")


def drag_drop_mode(files):
    """
    Drag & drop mode - quick audio merging with video
    
    Args:
        files (list): List of paths to dragged files
    """
    print("=== DRAG & DROP MODE - Quick Merging ===")
    
    # Check for ffmpeg availability
    if not check_ffmpeg():
        print("❌ ERROR: FFmpeg not found in system!")
        print("Install FFmpeg and add it to PATH:")
        print("https://ffmpeg.org/download.html")
        return
    
    # Separate files into audio and video
    audio_files = []
    video_files = []
    
    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            print(f"⚠️ File not found: {file_path}")
            continue
            
        if path.suffix.lower() == '.wav':
            audio_files.append(path)
        elif path.suffix.lower() == '.mp4':
            video_files.append(path)
        else:
            print(f"⚠️ Unsupported format: {path.name}")
    
    print(f"Found audio files: {len(audio_files)}")
    print(f"Found video files: {len(video_files)}")
    
    # Check drag & drop conditions
    if len(audio_files) != 1:
        print("❌ ERROR: Need exactly 1 audio file (.wav)")
        print("Drag exactly 1 .wav file and 1 or more .mp4 files")
        return
    
    if len(video_files) < 1:
        print("❌ ERROR: Need at least 1 video file (.mp4)")  
        print("Drag exactly 1 .wav file and 1 or more .mp4 files")
        return
    
    audio_file = audio_files[0]
    print(f"🎵 Audio: {audio_file.name}")
    print(f"🎬 Video files: {len(video_files)}")
    
    # Create sound folder in same location as audio file
    sound_dir = audio_file.parent / "sound"
    sound_dir.mkdir(exist_ok=True)
    print(f"📁 Created folder: {sound_dir}")
    
    processed_count = 0
    
    for video_file in video_files:
        print(f"Processing: {video_file.name}")
        
        # Path for result in sound folder
        output_path = sound_dir / video_file.name
        output_path = handle_duplicate_names(output_path)
        
        try:
            # FFmpeg command for merging
            cmd = [
                'ffmpeg',
                '-i', str(video_file),      # Input video
                '-i', str(audio_file),      # Input audio
                '-c:v', 'copy',             # Copy video without re-encoding
                '-c:a', 'aac',              # Encode audio to AAC
                '-map', '0:v:0',            # Take video from first file
                '-map', '1:a:0',            # Take audio from second file
                    '-y',                       # Overwrite output file if exists
                str(output_path)
            ]
            
            # Execute ffmpeg command
            result = subprocess.run(cmd, 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL,
                                  check=True)
            
            processed_count += 1
            print(f"✅ {video_file.name} → sound/{output_path.name}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error processing {video_file.name}")
    
    print(f"\n=== DRAG & DROP RESULTS ===")
    print(f"✅ Successfully processed: {processed_count} videos")
    print(f"📁 Results in folder: {sound_dir}")
    print("Done!")


def main():
    """
    Main function with mode selection
    """
    # Check if there are command line arguments (drag & drop via .bat file)
    if len(sys.argv) > 1:
        # Drag & drop mode
        files = sys.argv[1:]  # All arguments except script name
        try:
            drag_drop_mode(files)
        except Exception as e:
            print(f"❌ CRITICAL ERROR: {e}")
            print("Error details:")
            import traceback
            traceback.print_exc()
        return
    
    # Normal operation mode
    print("=== VIDEO UTILITIES ===")
    print("1. Video File Renamer")
    print("2. Sound Merge - Audio merging with video")
    print("💡 For drag & drop use video_renamer.bat")
    
    while True:
        choice = input("\nSelect function (1/2): ").strip()
        
        if choice == "1":
            video_rename_mode()
            break
        elif choice == "2":
            sound_merge_mode()
            break
        else:
            print("❌ Invalid choice. Enter 1 or 2.")


if __name__ == "__main__":
    main()