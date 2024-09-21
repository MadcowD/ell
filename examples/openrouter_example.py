import logging
import ell
from ell.models.openrouter import get_openrouter_client

# Configure logging to display WARNING and above messages
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        client = get_openrouter_client()
        logger.info(f"Successfully obtained OpenRouter client: {type(client).__name__}")

        # Initialize ell with verbose logging (optional)
        # ell.init(verbose=True)

        @ell.simple(model="openai/gpt-3.5-turbo")  # Using an OpenRouter-supported model
        def hello(name: str) -> str:
            """You are a friendly AI assistant."""
            return f"Generate a warm greeting for {name}"

        greeting = hello("Sam Altman")
        print(f"Greeting: {greeting}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()