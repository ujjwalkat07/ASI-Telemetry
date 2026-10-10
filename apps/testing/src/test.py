
from asi_tracer import instrument_llm_provider,instrument_gemini
import os
from dotenv import load_dotenv

# Load environment variables before initializing tracing
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

from asi_tracer import traceable, instrument_gemini
from google import genai

# Initialize the Google Gemini client
client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)
instrument_gemini(client)


@traceable(name="format_prompt")
def format_prompt(subject: str) -> str:
    """Build the prompt for the LLM."""
    return f"Explain {subject} in exactly 1 concise sentence."


@traceable(name="invoke_llm", run_type="llm")
def invoke_llm(messages: str) -> str:
    """Send the prompt to Google Gemini."""
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=messages,
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text


@traceable(name="parse_output")
def parse_output(response: str) -> str:
    """Clean the LLM response."""
    return response.strip()


@traceable(name="run_pipeline")
def run_pipeline() -> str:
    messages = format_prompt("How does an API work?")
    response = invoke_llm(messages)
    result = parse_output(response)

    return result


if __name__ == "__main__":
    try:
        result = run_pipeline()
        print("\n--- Final Output ---")
        print(result)
    except Exception as error:
        print(f"Pipeline failed: {error}")
