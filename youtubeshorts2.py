import argparse
import datetime
import json
import random
import requests
import sys
import os
import os.path
import time
import cv2
#import youtube_dl

#import pafy



from pathlib import Path

import google.oauth2.credentials
from googleapiclient.discovery import build

# > < =
PROGNA = f"{sys.argv[0]}"
TITLE = "YouTube #Shorts Video Creator"
VERSION = "1.0b"
AUTHOR = "Mr Tecoman"
EMAIL = "mrtecomancolima@gmail.com"
YOUTUBE_CHANNEL = "https://www.youtube.com/@MrTecoman"
GITHUB="https://github.com/mrtecoman/youtubeshorts"
COPYRIGHT = "(c) 2024 by Mr. Tecoman"

def parse_args():
    parser = argparse.ArgumentParser(description=f"""
                                                    {TITLE} Ver. {VERSION} Create a Youtube #shorts video (less than 60 seconds)
                                                    from videos found in channel using your “YouTube Data API”
                                                    The video will be done using files found in 'videos_directory'.

                                                    You can specify çhannel and api_key by creating 'secrets' file
                                                    with this content:
                                    
                                                    api_key = YOUR_API_KEY_HERE
                                                    channel = YOUR_CHANNEL_ID_HERE

                                                    or directly as arguments, see -h --help for more information.""", allow_abbrev=False)
    parser.add_argument("-a", "--api_key", required=False, help="YouTube Data API, default content in 'secrets' file")
    parser.add_argument("-ch", "--channel", required=False, help="YouTube channel id, default content in 'secrets' file")
    parser.add_argument("-yd", "--videos_directory", default="videos_directory", help="Working Directory (default: 'videos_directory')")
    parser.add_argument("-sl", "--short_length", type=int, default=60, help="Short video length in seconds (default: 60)")
    parser.add_argument("-hm", "--how_many", type=int, default=100, help="How many videos to request (default: 100)")
    parser.add_argument("-cs", "--crop_seconds", type=int, default=2, help="Crop duration in seconds (default: 2)")
    parser.add_argument("-o", "--offline", type=int, default=1, help="Triggers offline mode, uses json file (default: on)")
    parser.add_argument("-j", "--json_filename", default="youtubeshorts.json", help="Sets working JSON file (default: 'youtubeshorts.json')")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode (default: no verbose)")
    parser.add_argument("-c", "--credits", action="store_true", help="Display Credits")


    args = parser.parse_args()

    return args

def verbose(args, custom_msg):
    if args.verbose:
       print(custom_msg)

def parse_json_file(json_filename):
    
    if not os.path.exists(json_filename):
        print(f"Error: File '{json_filename}' does not exist.")
        sys.exit(1)

    try:
        with open(json_filename, "r") as json_file:
            data = json.load(json_file)
            return data
    except json.JSONDecodeError:
        print(f"Error decoding JSON content in '{json_filename}'.")
        sys.exit(1)


def get_random_video_id(args, api_key, channel):
    
    url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&maxResults={args.how_many}&part=snippet&type=video&q={channel}"
    
    verbose(args, f"Processing: {url}")

    response = requests.get(url)

    if response.status_code == 403:
        print("You’ve used up all your API quota for this period.")
        print("Try offline mode and work with an existing JSON file.")
        sys.exit(1)

    data = json.loads(response.text)
    
    print("Success! API request honored")
    verbose(args, "We found some videos!")

    return data
    
   
def generate_shorts_filename():
    now = datetime.datetime.now()
    formatted_date = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"YoutubeShorts-{formatted_date}.mkv"
    return filename

def calculate_videos(short_lenght, crop_seconds):

    if crop_seconds <= 0 or short_lenght<= 0:
        return 0

    return short_lenght // crop_seconds

def generate_cropped_youtube_url(video_id, crop_seconds):
    # Assuming video_id is a valid YouTube video ID (e.g., "dQw4w9WgXcQ")
    base_url = f"https://www.youtube.com/watch?v={video_id}"

    # Get video duration (you might need to fetch this from the YouTube API)
    video_duration_seconds = crop_seconds  # Example duration (5 minutes)

    # Initialize the random seed based on system time
    #random.seed(int(time.time()))
    
    # Generate a random start time within the video duration
    #random_start_time = random.randint(0, video_duration_seconds - crop_seconds)
    random_start_time = random.sample(range(1,500),1)[0]

    #random_start_time =  str(random.sample(range(1, 101)))

    #unique_numbers = random.sample(range(1, 101), 5)
    #print(unique_numbers)
    
    # Construct the final URL
    cropped_url = f"{base_url}" #&t={random_start_time}s&end={random_start_time + crop_seconds}s"

    return cropped_url

