---
name: aws-sdk-swift-usage
description: "Use when the task involves aws sdk for swift in AWS. |"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, sdk, swift, ios, mobile, s3, lambda, cognito, ios-development]
    related_skills: [cloud-architect, aws-sdk-js-v3-usage, aws-sdk-python-usage]
---

# AWS SDK for Swift

## Overview

This skill covers aws sdk for swift workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/core-skills/aws-sdk-swift-usage` into Hermes-native skill format for the local `software-development` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-sdk-swift-usage`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Async Code Structure

All SDK operations are async. Use `@main` entry point:

```swift
@main
struct Main {
    static func main() async throws {
        let client = try await S3Client()
        // ... async operations
    }
}
```

## CRITICAL: Use Struct Config Types

NEVER use `S3ClientConfiguration` or `DynamoDBClientConfiguration` - these are DEPRECATED classes.

ALWAYS use the struct-based config types:

- `S3Client.S3ClientConfig` (not S3ClientConfiguration)
- `DynamoDBClient.DynamoDBClientConfig` (not DynamoDBClientConfiguration)  
- `STSClient.STSClientConfig` (not STSClientConfiguration)

Config parameters MUST be in declaration order. Region is ALWAYS required when creating a config. Check the service client source for exact order.

```swift
// CORRECT - struct config
let config = try await S3Client.S3ClientConfig(region: "us-west-2")
let client = S3Client(config: config)

// WRONG - deprecated class
// let config = try await S3Client.S3ClientConfiguration(region: "us-west-2")
```

## Client Creation

All service clients follow the same pattern: `<Service>Client` with `<Service>Client.<Service>ClientConfig`.

Model types (structs/enums used in requests/responses) are namespaced under `<Service>ClientTypes`:

- `S3ClientTypes.Bucket`, `S3ClientTypes.Object`
- `DynamoDBClientTypes.AttributeValue`
- `CloudWatchClientTypes.MetricDatum`, `CloudWatchClientTypes.Dimension`

```swift
import AWSS3
import AWSDynamoDB

// Simple - auto-detects region
let s3 = try await S3Client()
let dynamo = try await DynamoDBClient()

// With region
let s3 = try S3Client(region: "us-west-2")

// With config - parameters must be in declaration order
let config = try await S3Client.S3ClientConfig(
    useFIPS: true,
    awsRetryMode: .adaptive,
    maxAttempts: 5,
    region: "us-west-2"
)
let client = S3Client(config: config)

// With custom endpoint and credentials
let config = try await S3Client.S3ClientConfig(
    awsCredentialIdentityResolver: resolver,
    region: "us-west-2",
    endpoint: "https://s3.custom-endpoint.com"
)
```

Common config parameters (MUST follow declaration order):

- `awsCredentialIdentityResolver` - Custom credentials
- `useFIPS` - Enable FIPS endpoints
- `useDualStack` - Enable dual-stack endpoints
- `awsRetryMode` - Retry strategy (.adaptive, .standard, .legacy)
- `maxAttempts` - Max retry attempts
- `region` - AWS region
- `httpClientEngine` - Custom HTTP client (requires HttpClientConfiguration parameter):

  ```swift
  import ClientRuntime
  let httpConfig = HttpClientConfiguration()
  let httpClient = URLSessionHTTPClient(httpClientConfiguration: httpConfig)
  let config = try await S3Client.S3ClientConfig(
      region: "us-east-1",
      httpClientEngine: httpClient
  )
  ```

- `endpoint` - Custom endpoint URL

For service-specific config options or exact parameter order, check `Sources/Services/AWS<Service>/Sources/AWS<Service>/<Service>Client.swift` in the SDK.

## Credential Resolvers

```swift
import AWSSDKIdentity
import SmithyIdentity

// Static credentials - pass credential object directly
let creds = AWSCredentialIdentity(accessKey: "AKIA...", secret: "...")
let resolver = StaticAWSCredentialIdentityResolver(creds)

// Assume role - REQUIRES underlying resolver
let underlying = try DefaultAWSCredentialIdentityResolverChain()
let resolver = try STSAssumeRoleAWSCredentialIdentityResolver(
    awsCredentialIdentityResolver: underlying,
    roleArn: "arn:aws:iam::123456789012:role/MyRole",
    sessionName: "session-name"
)

// Use in config
let config = try await S3Client.S3ClientConfig(
    awsCredentialIdentityResolver: resolver,
    region: "us-west-2"
)
```

## Waiters

Import `SmithyWaitersAPI`. WaiterOptions requires `maxWaitTime` parameter:

```swift
import AWSS3
import SmithyWaitersAPI

let client = try await S3Client()
_ = try await client.waitUntilBucketExists(
    options: WaiterOptions(maxWaitTime: 120.0),
    input: HeadBucketInput(bucket: "my-bucket")
)
```

## Pagination

```swift
let input = ListObjectsV2Input(bucket: "my-bucket")
for try await page in client.listObjectsV2Paginated(input: input) {
    for object in page.contents ?? [] {
        print(object.key ?? "")
    }
}
```

## Presigned URLs

```swift
let url = try await client.presignedURLForGetObject(
    input: GetObjectInput(bucket: "my-bucket", key: "file.pdf"),
    expiration: 3600
)
```

## Common Operations

```swift
// Put object
_ = try await client.putObject(input: PutObjectInput(
    body: .data(data),
    bucket: "bucket",
    key: "key"
))

// Get object
let output = try await client.getObject(input: GetObjectInput(bucket: "bucket", key: "key"))
let data = try await output.body?.readData()

// List buckets
let response = try await client.listBuckets(input: ListBucketsInput())
for bucket in response.buckets ?? [] {
    print(bucket.name ?? "")
}
```

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
