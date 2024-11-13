import argparse
import pathlib
import json
import pytz
import csv
import dateutil.parser
import datetime
import os
import urllib.parse
import re
import shutil

# ---------------------------------------------------------------------------------------------------------------------------------------------------
# Dataclasses for storing a tweet along with its associated URLs and media

from dataclasses import dataclass, field

@dataclass
class TweetUrl:
    """Represents a shortened URL within a tweet."""
    short: str
    display: str
    expanded: str

@dataclass
class TweetMedia:
    """Represents a media item associated with a tweet."""
    url: str
    media: str
    type: str
    tweet_id: int

@dataclass
class Tweet:
    """Represents a tweet, including its attributes, associated content, and reply IDs."""
    id: int
    text: str
    created: datetime.datetime
    reply: int
    rt: bool
    mention: bool
    urls: list[TweetUrl]
    media: list[TweetMedia]
    replies: list['Tweet'] = field(default_factory=list)

# ---------------------------------------------------------------------------------------------------------------------------------------------------
# Functions for loading and parsing the Twitter archive

def load_tweets(archive):
    """
    Loads JSON data from the `data/tweets.js` file within a Twitter archive.

    Args:
        archive (pathlib.Path): Path to the directory containing the Twitter archive.

    Returns:
        list: A list of tweets represented as dictionaries.
    """
    tweets_js = archive / "data/tweets.js"
    with open(tweets_js, "r") as file:
        lines = file.readlines()
    # Remove the JavaScript variable assignment at the beginning of the file
    lines[0] = lines[0].replace("window.YTD.tweets.part0 = ", "")
    data = "".join(lines)
    return json.loads(data)

def parse_tweet(t):
    """
    Parses tweet data and returns an instance of the Tweet dataclass.

    Args:
        t (dict): Dictionary containing tweet data.

    Returns:
        Tweet: An instance of the Tweet dataclass with extracted tweet attributes.
    """
    # Extract URLs from the tweet
    urls = [ TweetUrl(short=u["url"], display=u["display_url"], expanded=u["expanded_url"]) for u in t["tweet"]["entities"]["urls"] ]
    # Handle extended media entities (photos, videos, GIFs)
    extended_entities = t["tweet"].get("extended_entities", {}).get("media", [])
    media = []
    for m in extended_entities:
        if m["type"] == "photo":
            # Add photo media
            media.append(TweetMedia(url=m["url"], media=m["media_url"], type=m["type"], tweet_id=int(t["tweet"]["id"])))
        elif m["type"] in ["video", "animated_gif"]:
            # Select the video with the highest bitrate
            videos = {v["bitrate"]: v["url"] for v in m["video_info"]["variants"] if "bitrate" in v}
            bitrate = sorted(videos.keys())[0]
            media.append(TweetMedia(url=m["url"], media=videos[bitrate], type=m["type"], tweet_id=int(t["tweet"]["id"])))
        else:
            raise Exception("Unsupported media type")

    return Tweet(
        id=int(t["tweet"]["id"]),
        text=t["tweet"]["full_text"],
        created=dateutil.parser.parse(t["tweet"]["created_at"]),
        reply=int(t["tweet"].get("in_reply_to_status_id_str", 0)),
        rt=t["tweet"]["full_text"].startswith("RT @"),
        mention=t["tweet"]["full_text"].startswith("@"),
        urls=urls,
        media=media
    )

# ---------------------------------------------------------------------------------------------------------------------------------------------------
# Function to filter tweets into threads and replies

