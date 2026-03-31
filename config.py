# =============================================================================
# config.py — Central Configuration for AI Research Assistant
# =============================================================================
# All settings are stored here. Change values here to affect the whole system.

# ── API Settings ──────────────────────────────────────────────────────────────
ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_API_KEY = ""          # Optional — leave blank for free tier
MAX_RESULTS_PER_SOURCE = 5            # How many papers to fetch per API
REQUEST_TIMEOUT = 15                  # Seconds before API request times out

# ── NLP Settings ──────────────────────────────────────────────────────────────
# Sentence categories the classifier will assign
SENTENCE_CATEGORIES = ["Claim", "Method", "Result", "Limitation"]

# Minimum sentence length to classify (shorter sentences are skipped)
MIN_SENTENCE_LENGTH = 10

# ── Agent Settings ─────────────────────────────────────────────────────────────
# How many top sentences each agent focuses on
DEFENDER_TOP_N = 5
CRITIC_TOP_N   = 5
JUDGE_TOP_N    = 3

# ── Model Settings ─────────────────────────────────────────────────────────────
# Sentence-transformer model used for semantic similarity
SENTENCE_TRANSFORMER_MODEL = "all-MiniLM-L6-v2"

# ── Streamlit UI Settings ─────────────────────────────────────────────────────
APP_TITLE   = "AI Research Assistant — Multi-Agent Debate"
APP_ICON    = "🔬"
THEME_COLOR = "#4F8BF9"
MAX_ABSTRACT_DISPLAY_CHARS = 600       # Truncate long abstracts in UI

# ── Data / Storage ─────────────────────────────────────────────────────────────
DATA_DIR   = "data"
MODELS_DIR = "models"
LOG_FILE   = "data/session_log.json"
