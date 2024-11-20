"""Class for handling interaction with AI engines"""

import json
import time
import re

from dataclasses import dataclass

@dataclass
class ConfigAI():
    """Represents the configuration for an AI engine."""
    engine: dict  # AI engine configuration (e.g., model)
    prompt: dict  # AI prompt definition (e.g., type, components)

class AI():
    def __init__(self, engine_config, prompt_definition):
        """
        Initializes the AI class with the specified engine configuration and prompt definition.

        Args:
            engine_config (dict): Configuration for the AI engine.
            prompt_definition (dict): Definition of the AI prompt.
        """
        self.config = ConfigAI(engine=engine_config, prompt=prompt_definition)
        self.start = time.time()  # Start time for tracking elapsed time
        self.engine = self.factory()  # Instantiate the AI engine using the factory method
        self.engine.setup()  # Setup the AI engine

    def factory(self):
        """
        Factory method for creating an AI engine instance based on the configuration.

        Returns:
            An instance of the selected AI engine.

        Raises:
            Exception: If the engine type is unsupported.
        """
        if self.config.engine["type"] == "vertexai":
            from .vertexai import VertexAIEngine
            return VertexAIEngine(self.config.engine)
        elif self.config.engine["type"] == "bedrock":
            from .bedrock import BedrockEngine
            return BedrockEngine(self.config.engine)
        else:
            raise Exception(f"Unsupported AI engine: {self.config.engine["type"]}")

    def categorize(self, post):
        """
        Categorizes a given post using the configured AI engine and prompt.

        Args:
            post (Post): A post object containing its body and metadata.

        Returns:
            tuple: A tuple containing:
                - category (str): The assigned category for the post.
                - reason (str): The explanation for the assigned category.

        Raises:
            Exception: If the prompt type is invalid or an error occurs during categorization.
        """
        if self.config.prompt["type"] != "categorize":
            raise Exception(f"Invalid prompt type: {self.config.prompt["type"]}")

        # Prepare the prompt with the post body
        prompt = self.prepare(self.config.prompt["components"], post.body)
        res = self.engine.generate(prompt, self.config.prompt["params"])

        try:
            # If the response is enclosed in markdown syntax, remove the markdown delimiters
            md_match = re.search(r"```json\s*(.*?)\s*```", res.strip(), re.DOTALL)
            if md_match:
                res = md_match.group(1)
            # Parse the JSON result from the AI response
            data = json.loads(res)
            category = data["category"]
            reason = data["reason"]
        except Exception as e:
            # Handle exceptions and mark the category as `error`
            category = "error"
            reason = f"Exception: {repr(e)}\nResponse: {res}"

        # Validate the category and ensure it is part of the allowed categories
        if category not in self.config.prompt["categories"] or category == "error":
            print(f"Invalid category `{category}` for {post.extra["id"]}")
            category = "invalid"
            reason = f"Invalid category: {category}\nAI reason: {reason}"

        return category, reason

    def prepare(self, prompt, input):
        """
        Prepares the prompt by injecting the input and formatting it.

        Args:
            prompt (dict): The components of the prompt definition.
            input (str): The input text to be categorized.

        Returns:
            str: The formatted prompt ready to be processed by the AI engine.
        """
        prompt["input"] = input
        parts = [ f"<{k}>\n{v}\n</{k}>" for k, v in prompt.items() ]
        return "\n".join(parts)

    def stats(self):
        """
        Prints statistics about the AI engine and the elapsed time since initialization.
        """
        self.engine.stats()
        elapsed_minutes = int((time.time() - self.start) / 60)
        print(f"{elapsed_minutes} elapsed minutes")
