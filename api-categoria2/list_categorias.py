import boto3
import os
import logging
import json

def lambda_handler(event, context):
    try:
        # Obtén el nombre de la tabla desde las variables de entorno
        table_name = os.environ.get('TABLE_NAME', 'DefaultTable') 
        logging.info(f"Nombre de la tabla: {table_name}")
        
        # Accede a los parámetros queryStringParameters
        tenant_id = event['queryStringParameters'].get('tenant_id', None)
        limit = event['queryStringParameters'].get('limit', 10)
        
        if tenant_id is None:
            logging.error("tenant_id es obligatorio")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'tenant_id es obligatorio'})
            }
        
        try:
            limit = int(limit)
        except ValueError:
            logging.error("Limit no es un número válido")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'limit debe ser un número entero'})
            }

        logging.info(f"Parámetros recibidos - tenant_id: {tenant_id}, limit: {limit}")
        
        # Crear el recurso DynamoDB
        dynamodb = boto3.resource('dynamodb')
        
        # Obtener la tabla de DynamoDB usando el nombre de la tabla
        table = dynamodb.Table(table_name)
        
        # Ejecutar la consulta en la tabla
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id),
            Limit=limit
        )

        # Obtener los elementos de la respuesta
        items = response.get('Items', [])

        logging.info(f"Items encontrados: {items}")

        return {
            'statusCode': 200,
            'body': json.dumps({'categorias': items})  # Convertimos a JSON
        }
    
    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f"Error interno del servidor: {str(e)}"})
        }
