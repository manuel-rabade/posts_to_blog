"""Class for interacting with AWS Bedrock AI"""

from .engine import EngineAI

import boto3
import time

class BedrockEngine(EngineAI):
    def setup(self):
        """
        Initializes the AWS Bedrock client with the specified configuration.
        """
        self.client = boto3.client(service_name="bedrock-runtime", region_name=self.config["params"]["region"])
        self.tokens = {"input": 0, "output": 0, "total": 0}  # Tracks token usage

    def generate(self, prompt, config):
        """
        Generates content using the AWS Bedrock service with backoff handling.

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
                response = self.client.converse(
                    modelId=self.config["params"]["model"],
                    messages=[{"role": "user", "content": [{"text": prompt}]}],
                    inferenceConfig=config
                )
            except self.client.exceptions.ThrottlingException:
                # Handle throttling with backoff retries
                errors += 1
                if errors == self.config["backoff"]["limit"]:
                    print(f"ThrottlingException occurred {self.config["backoff"]["limit"]} times in a row. Exiting.")
                    exit()
                time.sleep(delay)
                delay *= self.config["backoff"]["rate"]
            else:
                completed = True

        # Update token usage statistics
        self.tokens["input"] += response["usage"]["inputTokens"]
        self.tokens["output"] += response["usage"]["outputTokens"]
        self.tokens["total"] += response["usage"]["totalTokens"]

        return response["output"]["message"]["content"][0]["text"]

    def stats(self):
        """
        Prints statistics about token usage during the session.
        """
        print(f"{self.tokens["input"]} input tokens")
        print(f"{self.tokens["output"]} output tokens")
        print(f"{self.tokens["total"]} total tokens")
