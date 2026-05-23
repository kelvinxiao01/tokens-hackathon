import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
NIMBLE_API_KEY = os.environ.get("NIMBLE_API_KEY", "")
SENSO_API_KEY = os.environ.get("SENSO_API_KEY", "")

NIMBLE_BASE_URL = "https://sdk.nimbleway.com/v1"
SENSO_BASE_URL = "https://apiv2.senso.ai/api/v1"

SENSO_INDEX_WAIT_SECONDS = 20

PROSPECTS_PER_RUN = 5

PLANNING_MODEL = "gpt-4.1"
RESEARCH_MODEL = "gpt-4.1-mini"
