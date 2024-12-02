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

        # Obtener los parámetros obligatorios
        tenant_id = body['tenant_id']  # Obligatorio
        user_id = body['user_id']  # Obligatorio

        # Parámetros opcionales
        email = body.get('email')
        data = body.get('data')

        # Asegúrate de que tenant_id y user_id están presentes
        if not tenant_id or not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'tenant_id and user_id are required'})
            }

        # Preparar la expresión de actualización
        update_expression = "set "
        expression_attribute_values = {}

        # Obtener el token de autorización de los encabezados
        token = event['headers'].get('Authorization')
        if not token:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Authorization token is missing'})
            }

        # Crear el cliente de Lambda para invocar la validación del token
        lambda_client = boto3.client('lambda')

        # Construir la carga útil para validar el token
        payload_string = json.dumps({
            "token": token,
            "tenant_id": tenant_id,
            "user_id": user_id
        })

        # Invocar la función de validación del token
        invoke_response = lambda_client.invoke(
            FunctionName="ValidarTokenAcceso",  # Asegúrate de que el nombre de la función sea correcto
            InvocationType='RequestResponse',
            Payload=payload_string
        )
        
        # Leer la respuesta de la validación del token
        response1 = json.loads(invoke_response['Payload'].read().decode())
        if response1['statusCode'] == 403:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden - Acceso No Autorizado'})
            }

        # Si se proporciona 'data', agregarla al UpdateExpression
        if data:
            update_expression += "#data = :data, "
            expression_attribute_values[':data'] = data
            # Usar alias para 'data' si es una palabra reservada
            expression_attribute_names = {"#data": "data"}
        else:
            expression_attribute_names = {}

        # Si se proporciona 'email', se valida que no exista ya en la base de datos
        if email:
            # Consultar por el email en el índice 'BusquedaPorEmail'
            response = table.query(
                IndexName='BusquedaPorEmail',  # Nombre del índice LSI
                KeyConditionExpression=Key('tenant_id').eq(tenant_id) & Key('email').eq(email)
            )

            # Si el email ya existe, retornar error
            if response['Items']:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Email already exists for this tenant'})
                }

            # Si el email es válido, añadirlo a la expresión de actualización
            update_expression += "email = :email, "
            expression_attribute_values[':email'] = email

        # Eliminar la coma extra al final de la expresión de actualización
        update_expression = update_expression.rstrip(', ')

        # Realizar la actualización en DynamoDB
        response = table.update_item(
            Key={'tenant_id': tenant_id, 'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="UPDATED_NEW"
        )

        # Retornar la respuesta con los atributos actualizados
        return {
            'statusCode': 200,
            'body': json.dumps(response['Attributes'])
        }
    
    except Exception as e:
        # Manejo de errores
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
