import os
import time
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple
import platform
import sys
import threading
import signal

from services.speech_recognition_service import SpeechRecognitionService
from services.search_service import SearchService
from services.tts_service import TTSService

class TriviaBot:
    def __init__(self):
        """Initialize the Trivia Bot with its services."""
        try:
            self.search_service = SearchService()
            self.speech_service = SpeechRecognitionService()
            self.tts_service = TTSService()
            self.is_listening = False
            self.listen_thread = None
            logger.info("Trivia Bot initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Trivia Bot: {e}")
            raise

    def start(self):
        """Start the bot in CLI mode."""
        try:
            # Set up signal handler for graceful shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            
            logger.info("Starting Trivia Bot...")
            logger.info("Press Enter to start/stop listening")
            logger.info("Press Ctrl+C to exit")
            
            while True:
                input()  # Wait for Enter key
                self.toggle_listening()
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.cleanup()
            sys.exit(1)

    def get_answer(self, question: str) -> str:
        """Get answer for a question (web interface mode)."""
        try:
            logger.info(f"Processing question: {question}")
            answer = self.search_service.search_for_answer(question)
            
            if answer:
                # Speak the answer if TTS is available
                try:
                    self.tts_service.speak(answer)
                except Exception as e:
                    logger.warning(f"TTS failed: {e}")
                return answer
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting answer: {e}")
            return None

    def toggle_listening(self):
        """Toggle the listening state."""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        """Start listening for questions."""
        if not self.is_listening:
            self.is_listening = True
            logger.info("Listening activated")
            self.listen_thread = threading.Thread(target=self.listen_loop)
            self.listen_thread.daemon = True
            self.listen_thread.start()

    def stop_listening(self):
        """Stop listening for questions."""
        if self.is_listening:
            self.is_listening = False
            logger.info("Listening deactivated")
            if self.listen_thread:
                self.listen_thread.join(timeout=1)

    def listen_loop(self):
        """Main listening loop."""
        while self.is_listening:
            try:
                self.listen_and_answer()
            except Exception as e:
                logger.error(f"Error in listening loop: {e}")
                self.is_listening = False
                break

    def listen_and_answer(self):
        """Listen for a question and provide an answer."""
        try:
            # Listen for question
            question = self.speech_service.listen_for_question()
            if not question:
                return
                
            logger.info(f"Question detected: {question}")
            
            # Search for answer
            answer = self.search_service.search_for_answer(question)
            
            # Provide answer
            if answer:
                self.tts_service.speak(answer)
            else:
                self.tts_service.speak("I'm sorry, I couldn't find an answer to that question.")
                
        except Exception as e:
            logger.error(f"Error in listen and answer: {e}")
            self.tts_service.speak("Sorry, there was an error processing your question.")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Shutting down...")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """Clean up resources."""
        try:
            self.stop_listening()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    bot = TriviaBot()
    bot.start() 