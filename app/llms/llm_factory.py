from app.llms.gemini_chat_client import default_chat_client


def get_default_chat_client():
    """Return the Gemini chat client used across the assistant.

    This project only integrates Gemini (via langchain-google-genai) — there
    is no multi-provider fallback in scope.

    Returns:
        ChatGoogleGenerativeAI instance.
    """
    return default_chat_client
