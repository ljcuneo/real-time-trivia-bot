import pyttsx3
from loguru import logger
import threading
import platform
import os

class TTSService:
    def __init__(self):
        """Initialize text-to-speech service."""
        self.engine = None
        self.init_engine()
    
    def init_engine(self):
        """Initialize the TTS engine."""
        try:
            if platform.system() == 'Darwin':
                # On macOS, we need to initialize differently
                import subprocess
                self.engine = 'macos'
            else:
                self.engine = pyttsx3.init()
                # Configure the engine
                self.engine.setProperty('rate', 175)  # Speed of speech
                self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
                
        except Exception as e:
            logger.error(f"Error initializing TTS engine: {e}")
            self.engine = None
    
    def speak(self, text: str, async_mode: bool = True):
        """Speak the given text.
        
        Args:
            text (str): The text to speak
            async_mode (bool): Whether to speak asynchronously
        """
        if not self.engine:
            logger.error("TTS engine not initialized")
            return
            
        try:
            if async_mode:
                # Run in a separate thread to avoid blocking
                thread = threading.Thread(target=self._speak_sync, args=(text,))
                thread.daemon = True
                thread.start()
            else:
                self._speak_sync(text)
                
        except Exception as e:
            logger.error(f"Error during text-to-speech: {e}")
    
    def _speak_sync(self, text: str):
        """Speak the text synchronously.
        
        Args:
            text (str): The text to speak
        """
        try:
            if self.engine == 'macos':
                # Use macOS's built-in say command
                os.system(f'say "{text}"')
            else:
                self.engine.say(text)
                self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error during synchronous speech: {e}")
            # Try to reinitialize the engine
            self.init_engine() 