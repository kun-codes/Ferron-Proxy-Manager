import asyncio
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import engine, get_session
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
        await session.rollback()
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


async def _refresh_favicon_cache(
    entry: models.DashboardFaviconCache, local_url: str | None = None
) -> tuple[str, bool, datetime]:
    vh_name = entry.virtual_host.virtual_host_name
    logger.debug("_refresh_favicon_cache: vh='{}', local_url={}", vh_name, local_url)
    favicon_data_url, is_placeholder = await fetch_favicon_payload(vh_name, local_url=local_url)
    logger.info("_refresh_favicon_cache: vh='{}' done, placeholder={}", vh_name, is_placeholder)
    return favicon_data_url, is_placeholder, utcnow()


async def refresh_favicon_for_host(virtual_host_id: int) -> None:
    # using AsyncSession directly instead of get_session() because this is called from background tasks and not
    # request handlers
    logger.info("refresh_favicon_for_host: starting for vh_id={}", virtual_host_id)
    async with AsyncSession(engine) as session:
        vh = await session.get(VirtualHost, virtual_host_id)
        if vh is None:
            logger.warning("refresh_favicon_for_host: vh_id={} not found, skipping", virtual_host_id)
            return

        virtual_host_name = vh.virtual_host_name
        local_url = await resolve_local_favicon_url(session, virtual_host_id)
        logger.info("refresh_favicon_for_host: vh='{}', local_url={}", virtual_host_name, local_url)
        favicon_data_url, is_placeholder = await fetch_favicon_payload(virtual_host_name, local_url=local_url)
        now = utcnow()

        result = await session.exec(
            select(models.DashboardFaviconCache).where(models.DashboardFaviconCache.virtual_host_id == virtual_host_id)
        )
        entry = result.scalar_one_or_none()

        if entry is None:
            entry = models.DashboardFaviconCache(
                virtual_host_id=virtual_host_id,
                favicon_data_url=favicon_data_url,
                is_placeholder=is_placeholder,
                fetched_at=now,
            )
            session.add(entry)
            logger.info(
                "refresh_favicon_for_host: created new cache entry for '{}', placeholder={}",
                virtual_host_name,
                is_placeholder,
            )
        else:
            entry.favicon_data_url = favicon_data_url
            entry.is_placeholder = is_placeholder
            entry.fetched_at = now
            logger.info(
                "refresh_favicon_for_host: updated cache entry for '{}', placeholder={}",
                virtual_host_name,
                is_placeholder,
            )

        await session.commit()
        logger.info("refresh_favicon_for_host: committed for '{}'", virtual_host_name)


async def refresh_all_stale_favicons() -> None:
    # using AsyncSession directly instead of get_session() because this is called from background tasks and not
    # request handlers
    async with AsyncSession(engine) as session:
        cache_result = await session.exec(
            select(models.DashboardFaviconCache).options(selectinload(models.DashboardFaviconCache.virtual_host))
        )
        all_entries = cache_result.scalars().all()
        stale_entries = [
            entry for entry in all_entries if utcnow() - normalize_datetime(entry.fetched_at) >= FAVICON_REFRESH_TTL
        ]

        logger.info("refresh_all_stale_favicons: {} total entries, {} stale", len(all_entries), len(stale_entries))

        if not stale_entries:
            logger.debug("refresh_all_stale_favicons: no stale entries to refresh")
            return

        # Pre-compute local URLs for all stale entries to avoid concurrent session access
        local_urls: dict[int, str | None] = {}
        for entry in stale_entries:
            local_url = await resolve_local_favicon_url(session, entry.virtual_host_id)
            local_urls[entry.virtual_host_id] = local_url

        logger.info("refresh_all_stale_favicons: refreshing {} stale entries...", len(stale_entries))
        refreshed_entries = await asyncio.gather(
            *[
                _refresh_favicon_cache(entry, local_url=local_urls.get(entry.virtual_host_id))
                for entry in stale_entries
            ],
            return_exceptions=True,
        )

        success_count = 0
        error_count = 0
        for entry, refreshed_entry in zip(stale_entries, refreshed_entries, strict=True):
            if isinstance(refreshed_entry, Exception):
                entry.fetched_at = utcnow()
                error_count += 1
                logger.error(
                    "refresh_all_stale_favicons: failed for '{}': {}",
                    entry.virtual_host.virtual_host_name,
                    refreshed_entry,
                )
            else:
                entry.favicon_data_url, entry.is_placeholder, entry.fetched_at = refreshed_entry
                success_count += 1
                logger.debug(
                    "refresh_all_stale_favicons: success for '{}', placeholder={}",
                    entry.virtual_host.virtual_host_name,
                    entry.is_placeholder,
                )

        await session.commit()
        logger.info("refresh_all_stale_favicons: done — {} succeeded, {} failed", success_count, error_count)
