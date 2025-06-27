# API Configuration
COLLECTIBLES_URL = "https://bymykel.github.io/CSGO-API/api/en/collectibles.json"

# Directory Configuration
OUTPUT_FOLDER = "data/medals/"
DUMP_FOLDER = "data/responses/"

# Filter Configuration
COLLECTIBLE_TYPES = ["pick", "coin", "medal", "pin", "trophy", "badge", "pass", "stars"]

# Performance Configuration
MAX_WORKERS = 10  # Number of concurrent download threads
REQUEST_TIMEOUT = 30  # Request timeout in seconds
MAX_RETRIES = 3  # Maximum retry attempts for failed requests

# Image Processing Configuration
TARGET_WIDTH = 256  # Target image width in pixels
TARGET_HEIGHT = 192  # Target image height in pixels
