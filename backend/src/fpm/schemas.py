from datetime import datetime

from pydantic import BaseModel


class DashboardHost(BaseModel):
    virtual_host_name: str
    target_url: str
    favicon_data_url: str
    is_placeholder: bool
    fetched_at: datetime
