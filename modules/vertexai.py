"""Class for interacting with Google Vertex AI"""

from .engine import EngineAI

import vertexai
import time

from vertexai.generative_models import GenerativeModel
from google.api_core.exceptions import ResourceExhausted, TooManyRequests

class VertexAIEngine(EngineAI):
    def setup(self):
        """
        Initializes the Vertex AI model with the specified configuration.
        """
        vertexai.init(location=self.config["params"]["location"])
        self.model = GenerativeModel(self.config["params"]["model"])
        self.tokens = { "prompt": 0, "candidates": 0, "total": 0 }  # Tracks token usage

    def generate(self, prompt, config):
        """
        Generates content using the Vertex AI model with backoff handling.

        Args:
            prompt (str): Input prompt for content generation.
            config (dict): Configuration parameters for the AI generation.

        Returns:
            str: The generated content.
        """
        completed = False
        errors = 0
        delay = self.config["backoff"]["delay"]

        while not completed:
            try:
                response = self.model.generate_content(prompt, generation_config=config)
            except (ResourceExhausted, TooManyRequests):
                # Handle rate-limiting and retry with backoff
                errors += 1
                if errors == self.config["backoff"]["limit"]:
                    print(f"ResourceExhausted or TooManyRequests occurred {self.config["backoff"]["limit"]} times in a row. Exiting.")
                    exit()
                time.sleep(delay)
                delay *= self.config["backoff"]["rate"]
            else:
                completed = True

        # Update token usage statistics
        self.tokens["prompt"] += response.usage_metadata.prompt_token_count
        self.tokens["candidates"] += response.usage_metadata.candidates_token_count
        self.tokens["total"] += response.usage_metadata.total_token_count

        return response.text

    def stats(self):
        """
        Prints statistics about token usage during the session.
        """
        print(f"{self.tokens["prompt"]} prompt tokens")
        print(f"{self.tokens["candidates"]} candidates tokens")
        print(f"{self.tokens["total"]} total tokens")
