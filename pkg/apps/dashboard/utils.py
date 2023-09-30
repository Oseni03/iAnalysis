from django.conf import settings
from .models import Data

import pandas as pd
from pandas.io.json._table_schema import build_table_schema
from google.cloud.bigquery import SchemaField
from sqlalchemy import inspect, create_engine

from langchain import PromptTemplate,SQLDatabase, SQLDatabaseChain
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import SQLDatabaseSequentialChain
from langchain.chat_models import ChatAnthropic, ChatOpenAI
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
from langchain.requests import RequestsWrapper
from langchain.llms.openai import OpenAI
from langchain.agents.agent_toolkits.openapi import planner
from langchain.tools import OpenAPISpec


## For elasticsearch integration
#pip install elasticsearch
from elasticsearch import Elasticsearch
from langchain.chains.elasticsearch_database import ElasticsearchDatabaseChain


def generate_identifier(user: settings.AUTH_USER_MODEL, data: Data):
    return f"{user.id}_{data.id}_{data.protocol}"


def get_schema(conn_str: str):
    """
    This generate a schema of the database engine supplied
    
    param con: sqlalchemy engine object
    
    return: schema dict
    """
    engine = create_engine(conn_str, echo=False)
    inspector = inspect(engine)
    schema = inspector.default_schema_name
    columns_str=''
    for table_name in inspector.get_table_names(schema):
        column_metadata = inspector.get_columns(table_name, schema)
        primary_keys = inspector.get_primary_keys(table_name, schema)
        foreign_keys = inspector.get_foreign_keys(table_name, schema)
        for col in column_metadata:
            name, type = col.get("name"), col.get("type")
            if name in primary_keys:
                name += f"({type})-pk"
            
            if name in [k for k in [key["constrained_columns"]] for idx, key in foreign_keys]:
                fk_table = foreign_keys[idx]["referred_table"] 
                name += f"-fk({fk_table})"
            columns_str=columns_str+f'\n{table_name}|{name}'
    return columns_str


_DEFAULT_TEMPLATE = """
You are an agent designed to interact with a SQL database.\n
Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.\n
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.\n
You can order the results by a relevant column to return the most interesting examples in the database.\n
Never query for all the columns from a specific table, only ask for the relevant columns given the question.\n
You have access to tools for interacting with the database.\n
Only use the below tools. Only use the information returned by the below tools to construct your final answer.\n
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.\n\n
DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.\n\n
If the question does not seem related to the database, just return "I don\'t know" as the answer.\n
"""


def get_db_agent(conn_str, model_name="gpt-3.5-turbo-0613", tables=None):
    """
    Get the SQL database agent to run the query against, 
    which convert "text to sql" and run the query against the db
    """
    
    if tables:
        db = SQLDatabase.from_uri(conn_str, include_tables=tables)
    else:
        db = SQLDatabase.from_uri(conn_str)
    llm = ChatOpenAI(
        temperature=0, 
        model=model_name, 
        openai_api_key=settings.OPENAI_API_KEY,
        max_tokens_to_sample=512
    )
    # llm = ChatAnthropic(temperature=0, anthropic_api_key=settings.ANTHROPIC_API_KEY, max_tokens_to_sample = 512)
    
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    
    agent_executor = create_sql_agent(
        llm=OpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY),
        toolkit=toolkit,
        verbose=True,
        prefix=_DEFAULT_TEMPLATE,
        top_k= 10,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        return_intermediate_steps=True,
        memory=None 
    )
    
    # # Using SQLDatabaseSequentialChain for large number of tables
    # chain = SQLDatabaseSequentialChain.from_llm(llm, db, verbose=True, return_intermediate_steps=True, use_query_checker=True)
    
    # response=agent_executor.run(query)
    return agent_executor


def get_elasticsearch_agent(conn_str, model_name="gpt-3.5-turbo-0613", tables=None):
    # Initialize Elasticsearch python client.
    # See https://elasticsearch-py.readthedocs.io/en/v8.8.2/api.html#elasticsearch.Elasticsearch
    
    # db = Elasticsearch("https://elastic:pass@localhost:9200")
    db = Elasticsearch(conn_str)
    llm = ChatOpenAI(model=model_name, temperature=0)
    chain = ElasticsearchDatabaseChain.from_llm(llm=llm, database=db, verbose=True)
    # response = chain.run(query)
    return chain


def get_api_agent(self, header: dict, model):
    openai_api_spec = OpenAPISpec.from_url(data.spec_url)
    openai_requests_wrapper = RequestsWrapper(headers=header)
    llm = OpenAI(model_name=model, temperature=0.25)
    agent = planner.create_openapi_agent(
        openai_api_spec, 
        openai_requests_wrapper, 
        llm
    )
    return agent


def generate_bigquery_schema(df: pd.DataFrame) -> List[SchemaField]:
    TYPE_MAPPING = {
        "i": "INTEGER",
        "u": "NUMERIC",
        "b": "BOOLEAN",
        "f": "FLOAT",
        "O": "STRING",
        "S": "STRING",
        "U": "STRING",
        "M": "TIMESTAMP",
    }
    schema = []
    for column, dtype in df.dtypes.items():
        val = df[column].iloc[0]
        mode = "REPEATED" if isinstance(val, list) else "NULLABLE"

        if isinstance(val, dict) or (mode == "REPEATED" and isinstance(val[0], dict)):
            fields = generate_bigquery_schema(pd.json_normalize(val))
        else:
            fields = ()

        type = "RECORD" if fields else TYPE_MAPPING.get(dtype.kind)
        schema.append(
            SchemaField(
                name=column,
                field_type=type,
                mode=mode,
                fields=fields,
            )
        )
    return schema