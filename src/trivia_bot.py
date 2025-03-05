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
        """Initialize the Trivia Bot with all required services."""
        # Load configuration
        self.speech_engine = os.getenv('SPEECH_RECOGNITION_ENGINE', 'google').lower()
        
        # Initialize services
        self.speech_service = SpeechRecognitionService(self.speech_engine)
        self.search_service = SearchService()
        self.tts_service = TTSService()
        
        # Set up thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Initialize state
        self.is_listening = False
        self.last_question = None
        self.last_answer = None
        self.running = True
        
        logger.info("Trivia Bot initialized successfully")
    
    def start(self):
        """Start the Trivia Bot and listen for hotkey."""
        try:
            # Set up signal handler for clean exit
            signal.signal(signal.SIGINT, self.signal_handler)
            
            logger.info("Starting Trivia Bot...")
            logger.info("Press Enter to start/stop listening")
            logger.info("Press Ctrl+C to exit")
            
            # Start input thread
            input_thread = threading.Thread(target=self.input_loop)
            input_thread.daemon = True
            input_thread.start()
            
            # Main loop
            while self.running:
                time.sleep(0.1)  # Reduce CPU usage
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()
    
    def input_loop(self):
        """Handle user input in a separate thread."""
        while self.running:
            try:
                input()  # Wait for Enter key
                self.toggle_listening()
            except EOFError:
                continue
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C signal."""
        logger.info("Shutting down...")
        self.running = False
    
    def toggle_listening(self):
        """Toggle the listening state."""
        self.is_listening = not self.is_listening
        if self.is_listening:
            logger.info("Listening activated")
            self.listen_and_answer()
        else:
            logger.info("Listening deactivated")
    
    def listen_and_answer(self):
        """Listen for a question and find its answer."""
        try:
            # Start timing
            start_time = time.time()
            
            # Listen for question
            question = self.speech_service.listen_for_question()
            if not question:
                logger.warning("No question detected")
                return
            
            self.last_question = question
            logger.info(f"Question detected: {question}")
            
            # Search for answer in parallel with TTS confirmation
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Start the search
                search_future = executor.submit(self.search_service.search_for_answer, question)
                
                # Confirm question was heard
                self.tts_service.speak("Searching for answer to: " + question)
                
                # Wait for search to complete
                answer = search_future.result(timeout=8)  # Ensure we stay within 10-second limit
            
            if not answer:
                self.tts_service.speak("Sorry, I couldn't find an answer to that question.")
                return
            
            # Store and speak the answer
            self.last_answer = answer
            self.tts_service.speak(answer)
            
            # Log timing
            elapsed_time = time.time() - start_time
            logger.info(f"Total response time: {elapsed_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error in listen_and_answer: {e}")
            self.tts_service.speak("Sorry, there was an error processing your question.")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.running = False
            self.executor.shutdown(wait=False)
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 