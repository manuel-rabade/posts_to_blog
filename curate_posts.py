# Script to categorize and label Hugo posts

import argparse
import pathlib
import yaml
import shutil
import random
import csv

from modules.post import Post
from modules.ai import AI

# Categorize a post using AI
def categorize(p, ai, apply=False, debug=False):
    category, reason = ai.categorize(p)

    if apply:
        # Update tags and move post to category-specific folder
        p.metadata["tags"] = p.metadata.get("tags", [])
        p.metadata["tags"].append(category)
        p.save()
        category_path = args.posts / category
        category_path.mkdir(parents=True, exist_ok=True)
        shutil.move(p.extra["path"], category_path)

    if debug:
        debug.writerow([ p.extra["id"], category, reason, p.body ])

# Label a post using AI
def label(p, ai, apply=False, debug=False):
    metadata, error = ai.label(p)

    if apply and not error:
        # Save metadata and rename post
        p.metadata = metadata
        p.save()
        old_slug = p.extra["id"].split("-")
        new_path = str(p.extra["path"]).replace(old_slug[1], p.metadata["slug"])
        shutil.move(p.extra["path"], new_path)

    if debug:
        debug.writerow([ p.extra["id"], p.metadata["slug"], p.metadata["title"], p.metadata["summary"], ", ".join(p.metadata["tags"]), p.body ])

# ---------------------------------------------------------------------------------------------------------------------------------------------------

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Curate Hugo posts")
parser.add_argument("posts", type=pathlib.Path, help="Hugo posts directory")
parser.add_argument("engine", type=argparse.FileType("r"), help="AI engine configuration file")
parser.add_argument("prompt", type=argparse.FileType("r"), help="AI prompt definition file")
parser.add_argument("--sample", type=int, help="Number of posts to sample")
parser.add_argument("--apply", action=argparse.BooleanOptionalAction, help="Apply changes")
parser.add_argument("--csv", type=argparse.FileType("w"), help="CSV file for debug output")
args = parser.parse_args()

# Load posts
posts = Post.load_all(args.posts)
print(f"{len(posts)} posts found")

# Sample posts if specified
if args.sample:
    posts = random.sample(posts, args.sample)
    print(f"{len(posts)} posts sampled")

# Load AI engine and prompt configuration
with args.engine as engine_config_file:
    engine_config = yaml.safe_load(engine_config_file)

with args.prompt as prompt_config_file:
    prompt_def = yaml.safe_load(prompt_config_file)

# Initialize AI engine
ai = AI(engine_config, prompt_def)

# Set up CSV debug writer if specified
if args.csv:
    debug = csv.writer(args.csv)
    debug.writerow(["id"])
else:
    debug = False

# Determine the processing function based on the prompt definition
process = locals()[prompt_def["type"]]

# Process each post using the determined function
for p in posts:
    process(p, ai, apply=args.apply, debug=debug)

# Show AI statistics
ai.stats()
