# Isolated-Worktree Verification Recipe (markdown/wiki content)

Worked example from a task that ingested a reviewed source into a Karpathy-style
LLM wiki via a temp worktree, without touching the repo's existing dirty checkout.

## SHA-256 over frontmatter body (not whole file)

Wiki raw-source frontmatter declares a `sha256:` computed over the body only —
everything after the closing `---` of the frontmatter, generally starting right
at the blank line that follows it (i.e. `lstrip("\n")` the remainder). Recompute
and compare rather than trusting the stored value:

```python
import hashlib
path = "raw/articles/<file>.md"
with open(path, "rb") as f:
    data = f.read()
lines = data.split(b"\n")
assert lines[0] == b"---"
end_idx = next(i for i in range(1, len(lines)) if lines[i] == b"---")
body = b"\n".join(lines[end_idx+1:]).lstrip(b"\n")
print(hashlib.sha256(body).hexdigest())
```

A quick shell version for a first pass (may not match if there's a leading
blank line difference — always cross-check with the Python version above
before declaring drift):

```bash
awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}' "$FILE" > /tmp/body.md
shasum -a 256 /tmp/body.md
```

## YAML frontmatter validation

```python
import yaml
with open(path) as f:
    content = f.read()
end = content.index("\n---\n", 4)
fm = yaml.safe_load(content[4:end])
```

Run this over every touched page, not just the new raw source — a hand-edited
concept page frontmatter is an easy place to introduce a YAML syntax error.

## Wikilink resolution

```python
import re, os
links = re.findall(r"\[\[([^\]]+)\]\]", text)
for link in links:
    slug = link.split("|")[0].strip()
    resolved = any(
        os.path.exists(os.path.join(wiki, sub, slug + ".md"))
        for sub in ["concepts", "entities", "comparisons", "queries"]
    )
```

## Secret scan on just the changed files

```bash
betterleaks dir --redact <file1> <file2> <file3>
```

Scope it to the explicit changed-file allowlist, not the whole repo — keeps
the check fast and the report focused on what's actually being published.

## Final diff shape check

Before staging, confirm the diff is exactly the intended allowlist:

```bash
git diff origin/main..HEAD --name-only
```

Should return only the files you intentionally touched — nothing from the
original dirty checkout, nothing incidental.
