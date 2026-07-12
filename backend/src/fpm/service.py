import asyncio
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import engine, get_session
from src.ferron.exceptions import ConfigNotFound
from src.ferron.models import VirtualHost
from src.fpm import models, schemas
from src.fpm.constants import FAVICON_REFRESH_TTL
from src.fpm.utils import build_target_url, fetch_favicon_payload, normalize_datetime, resolve_local_favicon_url, utcnow


async def read_dashboard_hosts(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[schemas.DashboardHost]:
    vh_result = await session.exec(select(VirtualHost).order_by(VirtualHost.virtual_host_name))
    virtual_hosts = vh_result.scalars().all()

    if not virtual_hosts:
        return []

    vh_ids = [vh.id for vh in virtual_hosts]
    try:
        cache_result = await session.exec(
            select(models.DashboardFaviconCache).where(models.DashboardFaviconCache.virtual_host_id.in_(vh_ids))
        )
        cached_entries = cache_result.scalars().all()
    except SQLAlchemyError:
        cached_entries = []

    cache_by_vh_id = {entry.virtual_host_id: entry for entry in cached_entries}

    result = []
    for vh in virtual_hosts:
        cache = cache_by_vh_id.get(vh.id)

        result.append(
            schemas.DashboardHost(
                virtual_host_name=vh.virtual_host_name,
                target_url=build_target_url(vh.virtual_host_name),
                favicon_data_url=cache.favicon_data_url if cache else "",
                is_placeholder=cache is None or cache.is_placeholder,
                fetched_at=cache.fetched_at if cache else utcnow(),
            )
        )

    return result


async def read_host_favicon(
    session: AsyncSession,
    virtual_host_name: str,
) -> schemas.DashboardHost:
    vh_result = await session.exec(select(VirtualHost).where(VirtualHost.virtual_host_name == virtual_host_name))
    vh = vh_result.scalar_one_or_none()

    if vh is None:
        raise ConfigNotFound(config_type="virtual host")

    cache_result = await session.exec(
        select(models.DashboardFaviconCache).where(models.DashboardFaviconCache.virtual_host_id == vh.id)
    )
    cache = cache_result.scalar_one_or_none()

    return schemas.DashboardHost(
        virtual_host_name=vh.virtual_host_name,
        target_url=build_target_url(vh.virtual_host_name),
        favicon_data_url=cache.favicon_data_url if cache else "",
        is_placeholder=cache is None or cache.is_placeholder,
        fetched_at=cache.fetched_at if cache else utcnow(),
    )


async def _refresh_favicon_cache(
    entry: models.DashboardFaviconCache, local_url: str | None = None
) -> tuple[str, bool, datetime]:
    favicon_data_url, is_placeholder = await fetch_favicon_payload(
        entry.virtual_host.virtual_host_name, local_url=local_url
    )
    return favicon_data_url, is_placeholder, utcnow()


async def refresh_favicon_for_host(virtual_host_id: int) -> None:
    # using AsyncSession directly instead of get_session() because this is called from background tasks and not
    # request handlers
    async with AsyncSession(engine) as session:
        vh = await session.get(VirtualHost, virtual_host_id)
        if vh is None:
            return

        result = await session.exec(
            select(models.DashboardFaviconCache).where(models.DashboardFaviconCache.virtual_host_id == virtual_host_id)
        )
        entry = result.scalar_one_or_none()

        # clear existing image so the frontend shows Globe during the refresh. This is done
        # like this so the polling in frontend dashboard route automatically knows that it
        # should poll for the new favicon after updating a config
        virtual_host_name = vh.virtual_host_name
        if entry is not None:
            entry.favicon_data_url = ""
            entry.is_placeholder = True
            await session.commit()

        local_url = await resolve_local_favicon_url(session, virtual_host_id)
        favicon_data_url, is_placeholder = await fetch_favicon_payload(virtual_host_name, local_url=local_url)
        now = utcnow()

        if entry is None:
            entry = models.DashboardFaviconCache(
                virtual_host_id=virtual_host_id,
                favicon_data_url=favicon_data_url,
                is_placeholder=is_placeholder,
                fetched_at=now,
            )
            session.add(entry)
        else:
            entry.favicon_data_url = favicon_data_url
            entry.is_placeholder = is_placeholder
            entry.fetched_at = now

        await session.commit()


async def refresh_all_stale_favicons() -> None:
    # using AsyncSession directly instead of get_session() because this is called from background tasks and not
    # request handlers
    async with AsyncSession(engine) as session:
        cache_result = await session.exec(
            select(models.DashboardFaviconCache).options(selectinload(models.DashboardFaviconCache.virtual_host))
        )
        stale_entries = [
            entry
            for entry in cache_result.scalars().all()
            if utcnow() - normalize_datetime(entry.fetched_at) >= FAVICON_REFRESH_TTL
        ]

        if not stale_entries:
            return

        # Pre-compute local URLs for all stale entries to avoid concurrent session access
        local_urls: dict[int, str | None] = {}
        for entry in stale_entries:
            local_url = await resolve_local_favicon_url(session, entry.virtual_host_id)
            local_urls[entry.virtual_host_id] = local_url

        refreshed_entries = await asyncio.gather(
            *[
                _refresh_favicon_cache(entry, local_url=local_urls.get(entry.virtual_host_id))
                for entry in stale_entries
            ],
            return_exceptions=True,
        )

        for entry, refreshed_entry in zip(stale_entries, refreshed_entries, strict=True):
            if isinstance(refreshed_entry, Exception):
                entry.fetched_at = utcnow()
            else:
                entry.favicon_data_url, entry.is_placeholder, entry.fetched_at = refreshed_entry

        await session.commit()
