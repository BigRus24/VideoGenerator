import random


from utils.gpt import generate_audio 
from utils.settings import config


class GPT:
    def __init__(self):
        self.max_chars = 5000
        self.voices = []

    def run(self, text, filepath, random_voice: bool = False):
        response = generate_audio(text)
        
        response.stream_to_file(filepath)