from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Text, Integer, Index, Column, DateTime, Boolean

# SQLAlchemy version compatibility
try:
    # SQLAlchemy 2.0+
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    class Base(DeclarativeBase):
        pass
    USE_V2_SYNTAX = True
except ImportError:
    # SQLAlchemy 1.4
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    USE_V2_SYNTAX = False

if USE_V2_SYNTAX:
    # SQLAlchemy 2.0 syntax
    class Job(Base):
        __tablename__ = "jobs"

        platform: Mapped[str] = mapped_column(String(32), primary_key=True)
        job_id: Mapped[str] = mapped_column(String(128), primary_key=True)

        title: Mapped[str] = mapped_column(String(256))
        company: Mapped[str] = mapped_column(String(256))
        city: Mapped[str] = mapped_column(String(128))

        salary_raw: Mapped[str] = mapped_column(String(128))
        salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
        salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
        salary_avg: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
        salary_unit_note: Mapped[str] = mapped_column(String(64), default="unknown")

        education: Mapped[str] = mapped_column(String(32), default="Unknown")
        exp: Mapped[str] = mapped_column(String(32), default="Unknown")

        tags: Mapped[str] = mapped_column(Text)  # JSON string
        detail_url: Mapped[str] = mapped_column(Text)
        description: Mapped[str] = mapped_column(Text)

        crawl_date: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD

        __table_args__ = (
            Index("idx_city_date", "city", "crawl_date"),
            Index("idx_title", "title"),
        )

    class User(Base):
        __tablename__ = "users"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
        email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
        password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
        created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
        is_active: Mapped[bool] = mapped_column(Boolean, default=True)
        is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    class AppSetting(Base):
        __tablename__ = "app_settings"

        key: Mapped[str] = mapped_column(String(128), primary_key=True)
        value: Mapped[str] = mapped_column(String(512), nullable=False)
        updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
else:
    # SQLAlchemy 1.4 syntax
    class Job(Base):
        __tablename__ = "jobs"

        platform = Column(String(32), primary_key=True)
        job_id = Column(String(128), primary_key=True)

        title = Column(String(256))
        company = Column(String(256))
        city = Column(String(128))

        salary_raw = Column(String(128))
        salary_min = Column(Integer, nullable=True)
        salary_max = Column(Integer, nullable=True)
        salary_avg = Column(Integer, nullable=True)
        salary_unit_note = Column(String(64), default="unknown")

        education = Column(String(32), default="Unknown")
        exp = Column(String(32), default="Unknown")

        tags = Column(Text)  # JSON string
        detail_url = Column(Text)
        description = Column(Text)

        crawl_date = Column(String(10))  # YYYY-MM-DD

        __table_args__ = (
            Index("idx_city_date", "city", "crawl_date"),
            Index("idx_title", "title"),
        )

    class User(Base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(String(64), unique=True, nullable=False)
        email = Column(String(128), unique=True, nullable=False)
        password_hash = Column(String(256), nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        is_active = Column(Boolean, default=True)
        is_admin = Column(Boolean, default=False)

    class AppSetting(Base):
        __tablename__ = "app_settings"

        key = Column(String(128), primary_key=True)
        value = Column(String(512), nullable=False)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
