import argparse
import pathlib
import yaml
import shutil
import random
import csv

from modules.post import Post
from modules.ai import AI

# Script for categorizing Hugo posts

if __name__ == "__main__":

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

    # Sample posts if the sample argument is provided
    if args.sample:
        posts = random.sample(posts, args.sample)
        print(f"{len(posts)} posts sample")

    # Load AI engine configuration
    with args.engine as engine_config_file:
       engine_config = yaml.safe_load(engine_config_file)

    # Load AI prompt definition
    with args.prompt as prompt_config_file:
       prompt_def = yaml.safe_load(prompt_config_file)

    # Initialize AI engine with the loaded configuration and prompt
    ai = AI(engine_config, prompt_def)

    # Setup CSV debug writer if debug output is enabled
    if args.csv:
        debug = csv.writer(args.csv)
        debug.writerow(["id", "category", "reason", "body"])

    # Process each post for categorization
    for p in posts:
        # Categorize the post using the AI engine
        category, reason = ai.categorize(p)

        # Apply categorization changes if the apply flag is enabled
        if args.apply:
            # Update the post metadata with the assigned category
            p.metadata["categories"] = [ category ]
            p.save()

            # Move the post to its category-specific directory
            category_path = args.posts / category
            category_path.mkdir(parents=True, exist_ok=True)
            shutil.move(p.extra["path"], category_path)

        # Write debug information to CSV if enabled
        if args.csv:
            debug.writerow([ p.extra["id"], category, reason, p.body ])

    # Display statistics about the categorization process
    ai.stats()
