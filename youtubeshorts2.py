import argparse
import datetime
import json
import random
import requests
import sys
import os
import os.path
import time
from pytube import YouTube
#from moviepy.editor import VideoFileClip
from moviepy.editor import VideoFileClip, concatenate_videoclips

import cv2

#import youtube_dl #didn't work
#import pafy #not found
from pathlib import Path
import google.oauth2.credentials
from googleapiclient.discovery import build
import googleapiclient.discovery


# > < =
PROGNA = f"{sys.argv[0]}"
TITLE = "YouTube #Shorts Video Creator"
VERSION = "1.0b"
AUTHOR = "Mr Tecoman"
EMAIL = "mrtecomancolima@gmail.com"
YOUTUBE_CHANNEL = "https://www.youtube.com/@MrTecoman"
GITHUB="https://github.com/mrtecoman/youtubeshorts"
COPYRIGHT = "(c) 2024 by Mr. Tecoman"

#defaults
VIDEOS_DIRECTORY = "videos_directory"
SHORTS_DIRECTORY = "shorts_directory"
SECRETS = "secrets"
SHORT_LENGTH = 60
HOW_MANY = 32
CROP_SECONDS = 5
OFFLINE  = 1
DOWNLOAD = 0
JSON_FILENAME = "youtubeshorts.json"


def parse_args():
    parser = argparse.ArgumentParser(description=f"""
                                                    {TITLE} Ver. {VERSION} Create a Youtube #shorts video (less than {SHORT_LENGTH} seconds)
                                                    from videos found in channel using your “YouTube Data API”
                                                    The video will be done using files found in '{VIDEOS_DIRECTORY}'.

                                                    You can specify çhannel and api_key by creating ´{SECRETS}' file
                                                    with this content:
                                    
                                                    api_key = YOUR_API_KEY_HERE
                                                    channel = YOUR_CHANNEL_ID_HERE

                                                    or directly as arguments, see
                                                     {PROGNA} --help 
                                                     
                                                     for more information.""", allow_abbrev=False)
    parser.add_argument("-a", "--api_key", required=False, help=f"YouTube Data API, default content in '{SECRETS}' file")
    parser.add_argument("-ch", "--channel", required=False, help=f"YouTube channel id, default content in '{SECRETS}' file")
    parser.add_argument("-yd", "--videos_directory", default=f"{VIDEOS_DIRECTORY}", help=f"Working Videos Directory (default: '{VIDEOS_DIRECTORY}')")
    parser.add_argument("-sd", "--shorts_directory", default=f"{SHORTS_DIRECTORY}", help=f"Working Shorts Directory (default: '{SHORTS_DIRECTORY}')")
    parser.add_argument("-sl", "--short_length", type=int, default={SHORT_LENGTH}, help=f"Short video length in seconds (default: {SHORT_LENGTH})")
    parser.add_argument("-hm", "--how_many", type=int, default={HOW_MANY}, help=f"How many videos to request (default: {HOW_MANY})")
    parser.add_argument("-cs", "--crop_seconds", type=int, default={CROP_SECONDS}, help=f"Crop duration in seconds (default: {CROP_SECONDS})")
    parser.add_argument("-o", "--offline", type=int, default={OFFLINE}, help=f"Triggers offline mode, doesn't request a new json file (0: online, 1: offline), (default: {OFFLINE})")
    parser.add_argument("-d", "--download", action="store_true", help="Download new videos (0: no, 1: yes), (default: {DOWNLOAD})")
    parser.add_argument("-j", "--json_filename", default=f"{JSON_FILENAME}", help=f"Sets working JSON file (default: '{JSON_FILENAME}')")
    parser.add_argument("-s", "--secret", default=f"{SECRETS}", help=f"Path to {SECRETS} file (default: '{SECRETS}')")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode (default: no verbose)")
    parser.add_argument("-c", "--credits", action="store_true", help="Display Credits")


    args = parser.parse_args()

    return args

