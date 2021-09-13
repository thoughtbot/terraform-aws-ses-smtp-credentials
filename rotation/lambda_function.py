# Based on the generic template provided by Amazon:
# https://github.com/aws-samples/aws-secrets-manager-rotation-lambdas

import base64
import boto3
import hashlib
import hmac
import json
import logging
import os
import time

from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Access key rotation lambda

    Args:
        event (dict): Lambda dictionary of event parameters. These keys must include the following:
            - SecretId: The secret ARN or identifier
            - ClientRequestToken: The ClientRequestToken of the secret version
            - Step: The rotation step (one of createSecret, setSecret, testSecret, or finishSecret)

        context (LambdaContext): The Lambda runtime information

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

        ValueError: If the secret is not properly configured for rotation

        KeyError: If the event parameters do not contain the expected keys

    """
    arn = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    # Setup the client
    service_client = boto3.client('secretsmanager', endpoint_url=os.environ['SECRETS_MANAGER_ENDPOINT'])

    # Make sure the version is staged correctly
    metadata = service_client.describe_secret(SecretId=arn)
    if not metadata['RotationEnabled']:
        logger.error("Secret %s is not enabled for rotation" % arn)
        raise ValueError("Secret %s is not enabled for rotation" % arn)
    versions = metadata['VersionIdsToStages']
    if token not in versions:
        logger.error("Secret version %s has no stage for rotation of secret %s." % (token, arn))
        raise ValueError("Secret version %s has no stage for rotation of secret %s." % (token, arn))
    if "AWSCURRENT" in versions[token]:
        logger.info("Secret version %s already set as AWSCURRENT for secret %s." % (token, arn))
        return
    elif "AWSPENDING" not in versions[token]:
        logger.error("Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, arn))
        raise ValueError("Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, arn))

    if step == "createSecret":
        create_secret(service_client, arn, token)

    elif step == "setSecret":
        set_secret(service_client, arn, token)

    elif step == "testSecret":
        test_secret(service_client, arn, token)

    elif step == "finishSecret":
        finish_secret(service_client, arn, token)

    else:
        raise ValueError("Invalid step parameter")


def create_secret(service_client, arn, token):
    """Create the secret

    This method first checks for the existence of a secret for the passed in
    token. If one does not exist, it will generate a new secret and put it with
    the passed in token. The oldest access key will be deleted.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist

    """
    username = os.environ['USERNAME']
    iam = boto3.client('iam')

    # Make sure the current secret exists
    current_secret = get_secret_dict(service_client, arn, "AWSCURRENT")

    # Check to see if we already have a value for this version of the secret
    try:
        # If we do, return it
        service_client.get_secret_value(SecretId=arn, VersionId=token, VersionStage="AWSPENDING")
        logger.info("createSecret: Successfully retrieved secret for %s." % arn)
    except service_client.exceptions.ResourceNotFoundException:
        # Delete any access keys besides the active one
        access_keys = iam.list_access_keys(UserName=username)
        for key in access_keys['AccessKeyMetadata']:
            access_key_id = key['AccessKeyId']
            if access_key_id != current_secret['SMTP_USERNAME']:
                iam.delete_access_key(UserName=username, AccessKeyId=access_key_id)
                logger.info("finishSecret: Deleted previous access key %s for %s" % (access_key_id, arn))

        # Create a new access key
        response = iam.create_access_key(UserName=username)
        logger.info("createSecret: Created access key for %s." % username)
        access_key = response['AccessKey']
        pending_access_key_id = access_key['AccessKeyId']
        current_secret['SMTP_USERNAME'] = pending_access_key_id
        current_secret['SMTP_SECRET'] = access_key['SecretAccessKey']
        current_secret['SMTP_PASSWORD'] = calculate_password(access_key['SecretAccessKey'], current_secret['SMTP_REGION'])

        # Put the secret
        service_client.put_secret_value(SecretId=arn, ClientRequestToken=token, SecretString=json.dumps(current_secret), VersionStages=['AWSPENDING'])
        logger.info("createSecret: Successfully put secret for ARN %s and version %s." % (arn, token))

def set_secret(service_client, arn, token):
    """Set the secret

    You can't generate your own access keys (they are generated by AWS), which
    means the access key already exists and there is nothing to set at this
    stage.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    """
    pass


def test_secret(service_client, arn, token):
    """Test the secret

    Validate that the secret value authenticates as the expected user.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    """

    # Get the pending version of the secret
    logger.info("testSecret: fetching AWSPENDING stage of version %s for secret %s." % (token, arn))
    pending = get_secret_dict(service_client, arn, "AWSPENDING", token)

    # Attempt to authenticate using the pending access key
    username = check_access_key(pending['SMTP_USERNAME'], pending['SMTP_SECRET'])

    # Verify that we're authenticated as the expected user
    if username == os.environ['USERNAME']:
        logger.info("testSecret: authenticated as %s for AWSPENDING stage of version %s for secret %s." % (username, token, arn))
        return
    else:
        logger.error("testSecret: authenticated as %s for AWSPENDING stage of version %s for secret %s." % (username, token, arn))
        raise ValueError("authenticated as %s for AWSPENDING stage of version %s for secret %s." % (username, token, arn))

def check_access_key(access_key_id, secret_access_key, attempts=5):
    try:
        caller=boto3.client('sts',
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key).get_caller_identity()
        _prefix, username = caller['Arn'].split('/', 2)
        return username
    except ClientError:
        logger.warn("Failed to authenticate with access key; %d attempts remaining" % (attempts))
        if attempts >= 0:
            time.sleep(5)
            return check_access_key(access_key_id, secret_access_key, attempts - 1)
        else:
            raise ValueError("unable to authenticate using generated access keys")



def finish_secret(service_client, arn, token):
    """Finish the secret

    This method finalizes the rotation process by marking the secret version
    passed in as the AWSCURRENT secret.

    Args:
        service_client (client): The secrets manager service client

        arn (string): The secret ARN or other identifier

        token (string): The ClientRequestToken associated with the secret version

    Raises:
        ResourceNotFoundException: If the secret with the specified arn does not exist

    """
    # First describe the secret to get the current version
    metadata = service_client.describe_secret(SecretId=arn)
    current_version = None
    for version in metadata["VersionIdsToStages"]:
        if "AWSCURRENT" in metadata["VersionIdsToStages"][version]:
            if version == token:
                # The correct version is already marked as current, return
                logger.info("finishSecret: Version %s already marked as AWSCURRENT for %s" % (version, arn))
                return
            current_version = version
            break

    # Finalize by staging the secret version current
    service_client.update_secret_version_stage(SecretId=arn, VersionStage="AWSCURRENT", MoveToVersionId=token, RemoveFromVersionId=current_version)
    logger.info("finishSecret: Successfully set AWSCURRENT stage to version %s for secret %s." % (token, arn))

def get_secret_dict(service_client, arn, stage, token=None):
    """Gets the secret dictionary corresponding for the secret arn, stage, and token
    This helper function gets credentials for the arn and stage passed in and returns the dictionary by parsing the JSON string
    Args:
        service_client (client): The secrets manager service client
        arn (string): The secret ARN or other identifier
        token (string): The ClientRequestToken associated with the secret version, or None if no validation is desired
        stage (string): The stage identifying the secret version
    Returns:
        SecretDictionary: Secret dictionary
    Raises:
        ResourceNotFoundException: If the secret with the specified arn and stage does not exist
        ValueError: If the secret is not valid JSON
        KeyError: If the secret json does not contain the expected keys
    """
    required_fields = ['SMTP_USERNAME', 'SMTP_PASSWORD', 'SMTP_REGION']

    # Only do VersionId validation against the stage if a token is passed in
    if token:
        secret = service_client.get_secret_value(SecretId=arn, VersionId=token, VersionStage=stage)
    else:
        secret = service_client.get_secret_value(SecretId=arn, VersionStage=stage)
    plaintext = secret['SecretString']
    secret_dict = json.loads(plaintext)

    for field in required_fields:
        if field not in secret_dict:
            raise KeyError("%s key is missing from secret JSON" % field)

    # Parse and return the secret JSON string
    return secret_dict

# Convert an IAM secret access key into an SMTP password for SES:
# https://aws.amazon.com/premiumsupport/knowledge-center/ses-rotate-smtp-access-keys/
DATE = "11111111"
SERVICE = "ses"
MESSAGE = "SendRawEmail"
TERMINAL = "aws4_request"
VERSION = 0x04

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def calculate_password(secret_access_key, region):
    signature = sign(("AWS4" + secret_access_key).encode('utf-8'), DATE)
    signature = sign(signature, region)
    signature = sign(signature, SERVICE)
    signature = sign(signature, TERMINAL)
    signature = sign(signature, MESSAGE)
    signature_and_version = bytes([VERSION]) + signature
    smtp_password = base64.b64encode(signature_and_version)
    return smtp_password.decode('utf-8')

