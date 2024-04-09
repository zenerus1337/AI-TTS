import logo from './hampter.png';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>AI-TTS</h1>
        <img src={logo} className="App-logo" alt="logo" />
        <p>Text to audio converter</p>
        <textarea className="App-input" placeholder="Enter your text here..."></textarea>
        <button className="App-convert-button">Convert</button> {/* Add this line */}
      </header>
    </div>
  );
}

export default App;