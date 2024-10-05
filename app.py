from flask import Flask, request, send_file, render_template
from flask_socketio import SocketIO, emit
from langchain_community.llms import Ollama
from pdfExtractor import extractText
from audioModelLoader import loadModel, generateAudio
from pydub import AudioSegment
import os

app = Flask(__name__, static_folder='public', static_url_path='/public')

socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_podcast', methods=['POST'])
def generate_podcast():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    # Save the uploaded file
    file_path = f"files/temp_{file.filename}"
    file.save(file_path)

    # Emit progress update
    socketio.emit('progress', {'progress': 0, 'message': 'Extracting text from the file...'})

    # Extract text from the file
    content = extractText(file_path)

    PODLM = Ollama(model="PODLM4")

    femalePrompt = "v2/en_speaker_9"
    malePrompt = "v2/en_speaker_6"

    # Emit progress update
    socketio.emit('progress', {'progress': 10, 'message': 'Generating podcast content...'})
    print("Generating podcast...")
    podcast = PODLM.invoke(input=content)
    print(podcast)

    audioModel, processor = loadModel()

    # Remove "Female:" and "Male:" prefixes and split into lines
    podcastList = []
    for line in podcast.split("\n"):
        if line.startswith("Female:"):
            podcastList.append(line[7:])
        elif line.startswith("Male:"):
            podcastList.append(line[6:])

    combined_audio = AudioSegment.empty()

    for i in range(0, len(podcastList), 2):
        print(i)
        if len(podcastList[i].strip()) == 0:
            continue

        femaleAudio, sample_rateF = generateAudio(audioModel, processor, podcastList[i], femalePrompt)
        female_segment = AudioSegment(
            femaleAudio.tobytes(),
            frame_rate=sample_rateF,
            sample_width=2,  # 2 bytes for int16
            channels=1
        )
        combined_audio += female_segment

        if i + 1 < len(podcastList) and len(podcastList[i + 1].strip()) > 0:
            maleAudio, sample_rateM = generateAudio(audioModel, processor, podcastList[i + 1], malePrompt)
            male_segment = AudioSegment(
                maleAudio.tobytes(),
                frame_rate=sample_rateM,
                sample_width=2,  # 2 bytes for int16
                channels=1
            )
            combined_audio += male_segment

        # Emit progress update
        progress = int((i + 2) / len(podcastList) * 100)
        socketio.emit('progress', {'progress': progress, 'message': f'Processing segment {i//2 + 1} of {len(podcastList)//2}...'})

    # Emit progress update
    socketio.emit('progress', {'progress': 90, 'message': 'Finalizing the podcast...'})

    # Export the combined audio to a single file
    output_file = "ouputs/podcast.wav"
    combined_audio.export(output_file, format="wav")

    # Remove the temporary file
    os.remove(file_path)

    # Emit progress update
    socketio.emit('progress', {'progress': 100, 'message': 'Podcast generation completed!'})

    return send_file(output_file, mimetype="audio/wav", as_attachment=True, download_name=output_file)

if __name__ == "__main__":
    socketio.run(app, port=5000, debug=True, use_reloader=True)