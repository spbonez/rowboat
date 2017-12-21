import os
import psycogreen.gevent; psycogreen.gevent.patch_psycopg()

from peewee import Proxy, OP, Model
from peewee import Expression
from playhouse.postgres_ext import PostgresqlExtDatabase

REGISTERED_MODELS = []

# Create a database proxy we can setup post-init
database = Proxy()


OP['IRGX'] = 'irgx'


def pg_regex_i(lhs, rhs):
    return Expression(lhs, OP.IRGX, rhs)


PostgresqlExtDatabase.register_ops({OP.IRGX: '~*'})


class BaseModel(Model):
    class Meta:
        database = database

    @staticmethod
    def register(cls):
        REGISTERED_MODELS.append(cls)
        return cls


def init_db(env):
	
    if env == 'docker':
        database.initialize(PostgresqlExtDatabase(
            'rowboat',
            host='db',
            user='postgres',
			register_hstore=False,
            port=int(os.getenv('PG_PORT', 5432)),
            autorollback=True))
    else:
        database.initialize(PostgresqlExtDatabase(
            'rowboat',
            user='rowboat',
            port=int(os.getenv('PG_PORT', 5432)),
			register_hstore=False,
            autorollback=True))

    database.execute_sql('CREATE EXTENSION IF NOT EXISTS pg_trgm;')
    database.execute_sql('CREATE EXTENSION IF NOT EXISTS hstore;')

    for model in REGISTERED_MODELS:
        model.create_table(True)
		
        if hasattr(model, 'SQL'):
            database.execute_sql(model.SQL)


def reset_db():
    init_db()

    for model in REGISTERED_MODELS:
        model.drop_table(True)
        model.create_table(True)
