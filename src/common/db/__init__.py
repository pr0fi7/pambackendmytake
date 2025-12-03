# Expose the db_connector module and re-export commonly used names
from . import db_connector as db_connector

# Re-export convenience functions/values
init_db = db_connector.init_db
insert_message = db_connector.insert_message
get_messages = db_connector.get_messages
DB_FILE = db_connector.DB_FILE

__all__ = ["db_connector", "init_db", "insert_message", "get_messages", "DB_FILE"]
