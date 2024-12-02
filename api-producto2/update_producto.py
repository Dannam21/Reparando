import boto3
import os
import json

# Inicializar DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

# Inicializar el cliente de Lambda para la validación del token
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Obtener el token de autorización del encabezado
        token = event['headers'].get('Authorization')
        
        # Verificar si el token está presente
        if not token:
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Token de autorización faltante'})
            }

        # Validar el token enviándolo a una función Lambda de validación
        payload = {
            "token": token,
            "role": "admin"  # Aquí asumes que el rol debe ser "admin"
        }

        # Invocar la función Lambda de validación de token
        invoke_response = lambda_client.invoke(
            FunctionName="api-usuarios-dev-ValidarTokenAcceso",  # Cambia el nombre de la función Lambda aquí
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Leer la respuesta de la validación
        response = json.loads(invoke_response['Payload'].read().decode())
        if response.get('statusCode') != 200:
            return {
                'statusCode': 403,
                'body': json.dumps({'message': 'Acceso denegado. Token no válido o rol no autorizado'})
            }

        # Deserializar el cuerpo de la solicitud si es una cadena JSON
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']

        tenant_id = body.get('tenant_id')
        producto_id = body.get('producto_id')
        updates = body.get('updates')

        if not tenant_id or not producto_id or not updates:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'tenant_id, producto_id y updates son requeridos'})
            }

        # Construir la expresión de actualización
        update_expression = "SET "
        expression_values = {}

        for key, value in updates.items():
            update_expression += f" {key} = :{key},"
            expression_values[f":{key}"] = value

        # Eliminar la última coma de la expresión
        update_expression = update_expression.rstrip(',')

        # Realizar la actualización en DynamoDB
        response = table.update_item(
            Key={'tenant_id': tenant_id, 'producto_id': producto_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )

        # Devolver la respuesta con los atributos actualizados
        return {
            'statusCode': 200
        }

    except Exception as e:
        # Manejo de errores
        return {
            'statusCode': 500
        }
