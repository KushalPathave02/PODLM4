from flask import Flask, request, send_file, render_template, jsonify
from flask_socketio import SocketIO, emit
from podcastGenerate import generateSegmentedPodcast
from pdfExtractor import extractText
from audioModelLoader import loadModel, generateAudio
from pydub import AudioSegment
from RAG import addDocumentToVectorDb, generateResponse
import os

app = Flask(__name__, static_folder='public', static_url_path='/public')
socketio = SocketIO(app)
conversationHistory = ""

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

    file_path = f"files/temp_{file.filename}"
    file.save(file_path)

    socketio.emit('progress', {'progress': 0, 'message': 'Extracting text from the file...'})

    print("Generating podcast content...")
    podcast = generateSegmentedPodcast("PODLM4", extractText(file_path), socketio)
    print(podcast)


    femalePrompt = "v2/en_speaker_9"
    malePrompt = "v2/en_speaker_6"

    audioModel, processor = loadModel()


    podcastList = [line[7:] if line.startswith("Female:") else line[6:] for line in podcast.split("\n") if line.startswith(("Female:", "Male:"))]

    combined_audio = AudioSegment.empty()


    for i in range(0, len(podcastList), 2):
        if len(podcastList[i].strip()) == 0:
            continue

        femaleAudio, sample_rateF = generateAudio(audioModel, processor, podcastList[i], femalePrompt)
        female_segment = AudioSegment(
            femaleAudio.tobytes(),
            frame_rate=sample_rateF,
            sample_width=2,  
            channels=1
        )
        combined_audio += female_segment

        if i + 1 < len(podcastList) and len(podcastList[i + 1].strip()) > 0:
            maleAudio, sample_rateM = generateAudio(audioModel, processor, podcastList[i + 1], malePrompt)
            male_segment = AudioSegment(
                maleAudio.tobytes(),
                frame_rate=sample_rateM,
                sample_width=2,
                channels=1
            )
            combined_audio += male_segment

        progress = int((i + 2) / len(podcastList) * 100)
        
        socketio.emit('progress', {'progress': progress, 'message': f'Processing segment {i//2 + 1} of {len(podcastList)//2}...'})

    socketio.emit('progress', {'progress': 90, 'message': 'Finalizing the podcast...'})

    output_file = "outputs/podcast.wav"
    combined_audio.export(output_file, format="wav")
    os.remove(file_path)

    socketio.emit('progress', {'progress': 100, 'message': 'Podcast generation completed!'})
    return send_file(output_file, mimetype="audio/wav", as_attachment=True, download_name=output_file)

@app.route('/upload_rag_file', methods=['POST'])
def upload_rag_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    file_path = f"files/rag_{file.filename}"
    file.save(file_path)

    content = extractText(file_path)
    addDocumentToVectorDb(file.filename, content)
    os.remove(file_path)

    return jsonify({'message': 'RAG file uploaded and processed successfully!'})

@app.route('/chat', methods=['POST'])
def chat():
    global conversationHistory
    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({'answer': 'No question provided.'}), 400


    conversationHistory+= f"User: {question}\n"


    answer = generateResponse(conversationHistory, question)

    conversationHistory+= f"Bot: {answer}\n"

    return jsonify({'answer': answer})


if __name__ == "__main__":
    socketio.run(app, port=5230, debug=True, use_reloader=True)