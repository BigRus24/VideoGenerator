import os
import g4f
import openai
import google.generativeai as genai

from g4f.client import Client
from utils.settings import config


# Set environment variables
OPENAI_API_KEY = "sk-proj-nUfyRKF3BSM8rEdSjn9MT3BlbkFJZgskDi80b6E6sabZdwO4"
openai.api_key = OPENAI_API_KEY
GOOGLE_API_KEY = ""
genai.configure(api_key=GOOGLE_API_KEY)


def generate_response(prompt: str, ai_model: str, json_output = False) -> str:
    
    response_format = {"type": "json_object"} if json_output else {"type": "text"}
    
    if ai_model == 'g4f':
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4o",
            provider=g4f.Provider.You,
            response_format=response_format,
            messages=[{"role": "user", "content": prompt}],
        ).choices[0].message.content

    elif ai_model in ["gpt3.5-turbo", "gpt4", "gpt-4o"]:

        model_name = "gpt-3.5-turbo" if ai_model == "gpt3.5-turbo" else "gpt-4-1106-preview"

        response = openai.chat.completions.create(

            model=model_name,
            response_format=response_format,
            messages=[{"role": "user", "content": prompt}],

            
        ).choices[0].message.content
    elif ai_model == 'gemmini':
        model = genai.GenerativeModel('gemini-pro')
        response_model = model.generate_content(prompt)
        response = response_model.text

    else:

        raise ValueError("Invalid AI model selected.")

    return response


def generate_audio(input: str):
    
        
    response = openai.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=input,
    )

    return response


def generate_transcript(audio_file_path: str):
    with open(audio_file_path, "rb") as audio_file:
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )

    # Convert the response to a dictionary
    response_dict = response.dict()

    # Ensure the response contains the 'words' key
    if 'words' in response_dict:
        return response_dict['words']
    else:
        raise TypeError("The response from the transcription API does not contain the expected keys.")