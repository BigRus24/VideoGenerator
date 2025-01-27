import re
import json
import praw
from prawcore.exceptions import ResponseException
from praw.models import MoreComments
from os.path import exists

from utils.settings import config
from utils.videos import check_done
from utils.voice import sanitize_text
from utils.posttextparser import posttextparser
from utils.ai_methods import sort_by_similarity

def get_subreddit_threads(POST_ID: str):
    """
    Returns a list of threads from the specified subreddit.
    """

    print("Logging into Reddit.")

    content = {}
    if config["reddit"]["creds"]["2fa"]:
        print("\nEnter your two-factor authentication code from your authenticator app.\n")
        code = input("> ")
        print()
        pw = config["reddit"]["creds"]["password"]
        passkey = f"{pw}:{code}"
    else:
        passkey = config["reddit"]["creds"]["password"]
    username = config["reddit"]["creds"]["username"]
    if str(username).casefold().startswith("u/"):
        username = username[2:]
    try:
        reddit = praw.Reddit(
            client_id=config["reddit"]["creds"]["client_id"],
            client_secret=config["reddit"]["creds"]["client_secret"],
            user_agent="Accessing Reddit threads",
            username=username,
            password=passkey,
            check_for_async=False,
        )
    except ResponseException as e:
        if e.response.status_code == 401:
            print("Invalid credentials - please check them in config.toml")
    except:
        print("Something went wrong...")

    print("Getting subreddit threads...")
    similarity_score = 0
    if not config["reddit"]["thread"]["subreddit"]:
        try:
            subreddit = reddit.subreddit(
                re.sub(r"r\/", "", input("What subreddit would you like to pull from? "))
            )
        except ValueError:
            subreddit = reddit.subreddit("askreddit")
            print("Subreddit not defined. Using AskReddit.")
    else:
        sub = config["reddit"]["thread"]["subreddit"]
        print(f"Using subreddit: r/{sub} from TOML config")
        subreddit_choice = sub
        if str(subreddit_choice).casefold().startswith("r/"):
            subreddit_choice = subreddit_choice[2:]
        subreddit = reddit.subreddit(subreddit_choice)

    if POST_ID:
        submission = reddit.submission(id=POST_ID)
    elif config["reddit"]["thread"]["post_id"] and len(str(config["reddit"]["thread"]["post_id"]).split("+")) == 1:
        submission = reddit.submission(id=config["reddit"]["thread"]["post_id"])
    elif config["ai"]["ai_similarity_enabled"]:
        threads = subreddit.hot(limit=50)
        keywords = config["ai"]["ai_similarity_keywords"].split(",")
        keywords = [keyword.strip() for keyword in keywords]
        print(f"Sorting threads by similarity to the given keywords: {', '.join(keywords)}")
        threads, similarity_scores = sort_by_similarity(threads, keywords)
        submission, similarity_score = get_subreddit_undone(threads, subreddit, similarity_scores=similarity_scores)
    else:
        threads = subreddit.hot(limit=25)
        submission = get_subreddit_undone(threads, subreddit)

    if submission is None:
        return get_subreddit_threads(POST_ID)
    elif not submission.num_comments and not config["settings"]["storymode"]:
        print("No comments found. Skipping.")
        exit()

    submission = check_done(submission)

    upvotes = submission.score
    ratio = submission.upvote_ratio * 100
    num_comments = submission.num_comments
    threadurl = f"https://reddit.com{submission.permalink}"

    print(f"Video will be: {submission.title} :thumbsup:")
    print(f"Thread url is: {threadurl} :thumbsup:")
    print(f"Thread has {upvotes} upvotes")
    print(f"Thread has an upvote ratio of {ratio}%")
    print(f"Thread has {num_comments} comments")
    if similarity_score:
        print(f"Thread has a similarity score up to {round(similarity_score * 100)}%")

    content["url"] = threadurl
    content["title"] = submission.title
    content["id"] = submission.id
    content["is_nsfw"] = submission.over_18
    content["comments"] = []
    if config["settings"]["storymode"]:
        if config["settings"]["storymodemethod"] == 1:
            content["content"] = posttextparser(submission.selftext)
        else:
            content["content"] = submission.selftext

    print("Received subreddit threads Successfully.")
    return content


def get_subreddit_undone(submissions: list, subreddit, times_checked=0, similarity_scores=None):
    """Get a submission that hasn't been processed yet."""

    if times_checked and config["ai"]["ai_similarity_enabled"]:
        print("Sorting based on similarity for a different date filter and thread limit..")
        submissions = sort_by_similarity(
            submissions, keywords=config["ai"]["ai_similarity_enabled"]
        )

    if not exists("./video_creation/data/videos.json"):
        with open("./video_creation/data/videos.json", "w+") as f:
            json.dump([], f)
    with open("./video_creation/data/videos.json", "r", encoding="utf-8") as done_vids_raw:
        done_videos = json.load(done_vids_raw)
    for i, submission in enumerate(submissions):
        if already_done(done_videos, submission):
            continue
        if submission.over_18:
            try:
                if not config["settings"]["allow_nsfw"]:
                    print("NSFW Post Detected. Skipping...")
                    continue
            except AttributeError:
                print("NSFW settings not defined. Skipping NSFW post...")
        if submission.stickied:
            print("This post was pinned by moderators. Skipping...")
            continue
        if submission.num_comments <= int(config["reddit"]["thread"]["min_comments"]) and not config["settings"]["storymode"]:
            print(f'This post has under the specified minimum of comments ({config["reddit"]["thread"]["min_comments"]}). Skipping...')
            continue
        if config["settings"]["storymode"]:
            if not submission.selftext:
                print("You are trying to use story mode on post with no post text")
                continue
            else:
                # Check for the length of the post text
                if len(submission.selftext) > config["reddit"]["thread"]["storymode_max_length"]:
                    print(f"Post is too long ({len(submission.selftext)}), try with a different post. ({config["reddit"]["thread"]['storymode_max_length']} character limit)")
                    continue
                elif len(submission.selftext) < config["reddit"]["thread"]["storymode_min_length"]:
                    print(f"Post is too short ({len(submission.selftext)}), try with a different post. ({config["reddit"]["thread"]['storymode_min_length']} character limit)")
                    continue
        if config["settings"]["storymode"] and not submission.is_self:
            continue
        if similarity_scores is not None:
            return submission, similarity_scores[i].item()
        return submission
    print("All submissions have been done going by top submission order.")
    VALID_TIME_FILTERS = ["day", "hour", "month", "week", "year", "all"]
    index = times_checked + 1
    if index == len(VALID_TIME_FILTERS):
        print("All submissions have been done.")

    return get_subreddit_undone(
        subreddit.top(time_filter=VALID_TIME_FILTERS[index], limit=(50 if int(index) == 0 else index + 1 * 50)),
        subreddit,
        times_checked=index,
    )


def already_done(done_videos: list, submission) -> bool:
    """Checks to see if the given submission is in the list of videos."""

    for video in done_videos:
        if video["id"] == str(submission):
            return True
    return False
