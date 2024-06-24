import React, { useState, useEffect } from 'react';
import logo from './hampter.png';
import './App.css';

function App() {
  const [audioUrl, setAudioUrl] = useState("");
  const [apiType, setApiType] = useState("TTS");
  const [language, setLanguage] = useState("en");
  const [modelOrVoice, setModelOrVoice] = useState("default");
  const [statusMessage, setStatusMessage] = useState("");
  const [apiKey] = useState("42659e288ccfa8b1e5aa4881e52b7fd7"); // Set the API key as a static value

  const ttsModels = {
    'en': [
      { name: "Default (Tacotron2-DDC)", id: "default" },
      { name: "Speedy Speech", id: "speedy-speech" },
      { name: "Fast Pitch", id: "fast-pitch" },
      { name: "Overflow", id: "overflow" },
      { name: "Neural HMM", id: "neural-hmm" }
    ],
    'pl': [
      { name: "VITS", id: "vits" }
    ]
  };

  const elevenLabsVoices = {
    'en': [
      { name: "Jessica", id: "lxYfHSkYm1EzQzGhdbfc" }
    ],
    'pl': [
      { name: "Aneta", id: "Pid5DJleNF2sxsuF6YKD" },
      { name: "Adygeusz", id: "DK2oYoQ3lTA1UXL843GC" },
      { name: "Przemek", id: "KziPYiGoJuECE51R7lYo" }
    ]
  };

  useEffect(() => {
    if (apiType === "TTS") {
      setModelOrVoice(ttsModels[language][0].id);
    } else {
      setModelOrVoice(elevenLabsVoices[language][0].id);
    }
  }, [apiType, language]);

  const handleTextChange = (event) => {};

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      convertFileToSpeech(file);
    }
  };

  const convertTextToSpeech = (text) => {
    if (!text.trim()) {
      alert("Please enter some text to convert to speech.");
      return;
    }
    setStatusMessage("Converting text to speech...");
    const payload = {
      text: text,
      language: language,
      apiType: apiType,
      api_key: apiKey // Include the API key in the payload
    };
    if (apiType === "TTS") {
      payload.model = modelOrVoice;
    } else {
      payload.voice = modelOrVoice;
      payload.model_id = language === "en" ? "eleven_turbo_v2" : "eleven_multilingual_v2";
    }

    fetch("http://localhost:5000/convert", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    })
    .then(response => response.blob())
    .then(blob => {
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      setStatusMessage("Conversion done. Play the audio below.");
    })
    .catch(error => {
      console.error('Error during text-to-speech conversion:', error);
      setStatusMessage("Failed to convert text to speech.");
    });
  };

  const convertFileToSpeech = (file) => {
    setStatusMessage("Converting file to speech...");
    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', language);
    formData.append('apiType', apiType);
    formData.append('api_key', apiKey); // Include the API key in the form data

    if (apiType === "TTS") {
      formData.append('model', modelOrVoice);
    } else {
      formData.append('voice', modelOrVoice);
      formData.append('model_id', language === "en" ? "eleven_turbo_v2" : "eleven_multilingual_v2");
    }

    fetch("http://localhost:5000/convert", {
      method: "POST",
      body: formData // Do not set 'Content-Type' manually here
    })
    .then(response => response.blob())
    .then(blob => {
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      setStatusMessage("Conversion done. Play the audio below.");
    })
    .catch(error => {
      console.error('Error during file-to-speech conversion:', error);
      setStatusMessage("Failed to convert file to speech.");
    });
  };

  const getModelOrVoiceOptions = () => {
    return apiType === "TTS" ? ttsModels[language] : elevenLabsVoices[language];
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI-TTS</h1>
        <img src={logo} className="App-logo" alt="logo" />
        <p>Text to audio converter</p>
        <div>
          <select value={apiType} onChange={e => setApiType(e.target.value)}>
            <option value="TTS">TTS</option>
            <option value="ElevenLabs">ElevenLabs</option>
          </select>
        </div>
        <textarea className="App-input" placeholder="Enter your text here..." onChange={handleTextChange}></textarea>
        <input type="file" accept=".txt,.pdf,.docx" onChange={handleFileChange} />
        <div>
          <select value={language} onChange={e => setLanguage(e.target.value)}>
            <option value="en">English</option>
            <option value="pl">Polish</option>
          </select>
          <select value={modelOrVoice} onChange={e => setModelOrVoice(e.target.value)}>
            {getModelOrVoiceOptions().map(option => (
              <option key={option.id} value={option.id}>{option.name}</option>
            ))}
          </select>
        </div>
        <button className="App-convert-button" onClick={() => convertTextToSpeech(document.querySelector('.App-input').value)}>Convert</button>
        {statusMessage && <p className="App-status-message">{statusMessage}</p>}
        {audioUrl && <audio controls src={audioUrl}>Your browser does not support the audio element.</audio>}
      </header>
    </div>
  );
}

export default App;