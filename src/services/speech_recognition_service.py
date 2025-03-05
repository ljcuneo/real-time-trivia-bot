import speech_recognition as sr
import whisper
import os
from loguru import logger
from typing import Optional

class SpeechRecognitionService:
    def __init__(self, engine: str = "google"):
        """Initialize speech recognition service.
        
        Args:
            engine (str): Speech recognition engine to use ('google' or 'whisper')
        """
        self.engine = engine.lower()
        self.recognizer = sr.Recognizer()
        self.whisper_model = None
        
        if self.engine == "whisper":
            logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
        
        # Adjust recognition parameters for faster response
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = 1000
        
    def listen_for_question(self) -> Optional[str]:
        """Listen for a question using the microphone.
        
        Returns:
            str: Recognized text or None if recognition failed
        """
        try:
            with sr.Microphone() as source:
                logger.info("Listening for question...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            if self.engine == "google":
                try:
                    text = self.recognizer.recognize_google(audio)
                    logger.info(f"Google recognized: {text}")
                    return text
                except sr.UnknownValueError:
                    logger.error("Google Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    logger.error(f"Could not request results from Google Speech Recognition service; {e}")
            
            elif self.engine == "whisper":
                try:
                    # Save audio to temporary file for Whisper
                    with open("temp_audio.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                    
                    # Use Whisper to transcribe
                    result = self.whisper_model.transcribe("temp_audio.wav")
                    text = result["text"].strip()
                    logger.info(f"Whisper recognized: {text}")
                    
                    # Clean up temporary file
                    os.remove("temp_audio.wav")
                    return text
                except Exception as e:
                    logger.error(f"Error with Whisper transcription: {e}")
                    if os.path.exists("temp_audio.wav"):
                        os.remove("temp_audio.wav")
            
        except Exception as e:
            logger.error(f"Error during speech recognition: {e}")
        
        return None 