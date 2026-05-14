from sqlmodel import create_engine, Session, SQLModel
from src.core.config import settings

# echo=True 
engine = create_engine(settings.DATABASE_URL, echo=False)

def init_db():
    # sql file 
    SQLModel.metadata.create_all(engine)

def get_session():
    # sesion opne
    with Session(engine) as session:
        yield session