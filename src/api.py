from flask import Flask, request, send_file
from flask_cors import CORS
import torch
from TTS.api import TTS
import os
from PyPDF2 import PdfReader  # Updated import here
import mammoth
from io import BytesIO

app = Flask(__name__)
CORS(app)

@app.route('/convert', methods=['POST'])
def convert_text_to_speech():
    # Initialize the TTS model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS("tts_models/en/ljspeech/tacotron2-DDC").to(device)
    
    # Prepare text variable
    text = ""

    if 'file' in request.files:
        file = request.files['file']
        file_type = file.filename.split('.')[-1].lower()
        
        if file_type == 'pdf':
            # Updated to use PdfReader
            reader = PdfReader(file)
            text = ''.join([page.extract_text() or "" for page in reader.pages])
        
        elif file_type == 'docx':
            # Use mammoth to convert DOCX to text
            buffer = BytesIO(file.read())
            result = mammoth.extract_raw_text(buffer)
            text = result.value
        
        elif file_type == 'txt':
            # Read text files directly
            text = file.read().decode('utf-8')
    
    elif 'text' in request.json:
        text = request.json['text']

    # Generate speech and save to a file
    file_path = os.path.join(os.getcwd(), "output.wav")
    tts.tts_to_file(text=text, file_path=file_path)

    # Return the generated file
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
