import boto3
import logging
import os
from datetime import datetime, timedelta

# Configuración del cliente S3
s3_client = boto3.client('s3')
bucket_name = os.environ['BUCKET_NAME']

def lambda_handler(event, context):
    print(event)
    # Obtener el nombre de la imagen y el nombre del bucket desde el evento
    object_name = event.get('object_name')  # El nombre del objeto (imagen) en S3
    if not object_name:
        return {
            'statusCode': 400,
            'body': 'Falta el object_name.'
        }

    # Generar una URL firmada que sea válida por 1 hora
    try:
        # Establecer el tiempo de expiración (1 hora)
        expiration = 3600  # en segundos (3600 segundos = 1 hora)
        
        # Generar la URL firmada
        url = s3_client.generate_presigned_url('get_object',
                                               Params={'Bucket': bucket_name, 'Key': object_name},
                                               ExpiresIn=expiration)
        
        return {
            'statusCode': 200,
            'url': url
        }

    except Exception as e:
        logging.error(f"Error al generar la URL firmada: {e}")
        return {
            'statusCode': 500,
            'body': {
                'message': 'Error generando la URL firmada',
                'error': str(e)
            }
        }