def verbose(args, custom_msg):
    if args.verbose:
       print(custom_msg)

def check_file_exists(file_path):
    return os.path.exists(file_path)

def get_authenticated_service(args, api_key):
    verbose(args, "Authenticating YouTube service...")
    return build('youtube', 'v3', developerKey=api_key)


def merge_json_files(file1, file2, output_file):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    combined_data = data1 + data2

    with open(output_file, 'w') as outfile:
        json.dump(combined_data, outfile, indent=2)

def get_video_ids(args, api_key, channel, how_many, json_filename):
    verbose(args,f"Getting {how_many} video ids ...")
    base_url = 'https://youtube.googleapis.com/youtube/v3/search'
    max_results = how_many  # You can adjust this as needed
    video_ids = []

    # Initial request
    params = {
        'part': 'snippet',
        'channelId': channel,
        'maxResults': max_results,
        'order': 'date',
        'type': 'video',
        'key': api_key
    }
    response = requests.get(url=base_url, params=params).json()

    # Extract video information
    tmp = 1
    for item in response.get('items', []):
        #print(tmp)
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        published_date = item['snippet']['publishedAt']
        video_ids.append({
            'video_id': video_id,
            'video_title': video_title,
            'published_date': published_date
        })
        verbose(args, f"in for-loop ({tmp}): {video_id} {video_title} {published_date}")
        tmp += 1

    # Handle pagination
    while 'nextPageToken' in response:

        response = requests.get(url=base_url, params=params).json()

        for item in response.get('items', []):
            print(tmp)

            video_id = item['id']['videoId']
            video_title = item['snippet']['title']
            published_date = item['snippet']['publishedAt']
            video_ids.append({
                'video_id': video_id,
                'video_title': video_title,
                'published_date': published_date
            })

            verbose(args, f"in while-for-loop ({tmp}): {video_id} {video_title} {published_date}")

            tmp += 1

        params['pageToken'] = response.get('nextPageToken')

    return video_ids

def save_to_json(args, video_ids, output_file):
    verbose(args, f"Saving {output_file}")
    try:
        with open(output_file, 'w') as json_file:
            json.dump(video_ids, json_file, indent=2)
    except Exception as e:
        # Handle any exceptions (e.g., file not found, permission issues)
        print(f"Error saving to {output_file}: {str(e)}")
    else:
        print(f"Saved to {output_file}")
    finally:
        json_file.close()  # Explicitly close the file



