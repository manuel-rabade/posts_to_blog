"""Class for managing Hugo posts and metadata"""

import yaml
import os

from dataclasses import dataclass, field

@dataclass
class Post:
    filename: str  # Path to the markdown file
    metadata: dict  # Front matter metadata as a dictionary
    body: str  # Content of the markdown file
    extra: dict = field(default_factory=lambda: {
        "path": None,
        "single_file": None,
        "id": None,
    })  # Additional attributes

    def save(self):
        """
        Saves the post's metadata and body back to its file.
        """
        content = ["---\n", yaml.dump(self.metadata, allow_unicode=True), "---\n", self.body]
        with open(self.filename, "w") as md:
            md.writelines(content)

    @staticmethod
    def load(filename):
        """
        Loads a markdown file and parses its metadata and body.

        Args:
            filename (str): Path to the markdown file.

        Returns:
            Post: An instance of the Post class.
        """
        basename = os.path.basename(filename)
        if basename == "index.md":
            path = os.path.split(filename)[0]
            single_file = False
            id = os.path.basename(path)
        else:
            path = filename
            single_file = True
            id = os.path.splitext(basename)[0]

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
        Loads all posts in a directory.

        Args:
            path (str): Directory containing markdown files.

        Returns:
            list: A list of Post instances.
        """
        posts = []
        for obj in os.scandir(path):
            if obj.is_dir():
                filename = os.path.join(obj.path, "index.md")
                if not os.path.isfile(filename):
                    continue
                post = Post.load(filename)
            elif obj.is_file() and os.path.splitext(obj.name)[1] == ".md":
                post = Post.load(obj.path)
            posts.append(post)
        return posts
