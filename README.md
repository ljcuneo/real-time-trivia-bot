# Real-Time Trivia Bot

A voice-activated trivia bot that can answer your questions in real-time using multiple search sources.

## Features

- Voice recognition for hands-free question asking
- Text-to-speech answers
- Multiple search sources (SERP API, Google, DuckDuckGo)
- Special handling for math questions and capital cities
- Web interface for easy interaction
- Command-line interface for voice interaction

## Setup

1. Clone the repository:
```bash
git clone https://github.com/ljcuneo/real-time-trivia-bot.git
cd real-time-trivia-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your SERP API key:
```
SERP_API_KEY=your_api_key_here
```

## Usage

### Web Interface

1. Start the web server:
```bash
python src/app.py
```

2. Open your browser and navigate to `http://localhost:5000`

3. Type your question in the input field and click "Ask Question"

4. The answer will appear below with text-to-speech output (if available)

### Command Line Interface (Voice Mode)

1. Start the bot:
```bash
python src/main.py
```

2. Press Enter to start/stop listening mode

3. Ask your question clearly when listening is active

4. Press Ctrl+C to exit

## Search Sources

The bot uses multiple search sources in the following order:
1. SERP API (if API key is provided)
2. Direct calculation for math questions
3. Google search
4. DuckDuckGo as fallback

## Contributing

Feel free to open issues or submit pull requests for improvements.

## License

MIT License 