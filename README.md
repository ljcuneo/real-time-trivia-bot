# Real-Time Trivia Answering Bot

A Python-based bot that listens for trivia questions and provides answers in real-time using speech recognition and web search capabilities.

## Features

- Speech Recognition (Google Speech-to-Text and Whisper AI)
- Real-time web search for answers
- Text-to-Speech response
- Performance optimization (< 10 seconds response time)
- Error handling and logging
- Hotkey activation support

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the bot:
```bash
python src/main.py
```

## Usage

1. Press the configured hotkey (default: Ctrl+Shift+L) to start listening
2. Speak your trivia question clearly
3. Wait for the bot to process and respond
4. The answer will be displayed and read aloud

## Configuration

- Create a `.env` file in the project root with the following options:
```
SPEECH_RECOGNITION_ENGINE=google  # or whisper
SEARCH_ENGINE=google  # or serpapi or bing
SERPAPI_KEY=your_key_here  # Optional: Only if using SerpAPI
BING_API_KEY=your_key_here  # Optional: Only if using Bing Search API
```

## Requirements

- Python 3.8+
- Microphone access
- Internet connection
- System audio output (for text-to-speech) 