"""Class for managing Hugo posts and metadata"""

import yaml
import os

from dataclasses import dataclass, field

@dataclass
class Post:
    """
    Represents a Hugo post, including its filename, metadata, and content.

    Attributes:
        filename (str): Path to the markdown file.
        metadata (dict): Front matter metadata as a dictionary.
        body (str): Content of the markdown file.
        extra (dict): Additional attributes like file path, file type, and post ID.
    """
    filename: str  # Path to the markdown file
    metadata: dict  # Front matter metadata
    body: str  # Content of the markdown file
    extra: dict = field(default_factory=lambda: {
        "path": None,  # Full path to the post
        "single_file": None,  # Indicates if it's a standalone file or part of a folder
        "id": None,  # Unique identifier derived from the file or folder name
    })

    def save(self):
        """
        Saves the post's metadata and body back to its file.
        """
        content = [
            "---\n",
            yaml.dump(self.metadata, allow_unicode=True, width=1000),  # Convert metadata to YAML
            "---\n",
            self.body  # Add the post content
        ]
        with open(self.filename, "w") as md:
            md.writelines(content)

    @staticmethod
    def load(filename):
        """
        Loads a markdown file, parsing its metadata and content.

        Args:
            filename (str): Path to the markdown file.

        Returns:
            Post: An instance of the Post class.
        """
        basename = os.path.basename(filename)
        if basename == "index.md":
            # If the file is 'index.md', derive the post ID from its directory
            path = os.path.split(filename)[0]
            single_file = False
            id = os.path.basename(path)  # Use the folder name as the ID
        else:
            # For standalone files, use the filename without extension as the ID
            path = filename
            single_file = True
            id = os.path.splitext(basename)[0]

        # Read and split the markdown file into metadata and body
        with open(filename, "r") as md:
            content = md.read()
            parts = content.split("---\n")
            metadata = yaml.safe_load(parts[1])
            body = parts[2]

        return Post(
            filename=filename,
            metadata=metadata,
            body=body,
            extra={"path": path, "single_file": single_file, "id": id}
        )

    @staticmethod
    def load_all(path):
        """
        Loads all posts in a specified directory, supporting both folder-based and standalone markdown files.

        Args:
            path (str): Directory containing markdown files.

        Returns:
            list: A list of Post instances.
        """
        # If the path is a single file, load it directly
        if os.path.isfile(path):
            return [ Post.load(path) ]

        # Scan the directory and load all valid posts
        posts = []
        for obj in os.scandir(path):
            if obj.is_dir():
                # If the object is a directory, look for 'index.md'
                filename = os.path.join(obj.path, "index.md")
                if not os.path.isfile(filename):  # Skip if 'index.md' doesn't exist
                    continue
                post = Post.load(filename)
            elif obj.is_file() and os.path.splitext(obj.name)[1] == ".md":
                # If it's a standalone markdown file, load it
                post = Post.load(obj.path)
            else:
                # Skip other file types
                continue
            posts.append(post)
        return posts
