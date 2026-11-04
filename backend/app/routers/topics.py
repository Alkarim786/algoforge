from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Problem, Topic
from app.schemas import TopicCreate, TopicDetail, TopicSummary, TopicUpdate
from app.security import require_admin

router = APIRouter(prefix="/topics", tags=["topics"])
DbSession = Annotated[Session, Depends(get_db)]


def get_topic_or_404(db: Session, slug: str) -> Topic:
    topic = db.scalar(
        select(Topic).where(Topic.slug == slug).options(selectinload(Topic.problems).joinedload(Problem.topic))
    )
    if topic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topic not found")
    return topic


@router.get("", response_model=list[TopicSummary])
def list_topics(db: DbSession) -> list[Topic]:
    return list(db.scalars(select(Topic).order_by(Topic.order, Topic.id)))


@router.get("/{slug}", response_model=TopicDetail)
def get_topic(slug: str, db: DbSession) -> Topic:
    return get_topic_or_404(db, slug)


@router.post("", response_model=TopicDetail, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_topic(payload: TopicCreate, db: DbSession) -> Topic:
    topic = Topic(**payload.model_dump())
    db.add(topic)
    db.commit()
    return get_topic_or_404(db, topic.slug)


@router.patch("/{slug}", response_model=TopicDetail, dependencies=[Depends(require_admin)])
def update_topic(slug: str, payload: TopicUpdate, db: DbSession) -> Topic:
    topic = get_topic_or_404(db, slug)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    db.commit()
    return topic


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_topic(slug: str, db: DbSession) -> None:
    topic = get_topic_or_404(db, slug)
    if topic.problems:
        raise HTTPException(status.HTTP_409_CONFLICT, "Topic still has problems; move or delete them first")
    db.delete(topic)
    db.commit()
