from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Smart_data_syncro.utils import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)