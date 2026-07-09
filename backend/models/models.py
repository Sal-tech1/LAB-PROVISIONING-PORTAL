"""SQLAlchemy ORM models for the lab provisioning portal."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    """Registered portal user with authentication credentials and role."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, server_default="student")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    active_sessions = relationship(
        "ActiveSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class LabTemplate(Base):
    """Reusable container image definition for provisioning lab environments."""

    __tablename__ = "lab_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    image_tag = Column(String(200), nullable=False)
    cpu_limit = Column(String(10), nullable=False, server_default="0.5")
    ram_limit = Column(String(10), nullable=False, server_default="256m")
    description = Column(Text, nullable=True)

    active_sessions = relationship("ActiveSession", back_populates="template")


class ActiveSession(Base):
    """Running or historical lab container session tied to a user and template."""

    __tablename__ = "active_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_id = Column(
        Integer,
        ForeignKey("lab_templates.id"),
        nullable=False,
    )
    container_id = Column(String(100), nullable=False)
    port = Column(Integer, unique=True, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), nullable=False, server_default="running")

    user = relationship("User", back_populates="active_sessions")
    template = relationship("LabTemplate", back_populates="active_sessions")
