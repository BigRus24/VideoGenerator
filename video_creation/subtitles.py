import datetime
from utils.gpt import generate_transcript


def convert_to_srt(words: list, start_offset: float) -> str:
    srt = []
    for i, word in enumerate(words):
        start_time = datetime.timedelta(seconds=word['start'] + start_offset)
        end_time = datetime.timedelta(seconds=word['end'] + start_offset)
        text = word['word']
        
        srt.append(f"{i + 1}")
        srt.append(f"{str(start_time)[:-3].replace('.', ',')} --> {str(end_time)[:-3].replace('.', ',')}")
        srt.append(text)
        srt.append("")

    return "\n".join(srt)

def generate_srt_file(audio_file_path: str, output_path: str, start_offset: float):
    words = generate_transcript(audio_file_path)
    srt_content = convert_to_srt(words, start_offset)

    with open(output_path, "w") as srt_file:
        srt_file.write(srt_content)