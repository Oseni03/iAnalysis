from asgiref.sync import async_to_sync
from celery import shared_task 
from channels.layers import get_channel_layer

# from .services import secrets
# from . import utils
from . import models

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore

User = get_user_model()

session = SessionStore()

@shared_task
def return_query_resp(user_id, data_id):
    user = User.objects.get(id=user_id)
    db = models.Data.objects.get(id=data_id)
    identifier = utils.generate_identifier(user, db)
    
    if identifier not in session:
        username, password = secrets.get_secret_value(identifier)
        conn_str = db.conn_str(username, password)
        
        if db.protocol == models.Data.ProtocolType.ELASTIC_SEARCH:
            agent = utils.get_elasticsearch_agent(conn_str, model, db.tbls)
        else:
            agent = utils.get_db_agent(conn_str, model, db.tbls)
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
    msg.save() # save ai response and sql to the database 
    async_to_sync(channel_layer.group_send)(f"chat_{data_id}", {"type": "chat_message", "msg_id": msg.id})