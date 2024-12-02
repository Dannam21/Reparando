import boto3
import os
import json

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        # Obtener el token de autorización del encabezado
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
                'body': json.dumps({'error': 'Forbidden - Solo los administradores pueden eliminar categorías'})
            }

        # Obtener el cuerpo de la solicitud
        body = event['body']

        # Deserializar si el body está en formato JSON
        if isinstance(body, str):
            body = json.loads(body)
        
        categoria_id = body['categoria_id']
        tenant_id = body['tenant_id']

        # Verificar si el ítem existe antes de eliminarlo
        response = table.get_item(
            Key={
                'categoria_id': categoria_id,
                'tenant_id': tenant_id
            }
        )

        if 'Item' not in response:
            print(f"Item with categoria_id: {categoria_id} and tenant_id: {tenant_id} not found.")
            return {
                'statusCode': 404,
                'body': json.dumps('Categoría no encontrada')
            }

        # Si el ítem existe, proceder con la eliminación
        try:
            delete_response = table.delete_item(
                Key={
                    'categoria_id': categoria_id,
                    'tenant_id': tenant_id
                }
            )

            return {
                'statusCode': 200,
                'body': json.dumps('Categoría eliminada con éxito')
            }

        except Exception as e:
            print(f"Error al eliminar la categoría: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps(f'Error al eliminar la categoría: {str(e)}')
            }

    except Exception as e:
        # Manejar errores generales
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error al procesar la solicitud: {str(e)}'})
        }
