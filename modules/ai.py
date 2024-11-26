"""Class for handling interaction with AI engines"""

import json
import time
import re

from dataclasses import dataclass

@dataclass
class ConfigAI():
    """Represents the configuration for an AI engine."""
    engine: dict  # AI engine configuration (e.g., model, zone)
    prompt: dict  # AI prompt definition (e.g., type, components, parameters)

class AI():
    def __init__(self, engine_config, prompt_definition):
        """
        Initializes the AI class with the specified engine configuration and prompt definition.

        Args:
            engine_config (dict): Configuration for the AI engine.
            prompt_definition (dict): Definition of the AI prompt.
        """
        self.config = ConfigAI(engine=engine_config, prompt=prompt_definition)
        self.start = time.time()  # Track initialization time
        self.engine = self.factory()  # Instantiate the appropriate AI engine
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
            # Handle AI response enclosed in markdown code blocks
            md_match = re.search(r"```json\s*(.*?)\s*```", res.strip(), re.DOTALL)
            if md_match:
                res = md_match.group(1)

            # Parse JSON response into category and reason
            data = json.loads(res)
            category = data["category"]
            reason = data["reason"]
        except Exception as e:
            # Handle exceptions and assign `error` as category
            category = "error"
            reason = f"Exception: {repr(e)}\nResponse: {res}"
            return category, reason

        # Validate the category
        if category not in self.config.prompt["categories"] or category == "error":
            print(f"Invalid category `{category}` for {post.extra["id"]}")
            category = "invalid"
            reason = f"Invalid category: {category}\nAI reason: {reason}"

        return category, reason

    def label(self, post):
        """
        Labels a given post using the configured AI engine and prompt.

        Args:
            post (Post): A post object containing its body and metadata.

        Returns:
            tuple:
                - metadata (dict): Updated metadata with title, summary, slug, and tags.
                - error (bool): False if labeling succeeded, True if an error occurred.

        Raises:
            Exception: If the prompt type is invalid or an error occurs during labeling.
        """
        if self.config.prompt["type"] != "label":
            raise Exception(f"Invalid prompt type: {self.config.prompt["type"]}")

        # Prepare the prompt with the post body and replace placeholders with specific values for the prompt
        error = False
        replace = { "%TAGS%": self.config.prompt["tags"], "%SUBJECTS%": self.config.prompt["subjects"] }
        prompt = self.prepare(self.config.prompt["components"], post.body, replace=replace)
        res = self.engine.generate(prompt, self.config.prompt["params"])

        try:
            # Handle AI response enclosed in markdown code blocks
            md_match = re.search(r"```json\s*(.*?)\s*```", res.strip(), re.DOTALL)
            if md_match:
                res = md_match.group(1)

            # Parse response into metadata fields
            data = json.loads(res)
            post.metadata["title"] = data["title"]
            post.metadata["summary"] = data["summary"]
            post.metadata["slug"] = data["slug"]
            post.metadata["tags"] = post.metadata.get("tags", [])
            new_tags = data["tags"].split(",") + data["subjects"].split(",")
            new_tags = [ t.strip() for t in new_tags ]
            post.metadata["tags"].extend(t for t in set(new_tags) if t not in post.metadata["tags"])
        except Exception as e:
            # Handle exceptions and mark metadata as `error`
            print(f"Exception for {post.extra["id"]}: {repr(e)}\nResponse: {res}")
            for k in [ "title", "summary", "slug", "tags" ]:
                post.metadata[k] = f"error ({post.metadata.get(k, "undefined")})"
            error = True
            return post.metadata, error

        # Validate the slug format
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", post.metadata["slug"]):
            print(f"Invalid slug `{post.metadata["slug"]}` for {post.extra["id"]}")
            post.metadata["slug"] = f"invalid ({post.metadata["slug"]})"
            error = True

        # Ensure at least one required tag is present in the tags list
        if not set(post.metadata["tags"]) & set(self.config.prompt["tags"]):
            print(f"Missing required tag in `{data["tags"]}` for {post.extra["id"]}")

        return post.metadata, error

    def prepare(self, prompt, input, replace=None):
        """
        Prepares the prompt by injecting the input and formatting it.

        Args:
            prompt (dict): The components of the prompt definition.
            input (str): The input text to be categorized or labeled.
            replace (dict, optional): Key-Value pairs to replace in the prompt.

        Returns:
            str: The formatted prompt ready for the AI engine.
        """
        prompt["input"] = input
        parts = [ f"<{k}>\n{v}\n</{k}>" for k, v in prompt.items() ]
        res = "\n".join(parts)

        if not isinstance(replace, dict):
            return res

        for key in replace.keys():
            if isinstance(replace[key], list):
                res = res.replace(key, ", ".join(replace[key]))
            else:
                res = res.replace(key, replace[key])
        return res

    def stats(self):
        """
        Prints statistics about the AI engine and the elapsed time since initialization.
        """
        self.engine.stats()
        elapsed_minutes = int((time.time() - self.start) / 60)
        print(f"{elapsed_minutes} elapsed minutes")
