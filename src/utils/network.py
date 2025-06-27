"""Network utilities for HTTP requests"""

from typing import Optional

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class NetworkClient:
    """HTTP client with retry strategy and connection pooling"""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """Initialize network client

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries

    def create_session(self) -> requests.Session:
        """Create a requests session with retry strategy and connection pooling

        Returns:
            Configured requests session
        """
        session = requests.Session()

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=20, pool_maxsize=20
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def download_with_retry(
        self, url: str, session: Optional[requests.Session] = None
    ) -> Optional[bytes]:
        """Download content with retry logic

        Args:
            url: URL to download from
            session: Optional existing session to reuse

        Returns:
            Downloaded content as bytes, or None if failed
        """
        if session is None:
            session = self.create_session()

        try:
            response = session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"Network error downloading from {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading from {url}: {e}")
            return None
