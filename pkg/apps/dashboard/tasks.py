from asgiref.sync import async_to_sync
from celery import shared_task 
from channels.layers import get_channel_layer
# from .utils import get_elasticsearch_agent, get_db_agent
# from .services import secrets

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from . import models

User = get_user_model()

session = SessionStore()

@shared_task
def return_query_resp(user_id, data_id):
    user = User.objects.get(id=user_id)
    db = models.Database.objects.get(id=data_id)
    identifier = generate_identifier(user, db)
    
    if identifier not in session:
        username, password = secrets.get_secret_value(identifier)
        conn_str = db.conn_str(username, password)
        
        if db.protocol == models.Database.ProtocolType.ELASTIC_SEARCH:
            agent = get_elasticsearch_agent(conn_str, model, db.tbls)
        else:
            agent = get_db_agent(conn_str, model, db.tbls)
        session[identifier] = agent
    else:
        agent = session.get(identifier)
    
    response = agent.run(query)
    result = response["result"]
    msg = models.Message.objects.create(
        db=db, 
        text=result, 
        sql_query=response["intermediate_steps"][-2],
        is_ai=True
    )
    msg.save()# save ai response and sql to the database 
    async_to_sync(channel_layer.group_send)(f"chat_{data_id}", {"type": "chat_message", "msg_id": msg.id})