def download_and_combine_videos(video_urls, output_filename):
    # Create an empty list to store the downloaded video segments
    video_segments = []

    # Download each video segment
    for i, url in enumerate(video_urls):
        response = requests.get(url)
        if response.status_code == 200:
            video_segments.append(response.content)
            print(f"Downloaded segment {i + 1}")
        else:
            print(f"Error downloading segment {i + 1}")

    # Combine the video segments
    combined_video = b"".join(video_segments)

    # Save the combined video as an MP4 file
    with open(output_filename, "wb") as mp4_file:
        mp4_file.write(combined_video)

    print(f"Combined video saved as {output_filename}")


def create_working_directory(working_directory):
    try:
        os.makedirs(working_directory, exist_ok=False)
        print(f"Directory '{working_directory}' created.")
    except FileExistsError:
        print(f"Warning: Directory '{working_directory}' already exist.")

#def run_bash_command(command):
#    try:
#        os.system(command)
#    except Exception as e:
#        print(f"Error executing command: {e}"

def check_file_exists(file_path):
    return os.path.exists(file_path)
                  
def download_youtube_segment(video_id, video_url, working_directory):
 
    ##yt-dlp -o test.mkv https://www.youtube.com/watch?v=HoPgo8UDuqM
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

def main():

    args = parse_args()

    if args.verbose:
        print("Verbose mode enabled")

    # Initialize the random seed based on system time

    tmp = int(time.time())
    verbose(args, f"Random seed: {tmp}")
    random.seed(tmp)

    #youtube #shorts vedeo parameters
    #frame_rate = 30  # Frames per second
    #frame_size = (1080, 1920)  # Width x Height
    #fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # Codec for MP4

    if args.credits:
        credits()

    #check for channel_id and api_id are not in arguments
    if not args.channel or not args.api_key:
        #open secrets
        verbose(args, "channel_id or api_id not found in command line, trying opening 'secrets' file")

        # Create an empty dictionary
        secret = {}

        if check_file_exists("secrets"):
            verbose(args, "'secrets' file found, trying to read values")

            with open("secrets", "r") as file:
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

    short_lenght = args.short_length
    crop_seconds = args.crop_seconds
    how_many = args.how_many
    short_filename = generate_shorts_filename()
    working_directory = args.videos_directory
    number_videos = calculate_videos(short_lenght, crop_seconds)
    json_filename = args.json_filename
    offline = args.offline

    verbose(args, f"API Key: {masked_msg(api_key)}")
    verbose(args, f"Channel ID: {masked_msg(channel)}")
    verbose(args, f"How many videos to request: {how_many}")
    verbose(args, f"Short Video Length: {short_lenght}")
    verbose(args, f"Crop Seconds: {crop_seconds}")
    verbose(args, f"JSON filename: {json_filename}")
    verbose(args, f"Offline mode: {offline}")
    verbose(args, f"Generated Short Filename: {short_filename}")
    verbose(args, f"Working directory: {working_directory}")
    verbose(args, f"Calculated number of videos: {number_videos}")
    sys.exit()
    print(f"Creating {working_directory}")
    create_working_directory(working_directory)

    print(f"\nGetting videos from {channel}")

    #create a VideoWriter object
    #video_writer = cv2.VideoWriter(short_filename, fourcc, frame_rate, frame_size)

    video_id = "HoPgo8UDuqM"
    #video_urls = []
    for n in range(0,6):
        new_video_url = generate_cropped_youtube_url(video_id, crop_seconds)
        print(f"Downloading {new_video_url}")

        #if n < 9:
        #    part_segment = f"0{n}"
        #else:
        #    part_segment = f"{n}"

        download_youtube_segment(video_id, new_video_url, working_directory)
        #video_urls.append(new_video_url)

    #print(generate_cropped_youtube_url(video_id, crop_seconds))
    #download_and_combine_videos(video_urls, short_filename)
    
    sys.exit(1)

    if how_many <= number_videos:
        print(f"\nAccording to my calculations, you need at least {number_videos} videos, but you request only {how_many} videos.")
        print(f"Will try to use {number_videos} times those {how_many} videos you request to create ")
        print(f"your {short_filename} file, This may involve using some of the same videos multiple times to achieve the")
        print(f"{short_lenght}-second video lenght you requested.\n")

    if not offline:
        fetch_videos = get_random_video_id(args, api_key, channel)
    else:
        if os.path.exists(json_filename):
            while True:
                user_choice = input(f"The file '{json_filename}' already exists. Do you want to overwrite it? (yes): ").lower()
                   
                if user_choice == "yes":
                    break
                sys.exit(0)
  

        print(f"Creating {json_filename}")

        fetch_videos = get_random_video_id(args, api_key, channel)

        try:
            with open(json_filename, "w") as json_file:
                json.dump(fetch_videos, json_file, indent=4)  # Write data to the file
                print(f"Data successfully saved to '{json_filename}'.")
        
        except json.JSONDecodeError:
            print(f"Error saving JSON content to '{json_filename}'.")
            sys.exit(1)


    print(f"Working with: {json_filename}")



if __name__ == "__main__":
    main()
