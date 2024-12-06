import boto3
import json
from botocore.exceptions import ClientError
from datetime import datetime

# Runtime deprecation information
# Source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
RUNTIME_DEPRECATIONS = {
    "dotnet6": {"deprecated": False, "date": "2024-11-12"},
    "dotnet7": {"deprecated": False, "date": "N/A"},
    "dotnetcore1.0": {"deprecated": True, "date": "2019-07-30"},
    "dotnetcore2.0": {"deprecated": True, "date": "2019-05-30"},
    "dotnetcore2.1": {"deprecated": True, "date": "2022-01-05"},
    "dotnetcore3.1": {"deprecated": True, "date": "2023-04-03"},
    "go1.x": {"deprecated": False, "date": "2024-07-12"},
    "go2.x": {"deprecated": False, "date": "N/A"},
    "java8": {"deprecated": False, "date": "2024-01-08"},
    "java8.al2": {"deprecated": False, "date": "2025-05-30"},
    "java11": {"deprecated": False, "date": "2025-01-08"},
    "java17": {"deprecated": False, "date": "2026-09-14"},
    "java21": {"deprecated": False, "date": "N/A"},
    "nodejs": {"deprecated": True, "date": "2016-10-31"},
    "nodejs4.3": {"deprecated": True, "date": "2020-04-06"},
    "nodejs4.3-edge": {"deprecated": True, "date": "2019-04-30"},
    "nodejs6.10": {"deprecated": True, "date": "2019-08-12"},
    "nodejs8.10": {"deprecated": True, "date": "2020-03-06"},
    "nodejs10.x": {"deprecated": True, "date": "2022-02-14"},
    "nodejs12.x": {"deprecated": True, "date": "2023-03-31"},
    "nodejs14.x": {"deprecated": False, "date": "2024-11-27"},
    "nodejs16.x": {"deprecated": False, "date": "2025-06-12"},
    "nodejs18.x": {"deprecated": False, "date": "2025-06-12"},
    "nodejs20.x": {"deprecated": False, "date": "N/A"},
    "provided": {"deprecated": False, "date": "N/A"},
    "provided.al2": {"deprecated": False, "date": "N/A"},
    "provided.al2023": {"deprecated": False, "date": "N/A"},
    "python2.7": {"deprecated": True, "date": "2021-07-15"},
    "python3.6": {"deprecated": True, "date": "2022-07-18"},
    "python3.7": {"deprecated": True, "date": "2023-11-27"},
    "python3.8": {"deprecated": False, "date": "2024-10-14"},
    "python3.9": {"deprecated": False, "date": "2025-08-24"},
    "python3.10": {"deprecated": False, "date": "2026-07-30"},
    "python3.11": {"deprecated": False, "date": "2027-09-24"},
    "python3.12": {"deprecated": False, "date": "N/A"},
    "ruby2.5": {"deprecated": True, "date": "2022-07-30"},
    "ruby2.6": {"deprecated": True, "date": "2022-05-30"},
    "ruby2.7": {"deprecated": False, "date": "2023-11-07"},
    "ruby3.2": {"deprecated": False, "date": "2026-04-09"}
}

def get_deprecation_info(runtime):
    if runtime in RUNTIME_DEPRECATIONS:
        info = RUNTIME_DEPRECATIONS[runtime]
        if info["deprecated"]:
            return f"Deprecated since {info['date']}"
        elif info["date"] == "N/A":
            return "No scheduled deprecation"
        else:
            return f"Will be deprecated on {info['date']}"
    return "No deprecation information available"

def list_functions_in_account(session, account_id, region):
    functions = []
    try:
        lambda_client = session.client('lambda', region_name=region)
        paginator = lambda_client.get_paginator('list_functions')
        for page in paginator.paginate():
            for function in page['Functions']:
                try:
                    function_config = lambda_client.get_function_configuration(
                        FunctionName=function['FunctionName']
                    )
                    runtime = function_config.get('Runtime', 'Unknown')
                    deprecation_info = get_deprecation_info(runtime)
                except ClientError as e:
                    print(f"Error getting configuration for function {function['FunctionName']} in account {account_id}, region {region}: {str(e)}")
                    runtime = 'Error retrieving'
                    deprecation_info = 'Unknown'

                functions.append({
                    'AccountId': account_id,
                    'Region': region,
                    'FunctionName': function['FunctionName'],
                    'FunctionArn': function['FunctionArn'],
                    'Runtime': runtime,
                    'DeprecationInfo': deprecation_info
                })
    except ClientError as e:
        print(f"Error listing functions in account {account_id}, region {region}: {str(e)}")
    return functions

def lambda_handler(event, context):
    org_client = boto3.client('organizations')
    sts_client = boto3.client('sts')
    ec2_client = boto3.client('ec2')

    # List all accounts in the organization
    accounts = []
    paginator = org_client.get_paginator('list_accounts')
    for page in paginator.paginate():
        accounts.extend(page['Accounts'])

    # Get list of all AWS regions
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

    # Role to assume in each account
    role_to_assume = "arn:aws:iam::{}:role/CrossAccountLambdaListerRole"

    all_functions = []

    for account in accounts:
        account_id = account['Id']
        try:
            # Assume role in the account
            assumed_role = sts_client.assume_role(
                RoleArn=role_to_assume.format(account_id),
                RoleSessionName="ListLambdaFunctionsSession"
            )

            # Create session with temporary credentials
            session = boto3.Session(
                aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
                aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
                aws_session_token=assumed_role['Credentials']['SessionToken']
            )

            for region in regions:
                functions = list_functions_in_account(session, account_id, region)
                all_functions.extend(functions)

        except ClientError as e:
            print(f"Error assuming role in account {account_id}: {str(e)}")

    return {
        'statusCode': 200,
        'body': all_functions
    }