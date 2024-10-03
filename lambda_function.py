import os
import json
import boto3
from linkedin_api.clients.restli.client import RestliClient

def lambda_handler(event, context):
    # Recuperar el token de acceso de LinkedIn desde AWS Secrets Manager
    secrets_client = boto3.client('secretsmanager')
    secret = secrets_client.get_secret_value(SecretId='linkedin_access_token')
    ACCESS_TOKEN = secret['SecretString']

    ME_RESOURCE = "/me"
    UGC_POSTS_RESOURCE = "/ugcPosts"

    restli_client = RestliClient()
    restli_client.session.hooks["response"].append(lambda r, *args, **kwargs: r.raise_for_status())

    # Obtener el ID del usuario de LinkedIn
    me_response = restli_client.get(resource_path=ME_RESOURCE, access_token=ACCESS_TOKEN)
    person_urn = me_response.entity['id']

    # Obtener el contenido generado por OpenAI desde el evento
    content = event

    # Construir el texto de la publicación
    post_text = f"{content['Título']}\n\n{content['Resumen']}\n\n{content['Enlace']}\n\n{content['Hashtags']}"

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
