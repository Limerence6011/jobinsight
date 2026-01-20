from __future__ import annotations
from typing import Optional
from sqlalchemy import String, Text, Integer, Index, Column

# SQLAlchemy 版本兼容性处理
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
    # SQLAlchemy 2.0 语法
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
else:
    # SQLAlchemy 1.4 语法
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
