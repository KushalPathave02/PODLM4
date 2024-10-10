
from langchain_community.llms import Ollama
from pdfExtractor import extractText

def getPodcast(model, content):
    podcast = model.invoke(input=content)
    return podcast

def divideContent(content, num_segments=8):
    segment_length = len(content) // num_segments
    return [content[i * segment_length:(i + 1) * segment_length] for i in range(num_segments)]

def generateSegmentedPodcast(model, content,socketio,lines=2,):
    PODLM4 = Ollama(model=model)
    segments = divideContent(content)
    previous_podcast = ""
    full_podcast = ""
    i = 0
    for segment in segments:
        socketio.emit('progress', {'progress': i*2, 'message': f'Generating podcast content...({str(i+1)}/8)'})

        input_content = "History: " + (previous_podcast if previous_podcast != "" else "First Segment") + "\nNew Segment: " + segment
        podcast_segment = getPodcast(PODLM4, input_content)
        full_podcast += podcast_segment + "\n"
        previous_podcast += "\n".join(podcast_segment.split("\n")[-lines:]) 

        print( podcast_segment)
    print(full_podcast)

    return full_podcast