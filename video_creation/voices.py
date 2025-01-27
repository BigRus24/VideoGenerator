from typing import Tuple

from rich.console import Console

from TTS.GTTS import GTTS
from TTS.TikTok import TikTok
from TTS.aws_polly import AWSPolly
from TTS.elevenlabs import elevenlabs
from TTS.engine_wrapper import TTSEngine
from TTS.pyttsx import pyttsx
from TTS.streamlabs_polly import StreamlabsPolly
from TTS.gpt import GPT
from utils.settings import config

console = Console()

TTSProviders = {
    "GoogleTranslate": GTTS,
    "AWSPolly": AWSPolly,
    "StreamlabsPolly": StreamlabsPolly,
    "TikTok": TikTok,
    "pyttsx": pyttsx,
    "ElevenLabs": elevenlabs,
    "GPT": GPT
}


def save_text_to_mp3(reddit_obj) -> Tuple[int, int]:
    voice = config["settings"]["tts"]["voice_choice"]
    text_to_mp3 = TTSEngine(get_case_insensitive_key_value(TTSProviders, voice), reddit_obj)
    return text_to_mp3.run()


def get_case_insensitive_key_value(input_dict, key):
    return next(
        (value for dict_key, value in input_dict.items() if dict_key.lower() == key.lower()),
        None,
    )
