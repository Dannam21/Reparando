import boto3
import json
from datetime import datetime

# Inicializar el cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')
TOKENS_TABLE = 't_tokens_acceso'
tokens_table = dynamodb.Table(TOKENS_TABLE)

def lambda_handler(event, context):
    try:
        # Log del evento recibido
        print("Evento recibido:", json.dumps(event))

        # Obtener los parámetros según la estructura del evento
        params = event.get('queryStringParameters') or event

        # Extraer parámetros relevantes
        token = params.get('token')
        role = params.get('role')
        tenant_id = params.get('tenant_id')
        user_id = params.get('user_id')

        # Validar que se envió el token
        if not token:
            print("Falta el token en los parámetros")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'El parámetro "token" es obligatorio'})
            }

        # Consultar el registro del token en DynamoDB
        response = tokens_table.get_item(Key={'token': token})
        item = response.get('Item')

        # Validar si el token existe
        if not item:
            print(f"Token no encontrado: {token}")
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Token no válido'})
            }

        # Imprimir el token recuperado para depuración
        print("Registro del token:", item)

        # Verificar si el token ha expirado
        expires = datetime.strptime(item['expires'], '%Y-%m-%d %H:%M:%S')
        if datetime.utcnow() > expires:
            print(f"Token expirado: {item['expires']}")
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Token expirado'})
            }

        # Validar el rol si no es "admin"
        if item['role'] != "admin":
            print(f"Validando como usuario con rol: {item['role']}")
            
            # Si se proporciona "role", validar
            if role:
                if role != item['role']:
                    print(f"El rol proporcionado no coincide: {role} vs {item['role']}")
                    return {
                        'statusCode': 403,
                        'body': json.dumps({'error': f'Token no válido para el rol: {role}'})
                    }

            # Si se proporciona "tenant_id" y "user_id", validar
            elif tenant_id and user_id:
                if tenant_id != item.get("tenant_id") or user_id != item.get("user_id"):
                    print("Tenant ID o User ID no coinciden")
                    return {
                        'statusCode': 403,
                        'body': json.dumps({'error': 'Token no válido para el tenant_id y user_id proporcionados'})
                    }

            # Si no se proporciona ni "role" ni "tenant_id/user_id", devolver error
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Debe enviar al menos role o tenant_id y user_id'})
                }

        # Token válido
        print("Token válido:", item)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Token válido'})
        }

    except Exception as e:
        # Manejo de errores generales
        print("Error en la ejecución:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error interno del servidor', 'details': str(e)})
        }
