# Script to fix categories in Hugo posts based on a CSV file.

import argparse
import pathlib
import shutil
import csv
import os

from modules.post import Post

# Argument parser
parser = argparse.ArgumentParser(description="Categorize Hugo posts")
parser.add_argument("posts", type=pathlib.Path, help="Hugo posts directory with categories")
parser.add_argument("csv", type=argparse.FileType("r"), help="CSV file input with fixes")
parser.add_argument("--apply", action=argparse.BooleanOptionalAction, help="Apply fixes")
parser.add_argument("--verbose", action=argparse.BooleanOptionalAction, help="Print fixes")
args = parser.parse_args()

# Load fixes from the CSV file into a dictionary indexed by post IDs
with args.csv as csv_file:
    csv_reader = csv.DictReader(csv_file)
    fixes = { r["id"]: { "category": r["category"], "flags": r["flags"].split(",") } for r in csv_reader }

# Iterate through the directories in the posts folder
for obj in os.scandir(args.posts):
    if not obj.is_dir():
        continue  # Skip non-directory entries

    category_orig = obj.name  # Original category name
    posts = Post.load_all(obj.path)  # Load all posts in the current category
    print(f"{len(posts)} posts found in {category_orig}")

    drafts = 0  # Counter for posts marked as drafts
    fixed = 0   # Counter for posts with updated categories

    for p in posts:
        if p.extra["id"] not in fixes:
            continue  # Skip posts not listed in the fixes

        f = fixes[p.extra["id"]]  # Get fix details for the current post

        # Handle 'draft' flag if present
        if "draft" in f["flags"]:
            p.metadata["draft"] = True
            drafts += 1
            if args.verbose:
                print(f"   {p.extra["id"]}: draft is on")
            if args.apply:
                p.save()

        # Update category if it has changed
        category_fix = f["category"]
        if category_orig == category_fix:
            continue  # Skip if the category remains unchanged

        if args.verbose:
            print(f"   {p.extra["id"]}: {category_orig} -> {category_fix}")

        # Update the tag metadata and prepare to move the post
        p.metadata["tags"] = [ tag for tag in p.metadata.get("tags", []) if tag != category_orig ]
        p.metadata["tags"].append(category_fix)
        path_fix = args.posts / category_fix  # New category directory path
        fixed += 1

        if args.apply:
            p.save()
            path_fix.mkdir(parents=True, exist_ok=True)
            shutil.move(p.extra["path"], path_fix)

    # Print a summary of the fixes applied to the current category
    print(f"{drafts} drafts from {category_orig}")
    print(f"{fixed} posts fixed in {category_orig}")
