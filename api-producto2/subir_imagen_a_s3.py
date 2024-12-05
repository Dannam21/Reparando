import boto3
import base64
import uuid
import os
from datetime import datetime

# Configuración de S3
s3_client = boto3.client('s3')
bucket_name = os.environ['BUCKET_NAME']  # Reemplaza con tu bucket de S3

def lambda_handler(event, context):
    print(event)
    # Obtener los datos del evento (esperamos base64 y nombre de directorio)
    file_base64 = event.get('file_base64')
    directory = event.get('directory', '')  # Directorio opcional
    
    if not file_base64:
        return {
            'statusCode': 400,
            'body': 'Falta el archivo en base64.'
        }
    
    # Decodificar la imagen (o archivo) de base64
    try:
        file_data = base64.b64decode(file_base64)
    except Exception as e:
        return {
            'statusCode': 400,
            'body': f'Error al decodificar el archivo base64: {str(e)}'
        }
    
    # Generar un nombre único para el archivo (utilizando uuid y timestamp)
    unique_filename = f"{uuid.uuid4().hex}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
    
    # Si se recibe un directorio, lo concatenamos al nombre del archivo
    if directory:
        unique_filename = os.path.join(directory, unique_filename)
    
    # Subir el archivo a S3
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=unique_filename,
            Body=file_data,
            ContentType='image/jpeg'  # Puedes cambiar el tipo MIME si es otro tipo de archivo
        )
        
        # Devolver solo el nombre único del archivo
        return {
            'statusCode': 200,
            'body': unique_filename
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error al subir el archivo a S3: {str(e)}'
        }