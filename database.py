from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.sql import func

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


MY_DB_PATH = 'sqlite:///./evaluations.db'

engine = create_engine(
    MY_DB_PATH, connect_args={'check_same_thread': False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    promptname = Column(String, nullable=True)
    score = Column(Float)
    score_justification = Column(Text)
    sentiment = Column(String)
    sentiment_justification = Column(Text)
    summary = Column(Text)
    improvement_points = Column(Text)
    is_issue_resolved = Column(Boolean, default=False)
    resolution_justification = Column(Text)
    score_evidence = Column(Text)
    sentiment_evidence = Column(Text)
    resolution_evidence = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    followups = relationship("FollowUp", back_populates="evaluation")


class FollowUp(Base):
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    evaluation = relationship("Evaluation", back_populates="followups")


def init_db():
    Base.metadata.create_all(bind=engine)
