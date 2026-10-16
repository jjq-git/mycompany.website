"""SQLAlchemy 实例."""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, 'connect')
def _enable_sqlite_fk(dbapi_connection, _connection_record):
    """SQLite 默认 foreign_keys=OFF, 必须每个连接显式开启,
    否则 models.py 里声明的 ondelete='CASCADE' 不会被执行."""
    import sqlite3
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()
