# Script to categorize and label Hugo posts

import argparse
import pathlib
import yaml
import shutil
import random
import csv

from modules.post import Post
from modules.ai import AI

# ---------------------------------------------------------------------------------------------------------------------------------------------------
# Function to categorize a post using the AI engine

def categorize(p, ai, apply=False, debug=False):
    category, reason = ai.categorize(p)

    # Apply categorization changes if the apply flag is enabled
    if apply:
        # Assign post tags to the specified category
        p.metadata["tags"] = p.metadata.get("tags", [])
        p.metadata["tags"].append(category)
        p.save()

        # Move the post to its category-specific directory
        category_path = args.posts / category
        category_path.mkdir(parents=True, exist_ok=True)
        shutil.move(p.extra["path"], category_path)

    # Write debug information to CSV if enabled
    if debug:
        debug.writerow([ p.extra["id"], category, reason, p.body ])

# ---------------------------------------------------------------------------------------------------------------------------------------------------
# Main script to parse command-line arguments, initialize AI, and process posts.

# Argument parser
parser = argparse.ArgumentParser(description="Categorize Hugo posts")
parser.add_argument("posts", type=pathlib.Path, help="Hugo posts directory")
parser.add_argument("engine", type=argparse.FileType("r"), help="AI engine configuration")
parser.add_argument("prompt", type=argparse.FileType("r"), help="AI prompt definition")
parser.add_argument("--sample", type=int, help="Number of posts to sample")
parser.add_argument("--apply", action=argparse.BooleanOptionalAction, help="Apply categorization")
parser.add_argument("--csv", type=argparse.FileType("w"), help="CSV file output for debug")
args = parser.parse_args()

# Load all posts from the specified directory
posts = Post.load_all(args.posts)
print(f"{len(posts)} posts found")

# Randomly sample posts if the sample argument is provided
if args.sample:
    posts = random.sample(posts, args.sample)
    print(f"{len(posts)} posts sample")

# Load AI engine configuration
with args.engine as engine_config_file:
    engine_config = yaml.safe_load(engine_config_file)

# Load AI prompt definition
with args.prompt as prompt_config_file:
    prompt_def = yaml.safe_load(prompt_config_file)

# Initialize the AI engine using the configuration and prompt
ai = AI(engine_config, prompt_def)

# Initialize CSV writer for debugging if a CSV output is specified
if args.csv:
    debug = csv.writer(args.csv)
    debug.writerow(["id", "category", "reason", "body"])
else:
    debug = False

# Determine the processing function based on the prompt definition
process = locals()[prompt_def["type"]]  # Select the function by its name

# Process each post using the determined function
for p in posts:
    process(p, ai, apply=args.apply, debug=debug)

# Display statistics about the AI process
ai.stats()
