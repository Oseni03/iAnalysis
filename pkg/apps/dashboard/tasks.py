from asgiref.sync import async_to_sync
from celery import shared_task 
from channels.layers import get_channel_layer

# from langchain.callbacks import get_openai_callback

# from .services import secrets
# from . import utils
from . import models

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore

User = get_user_model()

session = SessionStore()

@shared_task
def return_query_resp(query, user_id, data_id, model):
    user = User.objects.get(id=user_id)
    data = models.Data.objects.get(id=data_id)
    identifier = utils.generate_identifier(user, data)
    
    if identifier not in session:
        if data.is_db:
            username, password = secrets.get_secret_value(identifier)
            conn_str = data.conn_str(username, password)
            
            if data.protocol == models.Data.ProtocolType.ELASTIC_SEARCH:
                agent = utils.get_elasticsearch_agent(conn_str, model, data.tbls)
            else:
                agent = utils.get_db_agent(conn_str, model, data.tbls)
        elif data.is_api:
            agent = utils.get_api_agent(
                header=json.load(data.header), 
                model=model
            )
        session[identifier] = agent
    else:
        agent = session.get(identifier)
    
    with get_openai_callback() as cb:
        response = agent.run(query)
        models.Usage.objects.create(
            prompt_tokens=cb.prompt_tokens,
            total_tokens=cb.total_tokens,
            completion_tokens=cb.completion_tokens,
            total_cost=cb.total_cost,
        )
        
    result = response["result"]
    msg = models.Message.objects.create(
        source=data, 
        text=result, 
        sql_query=response["intermediate_steps"][-2],
        is_ai=True
    )
    msg.save() # save ai response and sql to the database 
    async_to_sync(channel_layer.group_send)(f"chat_{data_id}", {"type": "chat_message", "msg_id": msg.id})
    return result