def build_threads(tweets, after=False, before=False, timezone=None):
    """
    Organizes tweets into threads and counts replies, with optional timezone adjustment and date filtering.

    Args:
        tweets (list): A list of Tweet objects to be organized.
        after (str, optional): Include only tweets created after this date. Defaults to False.
        before (str, optional): Include only tweets created before this date. Defaults to False.
        timezone (str, optional): Timezone for adjusting tweet timestamps. Defaults to None.

    Returns:
        tuple: A tuple containing:
            - dict: A dictionary of Tweet objects representing threads, where keys are the IDs of the main tweets in each thread.
            - int: Total count of replies across all threads.
    """
    utc = pytz.UTC
    if after:
        date_after = utc.localize(dateutil.parser.parse(after))
    if before:
        date_before = utc.localize(dateutil.parser.parse(before))
    if timezone:
        local_tz = pytz.timezone(timezone)

    threads = {}
    replies = {}
    for i in tweets:
        t = parse_tweet(i)
        # Adjust tweet time to the specified timezone
        if timezone:
            t.created = t.created.replace(tzinfo=pytz.utc).astimezone(local_tz)
        # Filter by date
        if after and t.created <= date_after:
            continue
        if before and t.created >= date_before:
            continue
        # Ignore RTs
        if t.rt:
            continue
        # Ignore mentions that are not a reply in a thread
        if t.mention and not t.reply:
            continue
        # Store threads and replies
        if not t.reply:
            threads[t.id] = t
        else:
            replies[t.reply] = t

    # Store replies in threads
    for id in threads.keys():
        if id not in replies:
            continue
        head = threads[id]
        reply = replies[id]
        head.replies.append(reply)
        while reply.id in replies:
            reply = replies[reply.id]
            head.replies.append(reply)

    return threads, len(replies)

# ---------------------------------------------------------------------------------------------------------------------------------------------------
# Functions for building a Hugo post and debugging threads

def build_post(t, author=None, tag=None, unsafe=False):
    """
    Builds a Hugo post from a tweet thread, returning the markdown content and a media catalog.

    Args:
        t (Tweet): The main Tweet object representing the thread.
        author (str, optional): Author name to include in the post metadata. Defaults to None.
        tag (str, optional): Tag to include in the post metadata. Defaults to None.
        unsafe (bool): If True, use HTML video tag for videos. Requires setting `unsafe` to True in Hugo markup configuration. Defaults to False.

    Returns:
        tuple: A tuple containing:
            - str: The post content in Markdown format.
            - dict: A media catalog where each key is the original filename and each value is the new filename.
    """
    md = []

    # Front matter metadata for the Hugo post
    md.append("---")
    md.append("title: " + str(t.id))
    md.append("date: " + t.created.isoformat())
    if author:
        md.append("author: " + author)
    if tag:
        md.append("tags: [\"" + tag + "\"]")
    md.append("---")

    # Initialize thread text with URLs and media references
    text = t.text + "\n"
    urls = t.urls
    media = t.media

    # Add replies text, URLs and media
    for r in t.replies:
        # Remove mentions at the start of replies
        if r.text.startswith("@"):
            words = r.text.split()
            new_start = next((i for i, w in enumerate(words) if not w.startswith("@")), len(words))
            r.text = " ".join(words[new_start:])

        # Join paragraphs if one ends and the next begins with "..."
        if text.endswith("...\n") and r.text.startswith("..."):
            text = text.rstrip("...\n") + r.text.lstrip("...") + "\n"
        else:
            text += "\n" + r.text + "\n"
        urls.extend(r.urls)
        media.extend(r.media)

    # Replace shortened URLs in text with Markdown links
    for u in urls:
        text = text.replace(u.short, "[{0}]({1})".format(u.display, u.expanded))

    # Convert mentions to profile links
    text = re.sub("@([a-zA-Z0-9_]{1,15})", "[@\\1](http://x.com/\\1)", text)

    # Group media files by URL
    media_urls = {}
    for m in media:
        media_urls.setdefault(m.url, []).append(m)

    # Replace media URLs in text and build media files catalog
    media_files = {}
    media_count = 1
    for url, media_list in media_urls.items():
        tags = []
        for m in media_list:
            orig_media = f"{m.tweet_id}-{os.path.basename(urllib.parse.urlparse(m.media).path)}"
            new_media = f"{media_count}.{os.path.splitext(orig_media)[1][1:]}"
            media_files[orig_media] = new_media
            if m.type in ["video", "animated_gif"]:
                if unsafe:
                    tags.append(f"<video src='{new_media}' controls></video>")
                else:
                    tags.append(f"[Video]({new_media})")
            else:
                tags.append(f"[![]({new_media})]({new_media})")
            media_count += 1
        text = text.replace(url, "\n\n" + "\n".join(tags))

    # Append thread text to markdown and return post body plus media files catalog
    md.append(text)
    return "\n".join(md), media_files

