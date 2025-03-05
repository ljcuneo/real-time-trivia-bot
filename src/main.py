import os
from dotenv import load_dotenv
from loguru import logger
import sys

from trivia_bot import TriviaBot

# Load environment variables from .env file
load_dotenv()

def setup_logging():
    """Configure logging settings."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <white>{message}</white>",
        level="INFO"
    )
    logger.add(
        "trivia_bot.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )

def main():
    """Main entry point for the Trivia Bot."""
    # Setup logging
    setup_logging()
    
    try:
        # Create and start the bot
        bot = TriviaBot()
        logger.info("Starting Trivia Bot...")
        bot.start()
    except KeyboardInterrupt:
        logger.info("Shutting down Trivia Bot...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Trivia Bot shutdown complete")

if __name__ == "__main__":
    main() 