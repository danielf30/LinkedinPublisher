import json
import boto3
from botocore.exceptions import ClientError
from linkedin_api.clients.restli.client import RestliClient

def lambda_handler(event, context):    
    # Recuperar la clave API de OpenAI desde AWS Secrets Manager
    secret_name = "linkedin_access_token"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    secret = json.loads(secret)
    ACCESS_TOKEN = secret.get(secret_name)

    ME_RESOURCE = "/me"
    UGC_POSTS_RESOURCE = "/ugcPosts"

    restli_client = RestliClient()
    restli_client.session.hooks["response"].append(lambda r, *args, **kwargs: r.raise_for_status())

    # Obtener el ID del usuario de LinkedIn
    me_response = restli_client.get(resource_path=ME_RESOURCE, access_token=ACCESS_TOKEN)
    person_urn = me_response.entity['id']

    # Obtener el contenido generado por OpenAI desde el evento
    #content = event

    # Construir el texto de la publicación
    # post_text = f"{content['Título']}\n\n{content['Resumen']}\n\n{content['Enlace']}\n\n{content['Hashtags']}"
    post_text = event.get('message', '')
    if not post_text:
        return {'error': 'No se proporcionó ningún enlace.'}

    # Crear la publicación en LinkedIn
    try:
        ugc_posts_create_response = restli_client.create(
            resource_path=UGC_POSTS_RESOURCE,
            entity={
    