from datetime import datetime, timezone

from sqlalchemy import Text
from sqlmodel import Field, Relationship, SQLModel

from src.ferron.models import VirtualHost


class DashboardFaviconCache(SQLModel, table=True):
    __tablename__ = "fpm_dashboard_favicon_cache"

    id: int | None = Field(default=None, primary_key=True)
    virtual_host_id: int = Field(foreign_key="ferron_virtual_host.id", ondelete="CASCADE", unique=True)
    favicon_data_url: str = Field(sa_type=Text)
    is_placeholder: bool
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    virtual_host: VirtualHost = Relationship()
