import boto3
import os
import json
from boto3.dynamodb.conditions import Key

# Configuración de DynamoDB
dynamodb = boto3.resource('dynamodb')
USERS_TABLE = os.environ['USERS_TABLE']
table = dynamodb.Table(USERS_TABLE)

def lambda_handler(event, context):
    try:
        # Parsear el cuerpo de la solicitud
        body = json.loads(event['body'])
        tenant_id = body.get('tenant_id')
        user_id = body.get('user_id')
        email = body.get('email')
        
        # Obtener el token de autorización de los encabezados
        token = event['headers'].get('Authorization')

        # Crear el cliente de Lambda para invocar la función de validación del token
        lambda_client = boto3.client('lambda')

        # Verificar si tenemos tenant_id y user_id
        if tenant_id and user_id:
            payload = {
                "token": token,
                "tenant_id": tenant_id,
                "user_id": user_id
            }

            # Invocar la función de validación del token
            invoke_response = lambda_client.invoke(
                FunctionName="ValidarTokenAcceso",  # Asegúrate de que este sea el nombre correcto
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            # Leer la respuesta de la función de validación
            response1 = json.loads(invoke_response['Payload'].read().decode())
            
            # Imprimir la respuesta para depuración
            print(f"Response from ValidarTokenAcceso: {response1}")

            # Verificar si la respuesta tiene el statusCode
            if 'statusCode' not in response1:
                raise Exception("Invalid response structure: 'statusCode' not found")

            if response1['statusCode'] == 403:
                return {
                    'statusCode': 403,
                    'body': json.dumps({'error': 'Forbidden - Acceso No Autorizado'})
                }

        # Si tenemos tenant_id y email, usamos otro índice en DynamoDB
        elif tenant_id and email:
            response = table.query(
                IndexName='BusquedaPorEmail',  # El nombre del índice LSI
                KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('email').eq(email)
            )

            # Verificar si encontramos el usuario por email
            if len(response.get('Items', [])) > 0:
                user_item = response['Items'][0]
                user_id = user_item['user_id'] 
                payload = {
                    "token": token,
                    "tenant_id": user_item['tenant_id'],
                    "user_id": user_item['user_id']
                }

                # Invocar la función de validación del token
                invoke_response = lambda_client.invoke(
                    FunctionName="ValidarTokenAcceso",
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )

                response1 = json.loads(invoke_response['Payload'].read().decode())
                print(f"Response from ValidarTokenAcceso: {response1}")
                
                # Verificar si la respuesta tiene el statusCode
                if 'statusCode' not in response1:
                    raise Exception("Invalid response structure: 'statusCode' not found")

                if response1['statusCode'] == 403:
                    return {
                        'statusCode': 403,
                        'body': json.dumps({'error': 'Forbidden - Acceso No Autorizado'})
                    }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Usuario no encontrado'})
                }

        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Debe proporcionar tenant_id y user_id o tenant_id y email'})
            }

        # Si el usuario ha sido validado y se encuentra, proceder a eliminarlo
        response = table.delete_item(
            Key={'tenant_id': tenant_id, 'user_id': user_id}
        )

        # Verificar si la eliminación fue exitosa
        return {
            'statusCode': 204,
            'body': json.dumps({'message': 'Usuario eliminado exitosamente'})
        }

    except Exception as e:
        # Manejo de errores
        print(f"Error: {str(e)}")  # Agregar impresión para diagnóstico
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
