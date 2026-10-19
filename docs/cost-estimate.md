# Cost and free-usage controls

**No zero-cost guarantee is made.** This project's code and CloudFormation template are not a billing contract. AWS free usage depends on account age, free-plan or credits, service, region, request volume, data retention, and current pricing. Check the live billing account before creating resources.

## Cost drivers and controls

| Service | Purpose in Sentinal | Likely metered driver | Built-in control / decision |
|---|---|---|---|
| API Gateway HTTP API | protected JSON/upload API | requests and data transfer | 5 MB input limit; configure throttles before public exposure; not deployed |
| Lambda | API/analysis/report worker | invocations, GB-seconds, logs | small bounded jobs; API timeout 30 s, worker 120 s; no provisioned concurrency |
| Step Functions Standard | analyze → explain → report | state transitions | three principal stages per scan plus retries; avoid unnecessary loops |
| S3 | input/analysis/PDF artifacts | storage, requests, transfer | private block-public bucket, SSE-S3, input expiry after 1 day, analysis/report expiry after 30 days |
| DynamoDB on-demand | metadata/findings/history | reads/writes and stored data | pay-per-request avoids provisioned over-allocation but is still metered; scope rows to one job |
| Bedrock | AI narrative | input/output tokens or model-specific inference units | disabled by default; explicit model ID and IAM are required to enable; not included in any zero-cost assumption |
| Cognito | user registration and JWT | monthly active users and optional add-ons | included only as cloud target; check current regional/user-pool terms |
| CodeBuild | platform regression build | build minutes, compute, logs, data transfer | small instance, 15-minute timeout, no privileged mode; start on demand only, not deployed |
| CloudWatch | function and build logs | log ingestion/storage and alarms | 7-day Lambda log retention; optional alarm parameter defaults false |
| Local Ollama (optional) | on-device AI explanations | local CPU/GPU, memory and electricity | no model API charge; requires installing a compatible local model and sufficient hardware; default remains disabled |
| OpenAI API (optional) | alternative AI explanation provider | tokens/API usage | disabled by default; API key must be supplied securely; not a free AWS service |

## Safe default deployment parameters

- `AiProvider=disabled`.
- `BedrockModelId` empty.
- `CreateErrorAlarm=false` (enable only after confirming current alarm pricing/allowance).
- Small upload/file/analysis limits retained.
- Lifecycle rules enabled for temporary input and retained artifacts.
- No provisioned concurrency, NAT Gateway, EC2, RDS, OpenSearch or paid vector database in the template.

## Before a deployment

1. Confirm whether this AWS account is on a free plan, credits plan or paid plan and the actual credit expiry/remaining balance.
2. Inspect the official regional prices and free-usage limits for every resource in the deployment diff, especially API Gateway, Step Functions, DynamoDB, S3, Cognito, CodeBuild and CloudWatch.
3. Choose a budget and billing notifications where the account supports them. Alarms notify; they do not automatically prevent charges.
4. Keep Bedrock and OpenAI disabled unless model cost and source-code handling are explicitly approved.
5. Deploy only a reviewed diff through a least-privilege IAM role. Monitor after use; run `sam delete` after a demonstration if the deployment is no longer needed, then verify S3 objects and log groups were removed.

## What was verified in this session

A read-only inspection of the connected AWS account found an existing S3 bucket, Lambda worker, Step Functions state machine, two DynamoDB tables, CodeBuild project, and enabled Athena workgroup in `ap-south-1`. It returned no API Gateway APIs, no CloudWatch alarms and no Glue databases. The caller identity resolved to the AWS **root principal**. The AWS Free Tier account-plan API reported **PAID / ACTIVE**. Its usage response reported 13 usage categories, including some entries below their listed always-free monthly thresholds, but this was not a complete per-resource bill or a guarantee of zero future charges. Available credits may offset charges temporarily and may expire or be exhausted. No resources were created or updated.

## Official pricing references (re-check immediately before use)

- [AWS Free Tier](https://aws.amazon.com/free/) explains current account plan, credits and eligibility; the account's actual plan and credit balance must be checked in Billing.
- [Amazon API Gateway pricing](https://aws.amazon.com/api-gateway/pricing/) lists request allowances and standard request pricing. Any stated free request allowance is eligibility/time limited and does not guarantee a zero bill.
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) and [Bedrock model usage reporting](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring-costs.html) are the source of truth for model-specific inference cost. Bedrock is **not assumed free**.
- [AWS Step Functions pricing](https://aws.amazon.com/step-functions/pricing/) lists Standard/Express workflow billing and eligible free transitions. Retries and extra stages increase usage.
- Also check the live regional prices for Lambda, S3, DynamoDB, Cognito, CodeBuild and CloudWatch before deployment. Costs and free offers may change; alerts notify but do not cap spending.