def download_video_and_create_nfo(args, video_info_list, output_directory):
    verbose(args, "Downloading video and creating nfo file")

    tmp = 1
    for video_info in video_info_list:
        video_id = video_info['video_id']
        video_title = video_info['video_title']
        published_date = video_info['published_date']

        video_filename = f"{video_id}"
        mkv_filename = f"{video_id}.mkv"
        mkv_filepath = os.path.join(output_directory, mkv_filename)
        if not check_file_exists(mkv_filepath):

            # doesn't work, so back to dirty way, call terminal!
            #stream.download(output_path=output_directory, filename=video_filename)
            url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"downloading ({tmp}): {url}")
            os.system(f"yt-dlp -o {mkv_filepath} {url}")
            tmp += 1

        else:
            print(f"{mkv_filepath} exist, skipping")

        # Create the NFO content
        nfo_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <video>
            <title>{video_title}</title>
            <published_date>{published_date}</published_date>
            <!-- Other tags if needed -->
        </video>
        """
        # Write the NFO content to a file
        nfo_filename = f"{video_id}.nfo"
        nfo_filepath = os.path.join(output_directory, nfo_filename)
        if not check_file_exists(nfo_filepath):

            with open(nfo_filepath, 'w', encoding='utf-8') as nfo_file:
                nfo_file.write(nfo_content)

            print(f"Created {nfo_filename}")
        else:
            print(f"{nfo_filepath} already exist, skipping")

def save_file(args, filename, content):
    verbose(args, f"Saving: {filename}")

    try:
        with open(filename, "w") as file:
            file.write(content)
        print(f"Content saved to {filename} successfully!")
    except Exception as e:
        print(f"Error saving content to {filename}: {e}")
   
def generate_shorts_filename():
    now = datetime.datetime.now()
    formatted_date = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"YoutubeShorts-{formatted_date}.mkv"
    return filename

def calculate_videos(args, short_lenght, crop_seconds):
    verbose(args, "Calculating videos")

    if (crop_seconds <= 0) or (short_lenght <= 0):
        return 0

    return short_lenght // crop_seconds

def create_working_directory(working_directory):
    try:
        os.makedirs(working_directory, exist_ok=False)
        print(f"Directory '{working_directory}' created.")
    except FileExistsError:
        print(f"Warning: Directory '{working_directory}' already exist.")

                  
def download_youtube_segment(video_id, video_url, working_directory):
 
    if check_file_exists(f"{working_directory}/{video_id}.mkv"):
        print(f"Downloading {video_url}")
        os.system(f"old_dir=$(pwd) && cd $old_dir/{working_directory} && yt-dlp -o {video_id}.mkv {video_url} && cd $old_dir")
    else:
        print(f"File {video_id}.mkv already exist, skipping")

def credits():
    print(f"""
          {TITLE} Ver. {VERSION}
          {PROGNA} by {AUTHOR}

          {EMAIL}
          {YOUTUBE_CHANNEL}
          {GITHUB}
          {COPYRIGHT}

          """)
    sys.exit()
    
def masked_msg(msg):
    return len(msg) * "*"

def ON_OFF(args, mode):
 
    if not mode:
        msg = "ONLINE"
    else:
        msg = "OFFLINE"

    return msg

def confirm_overwrite(args, overwrite_filename):
     if check_file_exists(overwrite_filename):
        while True:
            user_choice = input(f"The file '{overwrite_filename}' already exists. Do you want to overwrite it? (yes) or enter to abort: ").lower()
                   
            if user_choice == "yes":
                return
            
            sys.exit(0)

def pick_random_files_by_extension(args, directory_path, extension, num_files):
   
    verbose(args, f"Selecting {num_files} random files from {directory_path}/{extension}")
    try:
        all_files = os.listdir(directory_path)
        file_list = [file for file in all_files if os.path.isfile(os.path.join(directory_path, file))]
        filtered_files = [file for file in file_list if file.lower().endswith(extension.lower())]
        random_files = random.sample(filtered_files, min(num_files, len(filtered_files)))
        return random_files
    except FileNotFoundError:
        print(f"Directory '{directory_path}' not found.")
        return []

def main():

    args = parse_args()

    if args.verbose:
        print("Verbose mode enabled")

    # Initialize the random seed based on system time
    tmp = int(time.time())
    verbose(args, f"Random seed: {tmp}")
    random.seed(tmp)

    if args.credits:
        credits()

    secret_file = args.secret


    #check for channel_id and api_id are not in arguments
    if not args.channel or not args.api_key:
        #open secrets
        verbose(args, f"channel_id or api_id not specify, trying '{secret_file}' file")

        # Create an empty dictionary
        secret = {}

        if check_file_exists(f"{secret_file}"):
            verbose(args, f"'{secret_file}' file found, trying to read values")

            with open(f"{secret_file}", "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    secret[key.strip()] = value.strip()
            
        else:
            print("Fatal Error: No way to know api_key or channel_id. See -h for help.")
            sys.exit(1)

        # Now you can access the values using the keys
        api_key = secret.get("api_key")
        channel = secret.get("channel")

    else:
        #take them as argument
        api_key = args.api_key
        channel = args.channel

    if not api_key or not channel:
        verbose(args, "Can't found api_key or channel_id")
        if not api_key: print(f"*API Key required")
        if not channel: print(f"*Channel ID required")
        print("For more information, see")
        print(f"{PROGNA} -h")
        sys.exit(1)

    #convert type 'set' to 'int'
    short_lenght = args.short_length
    crop_seconds = args.crop_seconds
    how_many = args.how_many
    download = args.download

    #rest of variables
    short_filename = generate_shorts_filename()
    working_directory = args.videos_directory
    shorts_directory = args.shorts_directory
    secret_file = args.secret
    number_videos = calculate_videos(args, short_lenght, crop_seconds) #number of videos will be need it
    json_filename = args.json_filename
    offline = args.offline

    verbose(args, f"\nAPI Key: {masked_msg(api_key)}")
    verbose(args, f"Channel ID: {masked_msg(channel)}")
    verbose(args, f"How many videos to request: {how_many}")
    verbose(args, f"Short Video Length: {short_lenght}")
    verbose(args, f"Crop Seconds: {crop_seconds}")
    verbose(args, f"JSON filename: {json_filename}")
    verbose(args, f"secret filename: {secret_file}")
    verbose(args, f"Offline mode: {ON_OFF(args, offline)}")
    verbose(args, f"secret filename: {secret_file}")
    verbose(args, f"Download mode: {download}")
    verbose(args, f"Shorts filename: {short_filename}")
    verbose(args, f"Shorts directory: {shorts_directory}")
    verbose(args, f"Working directory: {working_directory}")
    verbose(args, f"Calculated number of videos: {number_videos}")
    
    print(f"Creating {working_directory}\n")
    create_working_directory(working_directory)
    print(f"Creating {shorts_directory}\n")
    create_working_directory(shorts_directory)

    how_many_videos = sum(1 for entry in os.scandir(f"{working_directory}") if entry.is_file())

    if how_many_videos <= number_videos:
        print(f"\nAccording to my calculations, you need at least {number_videos} videos, but you request only {how_many_videos} videos.")
        print(f"in '{working_directory}', Will try to use {number_videos} times those {how_many_videos} videos you request to create")
        print(f"your {short_filename} file, This may involve using some of the same videos multiple times to achieve the")
        print(f"{short_lenght}-second video lenght you requested.\n")

    if not offline:
        #fetch_videos = get_video_ids(args, api_key, channel)
        verbose(args, f"Getting {how_many} from channel {masked_msg(channel)}")
        confirm_overwrite(args, json_filename)
        
        fetch_videos = get_video_ids(args, api_key, channel, how_many, json_filename)
        save_to_json(args, fetch_videos, json_filename)
    
    if not check_file_exists(json_filename):
        print(f"{json_filename} not found!\nTry {PROGNA} --offline 0 , see -h --help")
        sys.exit(1)
    
    with open(json_filename, 'r') as json_file:
        video_info_list = json.load(json_file)
    if download:
        download_video_and_create_nfo(args, video_info_list, working_directory)

    print(f"Creating {short_filename}")
    desired_extension = ".mkv"

    number_videos = number_videos
    random_files = pick_random_files_by_extension(args, working_directory, desired_extension, number_videos)
    
    if random_files:
        verbose(args, f"Randomly selected {desired_extension} files:")
        
        # Create a list to save clips
        all_clips = []

        for filename in random_files:
            verbose(args, f"adding {filename}")

            video = VideoFileClip(f"{working_directory}/{filename}")
            duration = video.duration
            
            random_start_times = [random.uniform(0, duration - crop_seconds) for _ in range(1)]
            clips = [video.subclip(start_time, start_time + crop_seconds) for start_time in random_start_times]

            all_clips.extend(clips)

        # Combine all clips in one file MKV
        final_clip = concatenate_videoclips(all_clips, method="compose")
        final_clip.write_videofile(f"{shorts_directory}/{short_filename}", codec="libx264")
        
        print(f"{shorts_directory}/{short_filename} created.")

    else:
        print(f"No {desired_extension} files found in the specified directory.")
        sys.exit(1)


    print("Done, enjoy!")

if __name__ == "__main__":
    main()