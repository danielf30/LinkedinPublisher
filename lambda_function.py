import json
import boto3
from botocore.exceptions import ClientError
from linkedin_api.clients.restli.client import RestliClient

def lambda_handler(event, context):    
    # Recuperar la clave API de OpenAI desde AWS Secrets Manager
    secret_name = "linkedin_access_token"
    region_name = "us-east-1"

    # Crear un cliente de Secrets Manager
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
        # Manejar excepciones de Secrets Manager
        raise e

    secret = get_secret_value_response['SecretString']
    secret = json.loads(secret)
    ACCESS_TOKEN = secret.get(secret_name)

    ME_RESOURCE = "/userinfo"
    UGC_POSTS_RESOURCE = "/ugcPosts"

    restli_client = RestliClient()
    restli_client.session.hooks["response"].append(lambda r, *args, **kwargs: r.raise_for_status())

    # Obtener el ID del usuario de LinkedIn
    me_response = restli_client.get(resource_path=ME_RESOURCE, access_token=ACCESS_TOKEN)
    person_urn = me_response.entity['sub']

    
    output_json = json.loads(event['InputString'])
    post_text = output_json.get('message', '')
    if not post_text:
        return {'error': 'No se proporcionó ningún enlace.'}

    # Crear la publicación en LinkedIn
    try:
        ugc_posts_create_response = restli_client.create(
            resource_path=UGC_POSTS_RESOURCE,
            entity={
                "author": f"urn:li:person:{person_urn}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": post_text
                        },
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            },
            access_token=ACCESS_TOKEN,
        )
        return {'message': 'Publicación exitosa en LinkedIn.'}
    except Exception as e:
        return {'error': str(e)}

## Simular la ejecución local con un evento de prueba
#if __name__ == "__main__":
#    # Crear un evento simulado
#    event = {
#        "message": "Test Message"
#    }
#
#    # Ejecutar la función Lambda con el evento simulado
#    result = lambda_handler(event, context=None)
#    
#    # Imprimir el resultado de la ejecución
#    print(result)