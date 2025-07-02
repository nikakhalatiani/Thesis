from abc import ABC, abstractmethod
import requests
import subprocess
import time


class ModelService(ABC):
    """Abstract service for interacting with language models."""

    @abstractmethod
    def generate(self, prompt: str, options=None) -> str:
        """Generate text using the model service."""
        ...


class OllamaService(ModelService):
    """Service for interacting with Ollama API."""

    def __init__(self, model_name: str, api_url: str = "http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.api_url = api_url

    def generate(self, prompt: str, options=None) -> str:
        """Generate text using Ollama API."""
        default_options = {
            "temperature": 0.1,
            "top_p": 0.5,
            "num_predict": 500,
            "stop": ["\n\n", "Explanation:", "Analysis:"]
        }

        if options:
            default_options.update(options)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": default_options
        }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            raise RuntimeError(f"Ollama API request failed: {e}")


class ServiceHealthChecker(ABC):
    """Abstract health checker for external services."""

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if the service is healthy and accessible."""
        ...

    @abstractmethod
    def start_if_needed(self) -> None:
        """Start the service if it's not running."""
        ...


class OllamaHealthChecker(ServiceHealthChecker):
    """Health checker for Ollama service."""

    def __init__(self, health_check_url: str = "http://localhost:11434/api/tags"):
        self.health_check_url = health_check_url

    def is_healthy(self) -> bool:
        """Check if Ollama server is running and accessible."""
        try:
            response = requests.get(self.health_check_url, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def start_if_needed(self) -> None:
        """Attempt to start Ollama if it's not running."""
        if not self.is_healthy():
            try:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                # Give it time to start
                time.sleep(2)

                if not self.is_healthy():
                    raise RuntimeError("Failed to start Ollama service")
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                raise RuntimeError(f"Could not start Ollama: {e}")