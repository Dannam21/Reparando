import boto3
import hashlib
import uuid
from datetime import datetime, timedelta
import json
import os
import logging
from boto3.dynamodb.conditions import Key

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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

        print("pasos")

        # Validate required fields
        if not tenant_id or not email or not password:
            return {
                'statusCode': 400,
                'headers':{
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True, 
                },
                'body': json.dumps({'error': 'Missing tenant_id, email, or password'})
            }
        print("pasos1")
        hashed_password = hash_password(password)

        # Process
        dynamodb = boto3.resource('dynamodb')
        users_table = dynamodb.Table(os.environ['USERS_TABLE'])
        tokens_table = dynamodb.Table(os.environ['TOKENS_TABLE'])

        response = users_table.query(
            IndexName='BusquedaPorEmail',  # El nombre del índice LSI
            KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('email').eq(email)
        )
        items = response.get('Items', [])
        print("pasos2")
        if not items:
            return {
                'statusCode': 403,
                 'headers':{
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True, 
                },
                'body': json.dumps({'error': 'Usuario no existe'})
            }
        print("pasos3")
        item = items[0]
        if hashed_password == item['password']:
            # Generate token
            token = str(uuid.uuid4())
            fecha_hora_exp = datetime.utcnow() + timedelta(minutes=60)
            registro = {
                'token': token,
                'expires': fecha_hora_exp.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': item['user_id'],
                'tenant_id': tenant_id,
                'role':item["role"]
            }
            tokens_table.put_item(Item=registro)
        else:
            return {
                'statusCode': 403,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True, 
                },
                'body': json.dumps({'error': 'Password incorrecto'})
            }

        # Output (json)
        return {
            'statusCode': 200,
            'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True, 
                },
            'body': json.dumps({'token': token})
        }
    except Exception as e:
        logger.error("Error during login: %s", str(e))
        return {
            'statusCode': 500,
            'headers':  {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True, 
                },
            'body': json.dumps({'error': 'Internal server error'})
        }