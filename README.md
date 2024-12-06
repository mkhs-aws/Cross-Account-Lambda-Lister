# Cross-Account Lambda Function Lister

This project provides a Lambda function that lists all AWS Lambda functions across multiple AWS accounts and regions, including their runtime and deprecation status.

The Cross-Account Lambda Function Lister is designed to help organizations manage and monitor their Lambda functions across a multi-account AWS environment. It leverages AWS Organizations and cross-account IAM roles to gather comprehensive information about Lambda functions, including their runtime versions and deprecation status.

Key features include:
- Cross-account and cross-region Lambda function discovery
- Runtime version identification
- Deprecation status reporting based on AWS's runtime deprecation schedule
- Scalable design to handle large AWS Organizations

## Repository Structure

- `CrossAccountLambdaLister.py`: The main Lambda function code that performs the cross-account Lambda function listing.
- `CrossAccountLambdaListerPolicy.json`: IAM policy granting permissions to list and get Lambda function configurations.
- `LambdaAssumeCrossAccountLambdaListerPolicy.json`: IAM policy allowing the Lambda function to assume the necessary role in other accounts.
- `LambdaListAccountsFunctionsPolicy.json`: IAM policy granting permissions to list accounts and Lambda functions.

## Usage Instructions

### Setup

1. Create a policy in each account using the `CrossAccountLambdaListerPolicy.json` file.
2. Create a role named `CrossAccountLambdaListerRole` in each account and attach the `CrossAccountLambdaListerPolicy`.
3. In the master account where the CrossAccountLambdaLister function will run:
   a. Create a policy using the `LambdaAssumeCrossAccountLambdaListerPolicy.json` file.
   b. Create another policy using the `LambdaListAccountsFunctionsPolicy.json` file.
   c. Create a Lambda runtime role and attach both `LambdaAssumeCrossAccountLambdaListerPolicy` and `LambdaListAccountsFunctionsPolicy`.

### Installation

Prerequisites:
- AWS CLI configured with appropriate permissions
- Python 3.8 or later
- Boto3 library installed

To set up the Cross-Account Lambda Function Lister:

1. Ensure all the setup steps above have been completed.
2. Create a Lambda function in your master account:
   ```
   aws lambda create-function --function-name CrossAccountLambdaLister \
     --runtime python3.8 --handler CrossAccountLambdaLister.lambda_handler \
     --role arn:aws:iam::YOUR_ACCOUNT_ID:role/CrossAccountLambdaListerRole \
     --zip-file fileb://CrossAccountLambdaLister.zip
   ```

### Configuration

The Lambda function uses a predefined dictionary `RUNTIME_DEPRECATIONS` to determine the deprecation status of Lambda runtimes. This dictionary is sourced from the AWS Lambda Runtimes documentation (https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) and was generated using Anthropic's Claude.ai GenAI. Update this dictionary in `CrossAccountLambdaLister.py` if you need to modify or add new runtime deprecation information.

### Execution

To run the Lambda function:

```
aws lambda invoke --function-name CrossAccountLambdaLister output.json
```

The function will return a JSON object containing information about all Lambda functions across your accounts and regions. The output is an array of Lambda functions including Account ID, Region, Function Name, Function ARN, Runtime, and Deprecation Information. For example:

```json
{
  "AccountId": "343218200688",
  "Region": "us-east-1",
  "FunctionName": "nodejs18-test",
  "FunctionArn": "arn:aws:lambda:us-east-1:343218200688:function:nodejs18-test",
  "Runtime": "nodejs18.x",
  "DeprecationInfo": "Will be deprecated on 2025-06-12"
}
```

### Common Use Cases

1. Audit Lambda function runtimes:
   ```python
   import json

   with open('output.json', 'r') as f:
       data = json.load(f)

   deprecated_functions = [f for f in data['body'] if 'Deprecated' in f['DeprecationInfo']]
   print(f"Found {len(deprecated_functions)} deprecated Lambda functions.")
   ```

2. Find functions in specific regions:
   ```python
   us_east_1_functions = [f for f in data['body'] if f['Region'] == 'us-east-1']
   print(f"Found {len(us_east_1_functions)} functions in us-east-1.")
   ```

### Troubleshooting

Common issues and solutions:

1. "Access Denied" errors:
   - Ensure that the `CrossAccountLambdaListerRole` exists in all accounts and has the correct trust relationship.
   - Verify that the Lambda function's execution role has the `LambdaAssumeCrossAccountLambdaListerPolicy` attached.

2. Missing functions in the output:
   - Check that the `CrossAccountLambdaListerPolicy` in each account grants access to all regions you want to scan.
   - Ensure the Lambda function has sufficient execution time to scan all accounts and regions.

To enable debug logging:
1. Set the environment variable `DEBUG_LOGGING` to `True` for the Lambda function.
2. Check the CloudWatch Logs for the Lambda function to see detailed execution logs.

## Data Flow

The Cross-Account Lambda Function Lister follows this data flow:

1. The Lambda function is invoked, triggering the `lambda_handler` function.
2. It uses AWS Organizations to list all accounts in the organization.
3. For each account:
   a. The function assumes the `CrossAccountLambdaListerRole` in the target account.
   b. It then lists all AWS regions.
   c. For each region, it lists all Lambda functions and retrieves their configurations.
4. The function compiles the data, including runtime and deprecation information.
5. Finally, it returns a JSON object containing details of all discovered Lambda functions.

```
[Lambda Invocation] -> [List Org Accounts] -> [For Each Account] -> [Assume Role] -> 
[List Regions] -> [For Each Region] -> [List Lambda Functions] -> 
[Get Function Configs] -> [Compile Data] -> [Return JSON Response]
```

Note: The function uses pagination to handle large numbers of accounts and functions, ensuring comprehensive coverage of the AWS environment.

## Infrastructure

The project defines the following important infrastructure resources:

### IAM Policies

1. CrossAccountLambdaListerPolicy
   - Type: AWS::IAM::ManagedPolicy
   - Purpose: Grants permissions to list Lambda functions and get their configurations across accounts

2. LambdaAssumeCrossAccountLambdaListerPolicy
   - Type: AWS::IAM::ManagedPolicy
   - Purpose: Allows the Lambda function to assume the CrossAccountLambdaListerRole in other accounts

3. LambdaListAccountsFunctionsPolicy
   - Type: AWS::IAM::ManagedPolicy
   - Purpose: Grants permissions to list accounts in the organization and list/get Lambda functions

### Lambda Function

- Type: AWS::Lambda::Function
- Name: CrossAccountLambdaLister
- Purpose: Executes the cross-account Lambda function listing logic

Note: The actual Lambda function resource is not defined in the provided infrastructure files but is mentioned here for completeness.