# Posts2Blog

Posts2Blog is a set of Python tools to convert social media posts into Hugo blog posts and organize them using AI.

## Examples

Install dependencies:

```bash
$ poetry install
```

Convert tweets into Hugo posts:

```bash
$ poetry run python tweets_to_hugo.py archive/ posts/ --after 2020-01-01 --author "Your Name" --timezone "Mexico/General" \
    --unsafe --csv threads.csv --username yourusername --tag twitter --origin "Original Tweet"
```

Categorize posts using the Gemini Pro model deployed on Google Vertex AI:

```bash
$ poetry run python curate_posts.py posts/ engines/vertexai.yaml prompts/categorize.yaml --csv categories-gemini-pro.csv --apply
```

Categorize posts using the Claude Sonnet model deployed on AWS Bedrock:

```bash
$ poetry run python curate_posts.py posts/ engines/bedrock.yaml prompts/categorize.yaml --csv categories-claude-sonnet.csv --apply
```

Applies category fixes and manages drafts based on a CSV file:

```bash
$ poetry run python fix_categories.py posts/ categories-fixes.csv --apply
```

Label posts using the Gemini Pro model deployed on Google Vertex AI:

```bash
$ poetry run python curate_posts.py posts/cultura/ engines/vertexai.yaml prompts/label-cultura.yaml --csv labels-cultura-gemini-pro.csv --apply
```

Label posts using the Claude Sonnet model deployed on AWS Bedrock:

```bash
$ poetry run python curate_posts.py posts/cultura/ engines/bedrock.yaml prompts/label-cultura.yaml --csv labels-cultura-claude-sonnet.csv --apply
```

## TODO

- [ ] Enhace README
- [ ] Break down `tweets_to_hugo.py`
- [ ] Retrofit Post class in `tweets_to_hugo.py`
