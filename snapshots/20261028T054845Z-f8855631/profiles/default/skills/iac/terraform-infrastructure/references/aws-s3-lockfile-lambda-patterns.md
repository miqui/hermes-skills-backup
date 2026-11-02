# AWS: S3 Lockfile State + Lambda/API GW Patterns

Distilled from a session scaffolding a production Terraform repo with S3 native
lock files, Node.js 22 Lambda, and API Gateway HTTP API.

---

## S3 Native State Locking (Terraform ≥ 1.10)

Use `use_lockfile = true` in the S3 backend. No DynamoDB table required.

```hcl
terraform {
  backend "s3" {
    # Supplied via -backend-config flag or *.s3.tfbackend file
    # bucket       = "..."   # do NOT hardcode here
    # key          = "app/dev/terraform.tfstate"
    # region       = "us-east-1"
    # encrypt      = true
    use_lockfile = true     # native S3 lock — no DynamoDB needed
  }
}
```

The IAM principal running Terraform needs `s3:GetObject`, `s3:PutObject`,
`s3:DeleteObject` on `<bucket>/<state-key>.tflock` in addition to normal
state-key permissions.

**DynamoDB locking is deprecated** — do not introduce it for new stacks.

---

## Bootstrap Stack Pattern

The stack that *creates* the remote state bucket must use a **local backend**.
It cannot reference the bucket it is about to create.

```hcl
# stacks/bootstrap/main.tf
terraform {
  backend "local" {}          # intentional — bootstraps the remote bucket
  required_version = ">= 1.10.0"
}
```

Key S3 state bucket resources to include:

```hcl
resource "aws_s3_bucket" "state" {
  bucket        = var.state_bucket_name
  force_destroy = false
  lifecycle { prevent_destroy = true }
}
resource "aws_s3_bucket_public_access_block" "state" { ... all four = true }
resource "aws_s3_bucket_ownership_controls" "state" {
  rule { object_ownership = "BucketOwnerEnforced" }
}
resource "aws_s3_bucket_versioning" "state" {
  versioning_configuration { status = "Enabled" }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
    bucket_key_enabled = true
  }
}
# TLS-only bucket policy
resource "aws_s3_bucket_policy" "state_tls_only" {
  depends_on = [aws_s3_bucket_public_access_block.state, aws_s3_bucket_ownership_controls.state]
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyNonTLS"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.state.arn, "${aws_s3_bucket.state.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}
```

---

## Lambda (Node.js 22, arm64) + API Gateway HTTP API

### archive_file packaging

```hcl
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../lambda/src"
  output_path = "${path.module}/../../lambda/dist/function.zip"
}
```

### Lambda resource with logging_config (aws provider ≥ 5.x)

Use the inline `logging_config` block instead of a separate managed policy
attachment for CloudWatch Logs. The managed policy
`AWSLambdaBasicExecutionRole` grants `logs:*` on `*` — avoid it for
least-privilege setups.

```hcl
resource "aws_lambda_function" "health" {
  function_name    = "${local.name_prefix}-health"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  handler          = "index.handler"
  runtime          = "nodejs22.x"
  architectures    = ["arm64"]
  role             = aws_iam_role.lambda_exec.arn
  timeout          = var.lambda_timeout_sec
  memory_size      = var.lambda_memory_mb

  logging_config {
    log_group             = aws_cloudwatch_log_group.lambda.name
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}
```

Least-privilege log policy (inline, scoped to the specific log group):

```hcl
data "aws_iam_policy_document" "lambda_logs" {
  statement {
    effect  = "Allow"
    actions = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.lambda.arn}:*"]
  }
}
resource "aws_iam_role_policy" "lambda_logs" {
  name   = "cloudwatch-logs"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_logs.json
}
```

### Lambda permission scoped to API execution ARN

```hcl
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health.function_name
  principal     = "apigateway.amazonaws.com"
  # Narrow to exactly this API — prevents any other API from invoking
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
```

### HTTP API with access logs

```hcl
resource "aws_apigatewayv2_api" "http" {
  name          = "${local.name_prefix}-http"
  protocol_type = "HTTP"
  # No cors_configuration — omit entirely for no-CORS-by-default
}

resource "aws_cloudwatch_log_group" "api_access" {
  name              = "/aws/apigateway/${local.name_prefix}-http/access"
  retention_in_days = var.log_retention_days
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access.arn
    format = jsonencode({
      requestId          = "$context.requestId"
      sourceIp           = "$context.identity.sourceIp"
      httpMethod         = "$context.httpMethod"
      routeKey           = "$context.routeKey"
      status             = "$context.status"
      responseLength     = "$context.responseLength"
      integrationLatency = "$context.integrationLatency"
      requestTime        = "$context.requestTime"
      errorMessage       = "$context.error.message"
    })
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.health.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}
```

---

## Verification Script Gotchas

**`((PASS++))` exits 1 when counter is 0** — bash arithmetic expansion returns
exit code equal to the numeric result, so `((0++))` → exit 1. Use
`PASS=$((PASS+1))` inside functions that are called from conditionals.

**Grep on `.terraform/` hits provider binaries** — `grep -r "dynamodb" stacks/`
matches text inside binary provider files. Always scope absence-checks:
```bash
grep -rq --include="*.tf" --include="*.example" "pattern" stacks/
```

---

## Terraform Binary Install Without Admin (macOS)

When `brew install hashicorp/tap/terraform` fails (e.g. outdated Xcode CLT),
install directly from HashiCorp releases:

```bash
TF_VERSION="1.12.2"   # or latest 1.x
ARCH="darwin_arm64"   # or darwin_amd64
curl -fsSL "https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_${ARCH}.zip" -o /tmp/tf.zip
cd /tmp && unzip -o tf.zip terraform
mkdir -p ~/bin && mv terraform ~/bin/terraform && chmod +x ~/bin/terraform
export PATH="$HOME/bin:$PATH"   # persist in ~/.zshrc or ~/.bashrc
terraform --version
```

Requires Terraform ≥ 1.10 for `use_lockfile = true`.
