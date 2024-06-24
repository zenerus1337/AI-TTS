from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import torch
import os
import requests
from TTS.api import TTS
from PyPDF2 import PdfReader
import mammoth
from io import BytesIO
import tempfile
from pydub import AudioSegment

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

def split_text(text, max_sentences=4, max_symbols=200):
    sentences = text.split('. ')
    chunks = []
    current_chunk = []
    current_length = 0
    current_sentences = 0

    for sentence in sentences:
        sentence_length = len(sentence)
        if current_sentences < max_sentences and current_length + sentence_length <= max_symbols:
            current_chunk.append(sentence)
            current_length += sentence_length
            current_sentences += 1
        else:
            chunks.append('. '.join(current_chunk) + '.')
            current_chunk = [sentence]
            current_length = sentence_length
            current_sentences = 1

    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')

    return chunks

@app.route('/convert', methods=['POST'])
def convert_text_to_speech():
    content_type = request.headers.get('Content-Type', '')

    if 'application/json' in content_type:
        data = request.get_json()
        text = data.get('text', '')
        api_type = data.get('apiType', 'TTS')
        language = data.get('language', 'en')
        model_or_voice = data.get('model', 'default') if api_type == 'TTS' else data.get('voice', None)
        model_id = data.get('model_id', None)
        api_key = data.get('api_key')
        print(f"Received JSON request: text={text}, apiType={api_type}, language={language}, model_or_voice={model_or_voice}, model_id={model_id}, api_key={api_key}")
    elif 'multipart/form-data' in content_type:
        text = request.form.get('text', '')
        api_type = request.form.get('apiType', 'TTS')
        language = request.form.get('language', 'en')
        model_or_voice = request.form.get('model', 'default') if api_type == 'TTS' else request.form.get('voice', None)
        model_id = request.form.get('model_id', None)
        api_key = request.form.get('api_key')
        print(f"Received form-data request: text={text}, apiType={api_type}, language={language}, model_or_voice={model_or_voice}, model_id={model_id}, api_key={api_key}")
        if 'file' in request.files:
            file = request.files['file']
            file_type = file.filename.split('.')[-1].lower()
            if file_type == 'pdf':
                reader = PdfReader(file)
                text = ''.join([page.extract_text() or "" for page in reader.pages])
            elif file_type == 'docx':
                buffer = BytesIO(file.read())
                result = mammoth.extract_raw_text(buffer)
                text = result.value
            elif file_type == 'txt':
                text = file.read().decode('utf-8')
    else:
        return jsonify({'error': 'Unsupported Media Type'}), 415

    if not text.strip():
        print("No text provided for synthesis.")
        return jsonify({'error': 'No text provided for synthesis'}), 400

    if not api_key:
        print("API key is required for ElevenLabs and was not provided.")
        return jsonify({'error': 'API key is required for ElevenLabs'}), 400

    if api_type == 'TTS':
        return handle_tts_api(text, language, model_or_voice)
    elif api_type == 'ElevenLabs':
        return handle_elevenlabs_api(text, model_or_voice, model_id, api_key)
    else:
        return jsonify({'error': 'Unsupported API type'}), 400

def handle_tts_api(text, language, model):
    default_model_path = "tts_models/en/ljspeech/tacotron2-DDC"
    model_path = tts_model_paths.get(language, {'default': default_model_path}).get(model, default_model_path)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS(model_path).to(device)

    try:
        chunks = split_text(text)
        audio_segments = []
        
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_chunk_file:
                tts.tts_to_file(text=chunk, file_path=temp_chunk_file.name)
                audio_segment = AudioSegment.from_wav(temp_chunk_file.name)
                audio_segments.append(audio_segment)
                os.remove(temp_chunk_file.name)
        
        print("Merging audio segments")
        final_audio = sum(audio_segments)

        print("Exporting final audio")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as final_temp_file:
            final_audio.export(final_temp_file.name, format="wav")
        
        return send_file(final_temp_file.name, as_attachment=True)
    except Exception as e:
        print("Error during TTS synthesis:", e)
        return jsonify({'error': 'Error during TTS synthesis'}), 500

def handle_elevenlabs_api(text, voice_id, model_id, api_key):
    if not api_key:
        return jsonify({'error': 'API key is required for ElevenLabs'}), 400

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        'xi-api-key': api_key,
        'Content-Type': 'application/json'
    }

    print(f"Using API Key: {api_key}")

    try:
        chunks = split_text(text)
        audio_segments = []
        
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}")
            payload = {
                "text": chunk,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                },
                "model_id": model_id
            }
            response = requests.post(url, json=payload, headers=headers)
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_chunk_file:
                    temp_chunk_file.write(response.content)
                    temp_chunk_file_path = temp_chunk_file.name
                
                try:
                    audio_segment = AudioSegment.from_file(temp_chunk_file_path, format="mp3")
                    audio_segments.append(audio_segment)
                except Exception as e:
                    print(f"Error loading audio file {temp_chunk_file_path}: {e}")
                    return jsonify({'error': f'Error loading audio file: {e}'}), 500
                finally:
                    os.remove(temp_chunk_file_path)
            else:
                print(f"Failed to create audio file with ElevenLabs. Status code: {response.status_code}")
                return jsonify(response.json()), response.status_code
        
        print("Merging audio segments")
        final_audio = sum(audio_segments)

        print("Exporting final audio")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as final_temp_file:
            final_audio.export(final_temp_file.name, format="wav")

        return send_file(final_temp_file.name, as_attachment=True)
    except Exception as e:
        print(f"An error occurred with ElevenLabs API: {e}")
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)