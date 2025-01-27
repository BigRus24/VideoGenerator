import re
import json
from typing import List, Tuple
from uuid import uuid4
from utils.posttextparser import posttextparser
from utils.gpt import generate_response


def generate_story(subject, paragraph_number, ai_model, voice):    
    content = {}
    
    script = generate_story(subject, paragraph_number, voice, ai_model)
    
    title = generate_story_title(subject, script, ai_model, voice)
    
    seotitle = generate_story_seo_title(subject, script, ai_model, voice)
    
    seodescription = generate_story_seo_description(subject, script, ai_model, voice)
    
    seokeywords = generate_story_seo_keywords(subject, 5, script, ai_model)
    
    content["id"] = str(uuid4())
    content["title"] = title
    content["seo_title"] = seotitle
    content["seo_description"] = seodescription
    content["seo_keywords"] = seokeywords
    content["content"] = posttextparser(script)

    print(content["title"])
    print(content["seo_title"])
    print(content["seo_description"])
    print(content["seo_keywords"])
    print(content["content"])
    
    return content


def generate_story(video_subject: str, paragraph_number: int, voice: str, ai_model: str):
    prompt = f"""
    Generate a script for a video about {video_subject}.
    The script should be engaging and informative.
    The video should be {paragraph_number} paragraphs long.
    The script should be written in {voice}.
    
    YOU MUST NOT INCLUDE ANY TYPE OF MARKDOWN OR FORMATTING IN THE SCRIPT.
    ONLY RETURN THE RAW CONTENT OF THE SCRIPT. DO NOT INCLUDE "VOICEOVER", "NARRATOR" OR SIMILAR INDICATORS OF WHAT SHOULD BE SPOKEN AT THE BEGINNING OF EACH PARAGRAPH OR LINE.
    """

    prompt += f"""
    
    Subject: {video_subject}
    Number of paragraphs: {paragraph_number}
    Language: {voice}

    """

    # Generate script
    response = generate_response(prompt, ai_model)

    if response:
        # Clean the script
        response = re.sub(r"[*#\[\]()]", "", response)

        # Split the script into paragraphs
        paragraphs = response.split("\n\n")[:paragraph_number]

        final_script = "\n\n".join(paragraphs)

        print(f"Number of paragraphs used: {len(paragraphs)}")
        return final_script
    else:
        print("[-] GPT returned an empty response.")
        return ""


def generate_story_title(video_subject: str, script: int, ai_model: str, voice: str) -> str:
    prompt = """
            Generate a title for a video, depending on the subject of the video.

            Do not under any circumstance reference this prompt in your response.

            Get straight to the point, don't start with unnecessary things like, "welcome to this video".

            Obviously, the title should be related to the subject of the video.

            YOU MUST NOT INCLUDE ANY TYPE OF MARKDOWN OR FORMATTING IN THE TITLE.
            ONLY RETURN THE RAW CONTENT OF THE TITLE. DO NOT INCLUDE "VOICEOVER", "NARRATOR" OR SIMILAR INDICATORS OF WHAT SHOULD BE SPOKEN AT THE BEGINNING OF EACH PARAGRAPH OR LINE. YOU MUST NOT MENTION THE PROMPT, OR ANYTHING ABOUT THE TITLE ITSELF.

        """
        
    prompt += f"""
    
    Subject: {video_subject}
    Language: {voice}

    """
        
    response = generate_response(prompt, ai_model)
    
    return response

    
def generate_story_seo_title(video_subject: str, script: int, ai_model: str, voice: str) -> str:
    prompt = """
            Generate a title for a video, depending on the subject of the video.

            Do not under any circumstance reference this prompt in your response.

            Get straight to the point, don't start with unnecessary things like, "welcome to this video".

            Obviously, the title should be related to the subject of the video.

            YOU MUST NOT INCLUDE ANY TYPE OF MARKDOWN OR FORMATTING IN THE TITLE.
            ONLY RETURN THE RAW CONTENT OF THE TITLE. DO NOT INCLUDE "VOICEOVER", "NARRATOR" OR SIMILAR INDICATORS OF WHAT SHOULD BE SPOKEN AT THE BEGINNING OF EACH PARAGRAPH OR LINE. YOU MUST NOT MENTION THE PROMPT, OR ANYTHING ABOUT THE TITLE ITSELF.

        """
        
    prompt += f"""
    
    Subject: {video_subject}
    Language: {voice}

    """
        
    response = generate_response(prompt, ai_model)
    
    return response
        
        
def generate_story_seo_description(video_subject: str, script: int, ai_model: str, voice: str) -> str:
    prompt = """
            Generate a description for a video, depending on the subject of the video.

            Do not under any circumstance reference this prompt in your response.

            Get straight to the point, don't start with unnecessary things like, "welcome to this video".

            Obviously, the description should be related to the subject of the video.

            YOU MUST NOT INCLUDE ANY TYPE OF MARKDOWN OR FORMATTING IN THE DESCRIPTION.
            ONLY RETURN THE RAW CONTENT OF THE DESCRIPTION. DO NOT INCLUDE "VOICEOVER", "NARRATOR" OR SIMILAR INDICATORS OF WHAT SHOULD BE SPOKEN AT THE BEGINNING OF EACH PARAGRAPH OR LINE. YOU MUST NOT MENTION THE PROMPT, OR ANYTHING ABOUT THE DESCRIPTION ITSELF.

        """
        
    prompt += f"""
    
    Subject: {video_subject}
    Language: {voice}

    """
    
    response = generate_response(prompt, ai_model)
    
    return response
        
    
def generate_story_seo_keywords(video_subject: str, amount: int, script: str, ai_model: str) -> List[str]:
    prompt = f"""
    Generate {amount} search terms for stock videos,
    depending on the subject of a video.
    Subject: {video_subject}

    The search terms are to be returned as
    a JSON-Array of strings.

    Each search term should consist of 1-3 words,
    always add the main subject of the video.
    
    YOU MUST ONLY RETURN THE JSON-ARRAY OF STRINGS.
    YOU MUST NOT RETURN ANYTHING ELSE. 
    YOU MUST NOT RETURN THE SCRIPT.
    
    Do not include any explanations, only provide a 
    RFC8259 compliant JSON response 
    following this format without deviation.
    ["search term 1", "search term 2", "search term 3"]

    For context, here is the full text:
    {script}
    """
    
    # Generate search terms
    response = generate_response(prompt, ai_model, json_output=True)
    print(response)

    try:
        search_terms = json.loads(response)
        if isinstance(search_terms, list) and all(isinstance(term, str) for term in search_terms):
            print(f"\nGenerated {len(search_terms)} search terms: {', '.join(search_terms)}")
            return search_terms
    except json.JSONDecodeError:
        print("[*] GPT returned an unformatted response. Attempting to clean...")

    # Attempt to clean and parse the response
    cleaned_response = "[" + response[response.find("[") + 1:response.rfind("]")] + "]"
    try:
        search_terms = json.loads(cleaned_response)
        if isinstance(search_terms, list) and all(isinstance(term, str) for term in search_terms):
            return search_terms
    except json.JSONDecodeError:
        print("[-] Could not parse response.")

    return []