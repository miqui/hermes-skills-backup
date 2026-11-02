# GitHub-safe naming gotcha for wrapper-managed repos

## Summary

When using `/Users/miqui/development/scripts/git-workflow.sh init`, a new local repository directory containing `+` can cause a partial-success failure:

- the wrapper creates the initial local commit
- the wrapper creates the GitHub repo using a normalized slug
- the wrapper then sets `origin` using the raw local directory name with `+`
- GitHub rejects that remote as an invalid repository name

## Observed shape

Example local directory:

```text
/Users/miqui/development/crossplane+api+eks+s3
```

Observed remote repo created successfully:

```text
https://github.com/miqui/crossplane-api-eks-s3
```

Observed invalid remote written locally:

```text
git@github.com:miqui/crossplane+api+eks+s3.git
```

Observed failure:

```text
fatal: remote error:
  is not a valid repository name
```

## Durable lesson

Before calling the wrapper for a brand-new repo, make the local directory name GitHub-safe and slug-stable. Prefer:

- lowercase letters
- digits
- hyphens

Avoid characters whose handling may differ between local directory names and GitHub repo creation, especially `+`.

## Safe pattern

Rename before first `init` run:

```text
crossplane+api+eks+s3  ->  crossplane-api-eks-s3
```

Then run the wrapper from the renamed directory.

## Why this belongs in the skill

This is not a transient network or auth issue. It is a repeatable workflow pitfall tied to the wrapper-managed publication path on this host, so future sessions benefit from checking naming before publish.
