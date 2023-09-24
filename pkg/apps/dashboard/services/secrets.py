import json
import boto3

from ..wrappers import secretsmanager_wrapper 


sm_client = boto3.client('secretsmanager')

def create_secret(identifier, username, password):
    value = json.dumps({
        "username": username,
        "password": password
    })
    
    secret = secretsmanager_wrapper.SecretsManagerSecret(sm_client)
    return secret.create(identifier, value)


def get_secret_value(identifier):
    secret = secretsmanager_wrapper.SecretsManagerSecret(sm_client)
    response = secret.get_value(name=identifier)
    secrets_credentials = json.loads(response['SecretString'])
    return secrets_credentials['username'], secrets_credentials['password']


def update_value(identifier, value):
    secret = secretsmanager_wrapper.SecretsManagerSecret(sm_client)
    response = secret.put_value(name=identifier, secret_value=value)
    return response


def delete_secret(identifier, without_recovery=False):
    secret = secretsmanager_wrapper.SecretsManagerSecret(sm_client)
    response = secret.delete(identifier, without_recovery)
    return 