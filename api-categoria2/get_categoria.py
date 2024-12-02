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
        categoria_id = event['queryStringParameters'].get('categoria_id', None)
        tenant_id = event['queryStringParameters'].get('tenant_id', None)
        
        if not categoria_id or not tenant_id:
            logging.error("Faltan parámetros requeridos: categoria_id o tenant_id")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'categoria_id y tenant_id son obligatorios'})
            }

        logging.info(f"Parámetros recibidos - categoria_id: {categoria_id}, tenant_id: {tenant_id}")
        
        # Crear el recurso DynamoDB
        dynamodb = boto3.resource('dynamodb')
        
        # Obtener la tabla de DynamoDB usando el nombre de la tabla
        table = dynamodb.Table(table_name)
        
        # Ejecutar la consulta en la tabla
        response = table.get_item(
            Key={'tenant_id': tenant_id, 'categoria_id': categoria_id}
        )

        # Verificar si la respuesta contiene el item
        if 'Item' not in response:
            logging.info(f"Categoría no encontrada para tenant_id: {tenant_id} y categoria_id: {categoria_id}")
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Categoría no encontrada'})
            }

        item = response['Item']
        logging.info(f"Categoría encontrada: {item}")

        return {
            'statusCode': 200,
            'body': json.dumps({'categoria': item})  # Convertimos a JSON
        }
    
    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f"Error interno del servidor: {str(e)}"})
        }
