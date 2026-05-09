from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.sql import func

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


 
MY_DB_PATH = 'sqlite:///./evaluations.db'

engine = create_engine(
    MY_DB_PATH, connect_args={'check_same_thread': False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    score = Column(Float) # 1-100
    sentiment = Column(String) # Positive, Neutral, Negative
    summary = Column(Text)
    improvement_points = Column(Text) 
    is_issue_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def init_db():
    Base.metadata.create_all(bind=engine)

