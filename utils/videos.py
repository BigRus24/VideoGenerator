import json
import time
import re
import translators

from praw.models import Submission

from utils.settings import config


def name_normalize(name: str) -> str:
    name = re.sub(r'[?\\"%*:|<>]', "", name)
    name = re.sub(r"( [w,W]\s?\/\s?[o,O,0])", r" without", name)
    name = re.sub(r"( [w,W]\s?\/)", r" with", name)
    name = re.sub(r"(\d+)\s?\/\s?(\d+)", r"\1 of \2", name)
    name = re.sub(r"(\w+)\s?\/\s?(\w+)", r"\1 or \2", name)
    name = re.sub(r"\/", r"", name)

    lang = config["reddit"]["thread"]["post_lang"]
    if lang:
        print("Translating filename...")
        translated_name = translators.translate_text(name, translator="google", to_language=lang)
        return translated_name
    return name


def check_done(redditobj: Submission) -> Submission:
    """Checks if the chosen post has already been generated

    Args:
        redditobj (Submission): Reddit object gotten from reddit/subreddit.py

    Returns:
        Submission|None: Reddit object in args
    """
    with open("./video_creation/data/videos.json", "r", encoding="utf-8") as done_vids_raw:
        done_videos = json.load(done_vids_raw)
    for video in done_videos:
        if video["id"] == str(redditobj):
            if config["reddit"]["thread"]["post_id"]:
                print(
                    "You already have done this video but since it was declared specifically in the config file the program will continue"
                )
                return redditobj
            print("Getting new post as the current one has already been done")
            return None
    return redditobj

def save_data(filename: str, reddit_title: str, reddit_id: str, credit: str, debug: bool=False):
    """Saves the videos that have already been generated to a JSON file in video_creation/data/videos.json

    Args:
        subreddit (str): The name of the subreddit
        filename (str): The finished video title name
        reddit_title (str): The title of the Reddit post
        reddit_id (str): The ID of the Reddit post
        credit (str): Credit for the background
        debug (bool): Flag to determine if running in debug mode
    """
    video_path = f"./results/{filename}"
    
    with open("./video_creation/data/videos.json", "r+", encoding="utf-8") as raw_vids:
        done_vids = json.load(raw_vids)
        
        if reddit_id in [video["id"] for video in done_vids]:
            return  # video already done but was specified to continue anyway in the config file
        
        if debug:
            print(f"Debug mode: Not adding video {video_path} to videos.json.")
            return

        payload = {
            "id": reddit_id,
            "time": str(int(time.time())),
            "background_credit": credit,
            "reddit_title": reddit_title,
            "filename": filename,
        }
        done_vids.append(payload)
        raw_vids.seek(0)
        raw_vids.truncate()
        json.dump(done_vids, raw_vids, ensure_ascii=False, indent=4)
        print(f"Saved video {video_path} to videos.json.")
