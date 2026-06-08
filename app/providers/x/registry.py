from typing import Annotated

from fastapi import Depends

from app.providers.x.base import XProvider
from app.providers.x.twitterapi.provider import TwitterApiProviderDep
from app.schemas.x.options import ProviderKey


def get_x_provider(
    _provider_key: ProviderKey,
    twitterapi_provider: TwitterApiProviderDep,
) -> XProvider:
    return twitterapi_provider


XProviderDep = Annotated[XProvider, Depends(get_x_provider)]
