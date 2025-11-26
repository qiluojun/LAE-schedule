import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 优先使用环境变量 DATABASE_URL（云端模式），否则使用本地 SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # 云端模式：使用 PostgreSQL
    # Vercel/Supabase 可能提供 postgres:// 开头的 URL，需要替换为 postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # PostgreSQL 不需要 check_same_thread 参数
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # 自动检测连接是否有效
        pool_recycle=300,    # 5分钟回收连接，避免超时
    )
else:
    # 本地模式：使用 SQLite
    DATABASE_URL = "sqlite:///data/lae_schedule.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()