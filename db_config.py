import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set up SQLAlchemy with the declarative base
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)