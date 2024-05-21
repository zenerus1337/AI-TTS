import React, { useState } from 'react';
import logo from './hampter.png';
import './App.css';

function App() {
  const [audioUrl, setAudioUrl] = useState("");

  const handleTextChange = (event) => {
    convertTextToSpeech(event.target.value);
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      convertFileToSpeech(file);
    }
  };

  const convertTextToSpeech = (text) => {
    fetch("http://localhost:5000/convert", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text: text })
    })
    .then(response => response.blob())
    .then(blob => {
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
    });
  };

  const convertFileToSpeech = (file) => {
    const formData = new FormData();
    formData.append('file', file);

    fetch("http://localhost:5000/convert", {
      method: "POST",
      body: formData
    })
    .then(response => response.blob())
    .then(blob => {
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
    });
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI-TTS</h1>
        <img src={logo} className="App-logo" alt="logo" />
        <p>Text to audio converter</p>
        <textarea className="App-input" placeholder="Enter your text here..." onChange={handleTextChange}></textarea>
        <input type="file" accept=".txt,.pdf,.docx" onChange={handleFileChange} />
        <button className="App-convert-button" onClick={() => convertTextToSpeech(document.querySelector('.App-input').value)}>Convert</button>
        {audioUrl && <audio controls src={audioUrl}>Your browser does not support the audio element.</audio>}
      </header>
    </div>
  );
}

export default App;
