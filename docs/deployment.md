# Deployment guide

This is a deployment **procedure**, not a record of a completed AWS deployment. No stack was created from this session.

## Pre-deployment controls

1. Use a non-root, MFA-protected, least-privilege deployment identity. The inspected connector identity was root; that identity should not be used for routine setup.
2. Check actual account free-plan/credits, all current regional prices, quotas and model access. The template's metered resources can exceed allowances. Keep AI disabled and the alarm disabled initially.
3. Choose an HTTPS frontend origin and set `FrontendOrigin`. Local default is `http://localhost:5173` for coursework development only.
4. Review the SAM template and generated IAM changes before creating the stack. Avoid deploying from the root account.

## Deploy target infrastructure

Install AWS SAM CLI and configure a permitted profile/region. From the repository root:

```bash
sam validate --template-file infra/template.yaml
sam build --template-file infra/template.yaml
sam deploy --template-file infra/template.yaml --guided
```

Use `ap-south-1` if that is where your course resources should live, but do not assume account-specific allowances. Start with `AiProvider=disabled`, empty `BedrockModelId`, and `CreateErrorAlarm=false`. Only enable Bedrock after choosing a supported model/inference profile, reviewing costs and restricting `BedrockModelId` to its approved ARN/ID. The template gates the worker model policy on `AiProvider=bedrock`.

After deployment, copy these stack outputs into a private local frontend env file:

```env
VITE_API_BASE_URL=<ApiBaseUrl output>
VITE_COGNITO_USER_POOL_ID=<CognitoUserPoolId output>
VITE_COGNITO_CLIENT_ID=<CognitoUserPoolClientId output>
VITE_AWS_REGION=<deployment region>
```

Build the web UI (`cd frontend && npm install && npm run build`) and deploy `frontend/dist` only to an approved static host with HTTPS and the matching exact origin. A static hosting service has its own terms/cost, so it is not provisioned in this template; for a local demonstration simply use Vite.

## Seed CodeBuild with reviewed Sentinal source

CodeBuild is configured to run **Sentinal's own tests/build**, not to execute arbitrary submitted projects by default. Run `python scripts/package-ci-source.py --output sentinal-ci-source.zip` to create an archive with `backend/`, `frontend/`, and `infra/` at its root, while excluding `.git`, dependency folders, `.env` secrets, local history, reference previews, and generated output. Upload the archive to the deployed `ArtifactsBucketName` output at `ci/sentinal-source.zip`, then start the `CodeBuildProjectName` project manually. It installs backend requirements, runs pytest, then executes `npm install && npm run build`.

## Test the cloud path

- Register a test account and verify Cognito email flows.
- Confirm API Gateway returns 401 without a JWT and serves health/history with a valid user token.
- Submit only the packaged demo first; then test a tiny public repository and a small ZIP.
- Verify the workflow runs Analyze → Explain → GenerateReport, all stages appear in the job, and a PDF download is scoped to the authenticated user.
- Try cross-user job IDs and confirm they return not found.
- Verify S3 is private, upload cleanup works, DynamoDB owner partition is populated, Lambda logs expire after seven days, and alarm is absent unless enabled.
- Check current billing/usage after the test and delete the stack when finished; confirm bucket contents are removed according to the retention plan.

## Current limitations

API Gateway's JWT authorization is defined as a default authorizer in the template; all routes including health require a token in this deployment configuration. The React app requests health/history after a successful sign-in. The Cognito user pool configuration is the initial course-demo setup; add quotas/anti-abuse protections and account lifecycle processes before exposing publicly.
