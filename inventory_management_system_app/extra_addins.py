
import requests
import random

def get_zen_quote():
    """
    Fetches a random motivational quote from the ZenQuotes API.

    Returns:
        str: A formatted quote like — "Be yourself; everyone else is already taken. — Oscar Wilde"
    """
    api_url = "https://zenquotes.io/api/random"
    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        quote = f"“{data[0]['q']}” — {data[0]['a']}"
        return quote
    except requests.exceptions.RequestException as e:
        print(f"Error fetching quote: {e}")
        # fallback quotes in case API fails
        fallback_quotes = [
            "“Act as if what you do makes a difference. It does.” — William James",
            "“Success is not how high you have climbed, but how you make a positive difference to the world.” — Roy T. Bennett",
            "“You do not find the happy life. You make it.” — Camilla Eyring Kimball",
        ]
        return random.choice(fallback_quotes)





