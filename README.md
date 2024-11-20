# Posts2Blog

Posts2Blog is a set of Python tools to convert social media posts into Hugo blog posts and organize them using AI.

## Examples

Convert tweets into Hugo posts:

```bash
$ poetry run python tweets_to_hugo.py archive/ ../homepage/content/posts/ \
    --after 2020-01-01 --author "Manuel Rábade" --tag twitter \
    --csv threads.csv --username manuelrabade \
    --unsafe \
    --origin "Tweet original"
```

Categorize posts using the Claude Sonnet model deployed on AWS Bedrock:

```bash
$ poetry run python categorize_posts.py ../homepage/content/posts/ engines/bedrock.yaml prompts/categorize.yaml \
    --csv debug/categories-claude-sonnet.csv \
    --apply
263 posts found
178706 input tokens
31422 output tokens
210128 total tokens
30 elapsed minutes
```

Categorize posts using the Gemini Pro model deployed on Google Vertex AI:

```bash
$ poetry run python categorize_posts.py ../homepage/content/posts/ engines/vertexai.yaml prompts/categorize.yaml \
    --csv debug/categories-gemini-pro.csv \
    --apply
263 posts found
Invalid category error for 20200301-1234225309655822336
144629 prompt tokens
20425 candidates tokens
165054 total tokens
40 elapsed minutes
```

## TODO

- [ ] Retrofit Post class in `tweets_to_hugo.py`
- [ ] Break down `tweets_to_hugo.py`
