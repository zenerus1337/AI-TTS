from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import torch
import os
import requests
from TTS.api import TTS
from PyPDF2 import PdfReader
import mammoth
from io import BytesIO

app = Flask(__name__)
CORS(app)

tts_model_paths = {
    'en': {
        'speedy-speech': "tts_models/en/ljspeech/speedy-speech",
        'fast-pitch': "tts_models/en/ljspeech/fast_pitch",
        'overflow': "tts_models/en/ljspeech/overflow",
        'neural-hmm': "tts_models/en/ljspeech/neural_hmm",
        'default': "tts_models/en/ljspeech/tacotron2-DDC"
    },
    'pl': {
        'vits': "tts_models/pl/mai_female/vits",
        'default': "tts_models/pl/mai_female/vits"
    }
}

elevenlabs_voices = {
    'en': ['lxYfHSkYm1EzQzGhdbfc'],
    'pl': ['Pid5DJleNF2sxsuF6YKD', 'DK2oYoQ3lTA1UXL843GC']
}

@app.route('/convert', methods=['POST'])
def convert_text_to_speech():
    api_type = request.values.get('apiType', 'TTS')
    language = request.values.get('language', 'en')
    model_or_voice = request.values.get('model', 'default') if api_type == 'TTS' else request.values.get('voice', None)
    model_id = request.values.get('model_id', None)
    text = request.values.get('text', '')

    if 'file' in request.files:
        file = request.files['file']
        print("Received file:", file.filename)
        file_type = file.filename.split('.')[-1].lower()
        print("File extension:", file_type)
        if file_type == 'pdf':
            reader = PdfReader(file)
            text = ''.join([page.extract_text() or "" for page in reader.pages])
        elif file_type == 'docx':
            buffer = BytesIO(file.read())
            result = mammoth.extract_raw_text(buffer)
            text = result.value
        elif file_type == 'txt':
            text = file.read().decode('utf-8')

    if not text.strip():
        return jsonify({'error': 'No text provided for synthesis'}), 400

    if api_type == 'TTS':
        return handle_tts_api(text, language, model_or_voice)
    elif api_type == 'ElevenLabs':
        return handle_elevenlabs_api(text, model_or_voice, model_id)

def handle_tts_api(text, language, model):
    default_model_path = "tts_models/en/ljspeech/tacotron2-DDC"
    model_path = tts_model_paths.get(language, {'default': default_model_path}).get(model, default_model_path)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS(model_path).to(device)

    file_path = os.path.join(os.getcwd(), "output.wav")
    try:
        tts.tts_to_file(text=text, file_path=file_path)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        print("Error during TTS synthesis:", e)
        return jsonify({'error': 'Error during TTS synthesis'}), 500

def handle_elevenlabs_api(text, voice_id, model_id):
    API_KEY = '42659e288ccfa8b1e5aa4881e52b7fd7'
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        'xi-api-key': API_KEY,
        'Content-Type': 'application/json'
    }

    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        },
        "model_id": model_id
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            file_path = os.path.join(os.getcwd(), "output.wav")
            with open(file_path, "wb") as file:
                file.write(response.content)
            return send_file(file_path, as_attachment=True)
        else:
            print(f"Failed to create WAV file with ElevenLabs. Status code: {response.status_code}")
            return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        print(f"An error occurred with ElevenLabs API: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
