from dotenv import load_dotenv
import os

DISCORDBOT_TOKEN = ""

def load_var_token():
    # Load local .env
    load_dotenv()

    try:
        DISCORDBOT_TOKEN = os.environ["DISCORDBOT_TOKEN"]
    except Exception as e:
        raise Exception(f'{e} - Could not retrieve bot token from environment!')

    return DISCORDBOT_TOKEN