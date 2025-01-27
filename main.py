#!/usr/bin/env python
import argparse
import math
import datetime
import os
import sys
from os.path import exists
from os import name
import ffmpeg
from pathlib import Path
from subprocess import Popen
from typing import NoReturn
from uuid import uuid4
from PIL import Image
from prawcore import ResponseException
from reddit.generate_story import generate_story
from reddit.subreddit import get_subreddit_threads
from utils.settings import config
from utils.cleanup import cleanup
from utils.videos import name_normalize, save_data
from video_creation.background import get_and_download_background, chop_and_prepare_background
from video_creation.voices import save_text_to_mp3
from uploader.youtube import upload_youtube
from rich.progress import track
from video_creation.thumbnail import create_fancy_thumbnail, crop_and_resize_image
from video_creation.subtitles import generate_srt_file
from video_creation.audio import merge_audio_tracks
import multiprocessing


def get_tomorrow_at_11am():
    """
    Returns a string representing tomorrow at 11:00 AM in ISO 8601 format.
    """
    now = datetime.datetime.now(datetime.UTC)
    tomorrow = now + datetime.timedelta(days=1)
    tomorrow_at_11am = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 15, 0, 0)
    return tomorrow_at_11am.isoformat() + "Z"


def main(POST_ID=None, debug=False, shorts=True, subtitles=True,):
    generatetext = False
    global redditid, reddit_object
    
    if shorts:
        config["reddit"]["thread"]["storymode_min_length"] = 600
        config["reddit"]["thread"]["storymode_max_length"] = 900
        config["settings"]["resolution_w"] = 1080
        config["settings"]["resolution_h"] = 1920
    else:
        config["reddit"]["thread"]["storymode_min_length"] = 5000
        config["reddit"]["thread"]["storymode_max_length"] = 7500
        config["settings"]["resolution_w"] = 1920
        config["settings"]["resolution_h"] = 1080
    
    
    if debug:
        config["settings"]["tts"]["voice_choice"] = "streamlabspolly"
    else:
        config["settings"]["tts"]["voice_choice"] = "gpt"
    
    
    width = int(config["settings"]["resolution_w"])
    height = int(config["settings"]["resolution_h"])
    
    
    if generatetext:
        subject = "create a reddit story that is interesting"
        reddit_object = generate_story(subject=subject, paragraph_number=5, ai_model="g4f", voice="English")
    else:
        reddit_object = get_subreddit_threads(POST_ID)
    redditid = reddit_object["id"]
    
    
    length, num_audio_clips = save_text_to_mp3(reddit_object)
    length = math.ceil(length)
    
    bg_config = {
        "video": get_and_download_background("video"),
        "audio": get_and_download_background("audio"),
    }
    unprepared_background_video_path, background_audio_path, background_video_path = chop_and_prepare_background(bg_config, length, reddit_object, width, height)
    
    sanitized_title = name_normalize(reddit_object["title"])
    
    #audio
    audio_file_path = f"assets/temp/{redditid}/audio.mp3"
    title_audio_path = f"assets/temp/{redditid}/mp3/title.mp3"
    audio_clips = [
        ffmpeg.input(f"assets/temp/{redditid}/mp3/postaudio-{i}.mp3")
        for i in track(range(num_audio_clips), "Collecting the audio files...")
    ]

    audio_concat = ffmpeg.concat(*audio_clips, a=1, v=0)
    ffmpeg.output(
        audio_concat, audio_file_path, **{"b:a": "192k"}
    ).overwrite_output().run(quiet=True)

    print(f"Video Will Be: {length} Seconds Long")
    story_audio = ffmpeg.input(audio_file_path)
    title_audio = ffmpeg.input(title_audio_path)
    combined_audio = ffmpeg.concat(title_audio, story_audio, v=0, a=1).node['a']
    final_audio = merge_audio_tracks(combined_audio, background_audio_path)
    title_duration = float(ffmpeg.probe(title_audio_path)["format"]["duration"])
    
    if not exists(f"./results"):
        print("The 'results' folder could not be found so it was automatically created.")
        os.makedirs(f"./results")

    if not exists(f"./results/{reddit_object['id']}"):
        os.makedirs(f"./results/{reddit_object['id']}")
    
    # thumbnail 
    image = Image.open("assets/thumbnail.png")
    thumbnail_path = f"results/{redditid}/thumbnail.png"
    video_thumbnail_path = f"results/{redditid}/temp_thumbnail.png"
    
    create_fancy_thumbnail(image, sanitized_title, video_thumbnail_path, "#000000", 5)
    crop_and_resize_image(video_thumbnail_path, thumbnail_path)
    background_video = ffmpeg.input(background_video_path)
    thumbnail_video_segment = background_video.trim(start=0, end=title_duration).setpts('PTS-STARTPTS').filter('scale', width, height)
    thumbnail_with_image = ffmpeg.overlay(thumbnail_video_segment, ffmpeg.input(video_thumbnail_path), x="(main_w-overlay_w)/2", y="(main_h-overlay_h)/2").setpts('PTS-STARTPTS')

    # Generate SRT file for the story
    subtitle_background = background_video.trim(start=title_duration).setpts('PTS-STARTPTS').filter('scale', width, height)

    # Combine the thumbnail_with_image segment with the subtitle_background segment
    full_video = ffmpeg.concat(thumbnail_with_image, subtitle_background, v=1, a=0).node['v']

    # Generate SRT file for the story
    subtitles_path = f"assets/temp/{redditid}/story_subtitles.srt"
    generate_srt_file(audio_file_path,subtitles_path, start_offset=title_duration)

    # Add subtitles from the SRT file and center them vertically and horizontally on the screen
    full_video_with_subtitles = ffmpeg.filter(full_video, 'subtitles', subtitles_path, force_style='Alignment=10')
    
    #final video
    results_dir = f"results/{redditid}"
    video_output_path = os.path.join(results_dir, sanitized_title + ".mp4")
    
    print("Rendering the video 🎥")
    
    try:
        final_output = ffmpeg.output(
            full_video_with_subtitles, final_audio, video_output_path,
            vcodec="libx264",
            acodec="aac",
            **{"b:v": "20M", "b:a": "192k"},
            threads=multiprocessing.cpu_count()
        )
        final_output = final_output.overwrite_output()
        final_output.run(quiet=True, overwrite_output=True, capture_stdout=False, capture_stderr=False)
    except ffmpeg.Error as e:
        print(f"ffmpeg error: {e.stderr.decode('utf8')}")
        exit(1)
    
    if not debug:
        title = reddit_object["title"][:100]
        credentials_path = "credentials.json"
        if shorts:
            upload_youtube(video_output_path, title=title, description=title, category="24", keywords="redditstories,reddit,redditstorytimes,redditreadings,askreddit", privacy_status='private', publish_at=get_tomorrow_at_11am(), credentials_file=credentials_path)
        else:
            upload_youtube(video_output_path, title=title, description=title, category="24", keywords="redditstories,reddit,redditstorytimes,redditreadings,askreddit", privacy_status='private', publish_at=get_tomorrow_at_11am(), credentials_file=credentials_path, thumbnail_path=thumbnail_path)


    save_data(sanitized_title + ".mp4", reddit_object["title"], redditid, bg_config["video"][1][2], debug=debug)
    print("Done! 🎉 The video is in the results folder 📁")
    cleanups = cleanup(redditid)
    print(f"Removed {cleanups} temporary files 🗑")


def shutdown() -> NoReturn:
    if "redditid" in globals():
        print("## Clearing temp files")
        cleanup(redditid)
    print("Exiting...")
    sys.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Reddit video maker script.")
    parser.add_argument("--post_id", type=str, help="The ID of the Reddit post to process.")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode.")
    parser.add_argument("--shorts", action="store_true", help="Run in shorts mode.")
    parser.add_argument("--subtitles", action="store_true", help="Run in subtitles mode.")
    args = parser.parse_args()

    try:
        if args.post_id:
            main(POST_ID=args.post_id, debug=args.debug, shorts=args.shorts)
        else:
            main(debug=args.debug, shorts=args.shorts)
    except KeyboardInterrupt:
        shutdown()
    except ResponseException:
        print("## Invalid credentials")
        print("Please check your credentials in the config.toml file")
        shutdown()
    except Exception as err:
        config["settings"]["tts"]["tiktok_sessionid"] = "REDACTED"
        config["settings"]["tts"]["elevenlabs_api_key"] = "REDACTED"
        raise err
