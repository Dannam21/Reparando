import boto3
import os
import json

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        # Obtener tenant_id y limit de los parámetros de consulta
        tenant_id = event['queryStringParameters'].get('tennat_id')
        limit = int(event['queryStringParameters'].get('limit', 10))  # Valor predeterminado de 10 si no se proporciona limit

        # Validar que tenant_id esté presente
        if not tenant_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'tenantID es requerido'})
            }

        # Realizar la consulta en DynamoDB
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id),
            Limit=limit
        )

        # Obtener los productos
        items = response.get('Items', [])

        # Devolver la lista de productos
        return {
            'statusCode': 200,
            'body': json.dumps({
                'productos': items
            })
        }

    except Exception as e:
        # Manejo de errores generales
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Ocurrió un error al obtener los productos: {str(e)}'
            })
        }
