import os
import sys
import time
import random
import httplib2
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1
# Maximum number of times to retry before giving up.
MAX_RETRIES = 10
# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib2.ServerNotFoundError)

# Always retry when an googleapiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = f"client_secret.json"
# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/youtube',
          'https://www.googleapis.com/auth/youtubepartner']
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = f"""
WARNING: Please configure OAuth 2.0
To make this sample run you will need to populate the client_secrets.json file
found at:
  
{os.path.abspath(os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE))}
with information from the API Console
https://console.cloud.google.com/
For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
"""
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def get_authenticated_service(credentials_file):
    
    if not os.path.exists(credentials_file):
        print(f"Missing credentials file: {credentials_file}")
        sys.exit(1)

    credentials = get_or_refresh_credentials(credentials_file)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)

def get_or_refresh_credentials(credentials_file):
    
    if os.path.exists(credentials_file):
        credentials = Credentials.from_authorized_user_file(credentials_file, SCOPES)
        if credentials.expired:
            credentials.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        credentials = flow.run_local_server()

    return credentials

def initialize_upload(youtube, options):
    tags = None
    if options['keywords']:
        tags = options['keywords'].split(",")

    body = {
        'snippet': {
            'title': options['title'],
            'description': options['description'],
            'tags': tags,
            'categoryId': options['category']
        },
        'status': {
            'privacyStatus': options['privacyStatus'],
            'madeForKids': False,  # Video is not made for kids
            'selfDeclaredMadeForKids': False  # You declare that the video is not made for kids
        }
    }

    if options['privacyStatus'] == 'private' and options.get('publishAt'):
        body['status']['publishAt'] = options['publishAt']

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(options['file'], chunksize=-1, resumable=True)
    )

    return resumable_upload(insert_request)

def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print(" => Uploading file...")
            status, response = insert_request.next_chunk()
            if 'id' in response:
                print(f"Video id '{response['id']}' was successfully uploaded.")
                return response
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = f"A retriable error occurred: {e}"

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                raise Exception("No longer attempting to retry.")

            max_sleep = 2 ** retry 
            sleep_seconds = random.random() * max_sleep
            print(f" => Sleeping {sleep_seconds} seconds and then retrying...")
            time.sleep(sleep_seconds)  

def upload_youtube(video_path, title, description, category, keywords, privacy_status, credentials_file, thumbnail_path=None, publish_at=None):
    try:
        # Get the authenticated YouTube service
        youtube = get_authenticated_service(credentials_file)

        # Retrieve and print the channel IDs for the authenticated user
        channels_response = youtube.channels().list(mine=True, part='id').execute()
        channel_ids = [channel['id'] for channel in channels_response['items']]
        print(f" => Channel IDs: {', '.join(channel_ids)}")

        # Initialize the upload process
        video_response = initialize_upload(youtube, {
            'file': video_path,  # The path to the video file
            'title': title,
            'description': description,
            'category': category,
            'keywords': keywords,
            'privacyStatus': privacy_status,
            'publishAt': publish_at  # Add the publishAt parameter
        })

        if thumbnail_path:
            set_thumbnail(youtube, video_response['id'], thumbnail_path)

        return video_response  # Return the response from the upload process
    except HttpError as e:
        print(f"[-] An HTTP error {e.resp.status} occurred:\n{e.content}")
        if e.resp.status in [401, 403]:
            # Here you could refresh the credentials and retry the upload
            youtube = get_authenticated_service(credentials_file)  # This will prompt for re-authentication if necessary
            video_response = initialize_upload(youtube, {
                'file': video_path,
                'title': title,
                'description': description,
                'category': category,
                'keywords': keywords,
                'privacyStatus': privacy_status,
                'publishAt': publish_at  # Add the publishAt parameter
            })
            if thumbnail_path:
                set_thumbnail(youtube, video_response['id'], thumbnail_path)
            return video_response
        else:
            raise e

def set_thumbnail(youtube, video_id, thumbnail_path):
    """
    This method sets the thumbnail for the uploaded video.

    Args:
        youtube (any): The authenticated YouTube service.
        video_id (str): The ID of the uploaded video.
        thumbnail_path (str): The path to the thumbnail image file.
    """
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        print(f"Thumbnail set for video id '{video_id}'.")
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred while setting the thumbnail:\n{e.content}")
