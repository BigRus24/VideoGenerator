import random

from elevenlabs import save
from elevenlabs.client import ElevenLabs

from utils.settings import config

voices = [
    "Adam",
    "Antoni",
    "Arnold",
    "Bella",
    "Domi",
    "Elli",
    "Josh",
    "Rachel",
    "Sam",
]


class elevenlabs:
    def __init__(self):
        self.max_chars = 2500
        self.voices = voices

    def run(self, text, filepath, random_voice: bool = False):
        if random_voice:
            voice = self.randomvoice()
        else:
            voice = str(config["settings"]["tts"]["elevenlabs_voice_name"]).capitalize()

        if config["settings"]["tts"]["elevenlabs_api_key"]:
            api_key = config["settings"]["tts"]["elevenlabs_api_key"]
        else:
            raise ValueError(
                "You didn't set an Elevenlabs API key! Please set the config variable ELEVENLABS_API_KEY to a valid API key."
            )

        client = ElevenLabs(api_key=api_key)

        audio = client.generate(text=text, voice=voice, model="eleven_multilingual_v1")
        save(audio=audio, filename=filepath)

    def randomvoice(self):
        return random.choice(self.voices)
