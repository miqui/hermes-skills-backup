# Opinionated AWS Lambda Layout

Use this as a starting point for Python Lambda projects when the repo does not already define a different structure.

```text
project/
  handler.py
  services/
    business_logic.py
  models/
    event_models.py
  tests/
    test_handler.py
  pyproject.toml
  template.yaml
  .env.example
  README.md
```

## Layout notes

- `handler.py` should stay thin: parse input, call services, shape the response
- `services/` should contain testable business logic
- `models/` can hold event/response structures or validation helpers
- `template.yaml` or equivalent infra file should document deploy-time wiring

## Handler pattern

```python
from botocore.exceptions import ClientError


def handler(event: dict, context: object) -> dict:
    try:
        result = process_event(event)
        return {"statusCode": 200, "body": result}
    except ClientError:
        return {"statusCode": 500, "body": "Internal error"}


def process_event(event: dict) -> str:
    ...
```

## Testing baseline

- one direct handler test
- one service-level test for core business behavior
- add regression tests for fixed bugs

## Common mistakes

- putting all logic directly in the handler
- mixing parsing, business logic, and serialization in one function
- returning inconsistent response shapes
- skipping explicit handling for AWS client failures
