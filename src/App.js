import React, { useState } from 'react';
import logo from './hampter.png';
import './App.css';

function App() {
  const [text, setText] = useState("");
  const [audioUrl, setAudioUrl] = useState("");

  const handleTextChange = (event) => {
    setText(event.target.value);
  };

  const convertTextToSpeech = () => {
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

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI-TTS</h1>
        <img src={logo} className="App-logo" alt="logo" />
        <p>Text to audio converter</p>
        <textarea className="App-input" placeholder="Enter your text here..." onChange={handleTextChange}></textarea>
        <button className="App-convert-button" onClick={convertTextToSpeech}>Convert</button>
        {audioUrl && <audio controls src={audioUrl}>Your browser does not support the audio element.</audio>}
      </header>
    </div>
  );
}

export default App;