def debug_thread(t):
    """
    Concatenates text from a tweet and its replies for debugging purposes.

    Args:
        t (Tweet): Tweet object to debug.

    Returns:
        str: Complete concatenated text of the thread.
    """
    text = t.text + "\n"
    for r in t.replies:
        text += "\n" + r.text + "\n"
    return text

# ---------------------------------------------------------------------------------------------------------------------------------------------------
# Main script to parse command-line arguments, load tweets, and build threads and posts.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Converts a Twitter archive into Hugo posts")
    parser.add_argument("archive", type=pathlib.Path, help="Twitter archive directory")
    parser.add_argument("output", type=pathlib.Path, help="Output directory for generated files")
    parser.add_argument("--after", type=str, help="Include only tweets created after this date")
    parser.add_argument("--before", type=str, help="Include only tweets created before this date")
    parser.add_argument("--timezone", type=str, help="Specify local timezone for tweets")
    parser.add_argument("--author", type=str, help="Author metadata for markdown files")
    parser.add_argument("--tag", type=str, help="Tag metadata for markdown files")
    parser.add_argument("--unsafe", action=argparse.BooleanOptionalAction, help="Use HTML video tag, requires enabling `unsafe` in Hugo markup configuration")
    parser.add_argument("--csv", type=argparse.FileType("w"), help="CSV file output for threads")
    parser.add_argument("--username", type=str, help="Twitter username for CSV links")
    args = parser.parse_args()

    # Load tweets from the specified archive
    tweets = load_tweets(args.archive)
    print(f"{len(tweets)} tweets loaded")

    # Organize tweets into threads and replies with optional filters
    threads, replies_count = build_threads(tweets, after=args.after, before=args.before, timezone=args.timezone)
    print(f"{len(threads)} threads found")
    print(f"{replies_count} replies found")

    # Generate Hugo markdown files and copy media files from the archive
    args.output.mkdir(parents=True, exist_ok=True)
    for id in sorted(threads.keys(), reverse=True):
        t = threads[id]
        body, media = build_post(t, author=args.author, tag=args.tag, unsafe=args.unsafe)
        if media:
            # If media is present, create a directory to store media and markdown files
            post_dir = args.output / f"{t.created.strftime('%Y%m%d')}-{t.id}"
            post_dir.mkdir(parents=True, exist_ok=True)
            # Copy each media file to the output directory
            for m in media.keys():
                shutil.copy(args.archive / "data/tweets_media" / m, post_dir / media[m])
            post_md = post_dir / "index.md"
        else:
            # Create a standalone markdown file if no media is present
            post_md = args.output / f"{t.created.strftime('%Y%m%d')}-{t.id}.md"
        with open(post_md, "w") as md:
            md.write(body)

    # Generate a CSV file if requested
    if args.csv:
        with args.csv as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["id", "date", "time", "replies", "media", "link", "body"])
            for id in sorted(threads.keys(), reverse=True):
                t = threads[id]
                row = [
                    id,
                    t.created.strftime("%Y-%b-%d"),
                    t.created.strftime("%H:%M"),
                    len(t.replies),
                    len(t.media),
                    f"https://x.com/{args.username}/status/{t.id}",
                    debug_thread(t)
                ]
                csv_writer.writerow(row)
