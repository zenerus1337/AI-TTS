from flask import Flask, request, send_file
from flask_cors import CORS
import torch
from TTS.api import TTS
import os

app = Flask(__name__)
CORS(app)  # This will enable Cross-Origin Resource Sharing (CORS) for all domains

@app.route('/convert', methods=['POST'])
def convert_text_to_speech():
    # Get text from the request
    data = request.get_json()
    text = data['text']
    
    # Set the device
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Initialize the TTS
    tts = TTS("tts_models/en/ljspeech/tacotron2-DDC").to(device)

    # Generate speech and save to a file
    file_path = os.path.join(os.getcwd(), "output.wav")
    tts.tts_to_file(text=text, file_path=file_path)

    # Return the generated file
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)