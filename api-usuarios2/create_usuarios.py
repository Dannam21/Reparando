import boto3
import uuid
import datetime
import hashlib
import os
import json
import logging
from boto3.dynamodb.conditions import Key

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
USERS_TABLE = os.environ['USERS_TABLE']
table = dynamodb.Table(USERS_TABLE)
TOKENS_TABLE = 't_tokens_acceso'
tokens_table = dynamodb.Table(TOKENS_TABLE)

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    try:
        # Log the received event
        logger.info("Received event: %s", json.dumps(event))

        # Parse the event body
        body = json.loads(event['body'])
        tenant_id = body.get('tenant_id')
        email = body.get('email')
        password = body.get('password')
        data = body.get('data')

        # Validate required fields
        if not tenant_id or not email or not data or not password:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing tenantID, email, nombre, or password'})
            }

        # Check if the email already exists for the given tenantID
        response = table.query(
            IndexName='BusquedaPorEmail',  # El nombre del índice LSI
            KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('email').eq(email)
        )
        if response['Items']:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Email already exists for this tenant'})
            }

        # Hash the password
        password_hash = hash_password(password)

        # Generate user ID and creation date
        year_prefix = datetime.datetime.utcnow().strftime('%Y')
        user_id = f"{year_prefix}-{str(uuid.uuid4())}"
        fecha_creacion = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')

        # Create user item
        usuario = {
            'tenant_id': tenant_id,
            'user_id': user_id,
            'email': email,
            'password': password_hash,
            'data': data,
            'role': "user",
            'fechaCreacion': fecha_creacion,
            'ultimoAcceso': fecha_creacion
        }

        # Store user in DynamoDB
        table.put_item(Item=usuario)

        # Generate token
        token = str(uuid.uuid4())
        fecha_hora_exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
        registro = {
            'token': token,
            'expires': fecha_hora_exp.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'tenant_id': tenant_id,
            'role':usuario["role"]
        }
        tokens_table.put_item(Item=registro)

        # Return success response with token
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Usuario creado',
                'tenant_id': tenant_id,
                'user_id': user_id,
                'fechaCreacion': fecha_creacion,
                'token': token
            })
        }
    except Exception as e:
        logger.error("Error creating user: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }