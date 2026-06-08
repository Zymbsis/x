from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ProviderKey(StrEnum):
    TWITTERAPI_IO = "twitterapi_io"


class CollectionOptions(BaseModel):
    collect_metadata: bool = True
    collect_data: bool = True
    with_replies: bool = True
    replies_limit: int | None = None
    replies_since: datetime | None = None
    omit_existing_urls: bool = False
    force_collection: bool = False
    max_runtime_sec: int | None = None
    include_media: bool = True
    raw_payloads: bool = True
