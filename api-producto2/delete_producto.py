import boto3
import os
import json

# Inicializar recursos DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        # Decodificar el cuerpo de la solicitud
        body = json.loads(event['body'])

        # Obtener el token de autorización
        token = event['headers'].get('Authorization')
        if not token:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Authorization token is missing'})
            }

        # Validar el token y verificar el rol
        lambda_client = boto3.client('lambda')
        payload = {
            "token": token,
            "role": "admin"
        }

        # Invocar la función de validación de token
        invoke_response = lambda_client.invoke(
            FunctionName="api-usuarios-dev-ValidarTokenAcceso",  # Cambia al nombre correcto de tu función
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Leer la respuesta de la validación del token
        response1 = json.loads(invoke_response['Payload'].read().decode())
        if response1['statusCode'] != 200:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden - Solo los administradores pueden eliminar productos'})
            }

        # Extraer parámetros del cuerpo
        tenant_id = body.get('tenant_id')
        producto_id = body.get('producto_id')

        # Validar parámetros obligatorios
        if not tenant_id or not producto_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'tenant_id y producto_id son requeridos'})
            }

        # Intentar eliminar el producto
        response = table.delete_item(
            Key={
                'tenant_id': tenant_id,
                'producto_id': producto_id
            },
            ReturnValues="ALL_OLD"  # Solicitar los datos del producto eliminado
        )

        # Verificar si el producto existía
        if 'Attributes' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Producto no encontrado'})
            }

        # Respuesta de éxito
        return {
            'statusCode': 204
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error eliminando el producto: {str(e)}'})
        }
