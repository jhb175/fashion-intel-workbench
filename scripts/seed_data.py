#!/usr/bin/env python
"""Seed data script.

Insert preset monitor groups, a preset OpenAI AI provider, and sample brand
and keyword data.

Usage (from project root):
    python scripts/seed_data.py
"""

import asyncio
import os
import sys

# ---------------------------------------------------------------------------
# Ensure the backend package is importable
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from cryptography.fernet import Fernet
from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.models.ai_provider import AIProvider
from app.models.brand import Brand
from app.models.keyword import Keyword
from app.models.monitor_group import MonitorGroup
from app.models.user import User

# ---------------------------------------------------------------------------
# Preset data definitions
# ---------------------------------------------------------------------------

MONITOR_GROUPS = [
    {
        "name": "Luxury",
        "display_name": "奢侈品",
        "description": "全球顶级奢侈品牌动态，涵盖高级时装、皮具、珠宝腕表等领域",
        "sort_order": 1,
    },
    {
        "name": "Sports",
        "display_name": "运动",
        "description": "运动品牌与运动时尚资讯，涵盖球鞋、运动装备、运动联名等领域",
        "sort_order": 2,
    },
    {
        "name": "Outdoor",
        "display_name": "户外",
        "description": "户外品牌与山系时尚资讯，涵盖功能性服饰、户外装备、Gorpcore 等领域",
        "sort_order": 3,
    },
    {
        "name": "Rap/Culture",
        "display_name": "说唱/文化",
        "description": "说唱文化与街头潮流资讯，涵盖街头品牌、说唱歌手品牌、亚文化时尚等领域",
        "sort_order": 4,
    },
]

# brand data keyed by monitor group name
BRANDS_BY_GROUP: dict[str, list[dict]] = {
    "Luxury": [
        {
            "name_zh": "路易威登",
            "name_en": "Louis Vuitton",
            "official_name": "LOUIS VUITTON",
            "social_media_name": "Louis Vuitton",
            "naming_notes": "全大写",
        },
        {
            "name_zh": "古驰",
            "name_en": "Gucci",
            "official_name": "GUCCI",
            "social_media_name": "Gucci",
            "naming_notes": "全大写",
        },
        {
            "name_zh": "迪奥",
            "name_en": "Dior",
            "official_name": "DIOR",
            "social_media_name": "Dior",
            "naming_notes": "全大写",
        },
        {
            "name_zh": "巴黎世家",
            "name_en": "Balenciaga",
            "official_name": "BALENCIAGA",
            "social_media_name": "Balenciaga",
            "naming_notes": "全大写",
        },
        {
            "name_zh": "普拉达",
            "name_en": "Prada",
            "official_name": "PRADA",
            "social_media_name": "Prada",
            "naming_notes": "全大写",
        },
    ],
    "Sports": [
        {
            "name_zh": "耐克",
            "name_en": "Nike",
            "official_name": "Nike",
            "social_media_name": "Nike",
            "naming_notes": "首字母大写",
        },
        {
            "name_zh": "阿迪达斯",
            "name_en": "adidas",
            "official_name": "adidas",
            "social_media_name": "adidas",
            "naming_notes": "全小写",
        },
        {
            "name_zh": "新百伦",
            "name_en": "New Balance",
            "official_name": "New Balance",
            "social_media_name": "New Balance",
            "naming_notes": "每个单词首字母大写",
        },
        {
            "name_zh": "彪马",
            "name_en": "Puma",
            "official_name": "PUMA",
            "social_media_name": "PUMA",
            "naming_notes": "全大写",
        },
    ],
    "Outdoor": [
        {
            "name_zh": "北面",
            "name_en": "The North Face",
            "official_name": "The North Face",
            "social_media_name": "The North Face",
            "naming_notes": "每个单词首字母大写",
        },
        {
            "name_zh": "始祖鸟",
            "name_en": "Arc'teryx",
            "official_name": "Arc'teryx",
            "social_media_name": "Arc'teryx",
            "naming_notes": "注意撇号和小写 t",
        },
        {
            "name_zh": "巴塔哥尼亚",
            "name_en": "Patagonia",
            "official_name": "Patagonia",
            "social_media_name": "Patagonia",
            "naming_notes": "首字母大写",
        },
        {
            "name_zh": "萨洛蒙",
            "name_en": "Salomon",
            "official_name": "Salomon",
            "social_media_name": "Salomon",
            "naming_notes": "首字母大写",
        },
    ],
    "Rap/Culture": [
        {
            "name_zh": "Supreme",
            "name_en": "Supreme",
            "official_name": "Supreme",
            "social_media_name": "Supreme",
            "naming_notes": "首字母大写",
        },
        {
            "name_zh": "BAPE",
            "name_en": "A Bathing Ape",
            "official_name": "A BATHING APE®",
            "social_media_name": "BAPE",
            "naming_notes": "全大写，官方全称含 ® 符号",
        },
        {
            "name_zh": "Stüssy",
            "name_en": "Stüssy",
            "official_name": "Stüssy",
            "social_media_name": "Stussy",
            "naming_notes": "注意 ü 字符",
        },
        {
            "name_zh": "Palace",
            "name_en": "Palace",
            "official_name": "Palace Skateboards",
            "social_media_name": "Palace",
            "naming_notes": "首字母大写",
        },
    ],
}

KEYWORDS_BY_GROUP: dict[str, list[dict]] = {
    "Luxury": [
        {"word_zh": "联名", "word_en": "collaboration"},
        {"word_zh": "高定", "word_en": "haute couture"},
        {"word_zh": "秀场", "word_en": "runway"},
        {"word_zh": "新品", "word_en": "new release"},
    ],
    "Sports": [
        {"word_zh": "球鞋", "word_en": "sneakers"},
        {"word_zh": "联名", "word_en": "collaboration"},
        {"word_zh": "复刻", "word_en": "retro"},
        {"word_zh": "运动装备", "word_en": "sportswear"},
    ],
    "Outdoor": [
        {"word_zh": "山系", "word_en": "gorpcore"},
        {"word_zh": "机能", "word_en": "techwear"},
        {"word_zh": "户外装备", "word_en": "outdoor gear"},
        {"word_zh": "联名", "word_en": "collaboration"},
    ],
    "Rap/Culture": [
        {"word_zh": "街头", "word_en": "streetwear"},
        {"word_zh": "限量", "word_en": "limited edition"},
        {"word_zh": "说唱", "word_en": "hip-hop"},
        {"word_zh": "涂鸦", "word_en": "graffiti"},
    ],
}


def _encrypt_placeholder_key(placeholder: str) -> str:
    """Encrypt a placeholder API key using the configured encryption key.

    If the configured ENCRYPTION_KEY is not a valid Fernet key (e.g. the
    default "change-me-in-production"), generate a temporary Fernet key so
    the seed script can still run.
    """
    key = settings.ENCRYPTION_KEY
    try:
        f = Fernet(key.encode("utf-8") if isinstance(key, str) else key)
    except (ValueError, Exception):
        # Fallback: generate a one-time key for seeding purposes
        f = Fernet(Fernet.generate_key())
    return f.encrypt(placeholder.encode("utf-8")).decode("utf-8")


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------


async def seed_monitor_groups(session) -> dict[str, MonitorGroup]:
    """Insert preset monitor groups. Returns a name → MonitorGroup mapping."""
    print("[seed] Seeding monitor groups …")
    group_map: dict[str, MonitorGroup] = {}

    for data in MONITOR_GROUPS:
        stmt = select(MonitorGroup).where(MonitorGroup.name == data["name"])
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            print(f"  • {data['name']} ({data['display_name']}) — already exists, skipping.")
            group_map[data["name"]] = existing
            continue

        group = MonitorGroup(**data)
        session.add(group)
        await session.flush()  # populate id
        group_map[data["name"]] = group
        print(f"  ✓ {data['name']} ({data['display_name']})")

    return group_map


async def seed_ai_provider(session) -> None:
    """Insert the preset OpenAI AI provider."""
    print("[seed] Seeding preset OpenAI AI provider …")

    # We need an admin user to associate the provider with
    stmt = select(User).where(User.username == "admin")
    admin = (await session.execute(stmt)).scalar_one_or_none()
    if admin is None:
        print("  ⚠ Admin user not found. Run init_db.py first.")
        return

    stmt = select(AIProvider).where(
        AIProvider.name == "OpenAI",
        AIProvider.is_preset == True,  # noqa: E712
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        print("  • OpenAI preset provider already exists — skipping.")
        return

    encrypted_key = _encrypt_placeholder_key("sk-placeholder-replace-with-real-key")

    provider = AIProvider(
        user_id=admin.id,
        name="OpenAI",
        api_key_encrypted=encrypted_key,
        api_base_url="https://api.openai.com/v1",
        model_name="gpt-4o",
        is_preset=True,
        is_active=True,
    )
    session.add(provider)
    await session.flush()
    print("  ✓ OpenAI (preset, active)")


async def seed_brands(
    session,
    group_map: dict[str, MonitorGroup],
) -> None:
    """Insert sample brands for each monitor group."""
    print("[seed] Seeding brands …")

    for group_name, brands in BRANDS_BY_GROUP.items():
        group = group_map.get(group_name)
        if group is None:
            print(f"  ⚠ Monitor group '{group_name}' not found — skipping brands.")
            continue

        for data in brands:
            stmt = select(Brand).where(
                Brand.name_en == data["name_en"],
                Brand.monitor_group_id == group.id,
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing is not None:
                print(f"  • {data['name_en']} ({group_name}) — already exists, skipping.")
                continue

            brand = Brand(monitor_group_id=group.id, **data)
            session.add(brand)
            print(f"  ✓ {data['name_en']} ({group_name})")

    await session.flush()


async def seed_keywords(
    session,
    group_map: dict[str, MonitorGroup],
) -> None:
    """Insert sample keywords for each monitor group."""
    print("[seed] Seeding keywords …")

    for group_name, keywords in KEYWORDS_BY_GROUP.items():
        group = group_map.get(group_name)
        if group is None:
            print(f"  ⚠ Monitor group '{group_name}' not found — skipping keywords.")
            continue

        for data in keywords:
            stmt = select(Keyword).where(
                Keyword.word_zh == data["word_zh"],
                Keyword.monitor_group_id == group.id,
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing is not None:
                print(f"  • {data['word_zh']} / {data['word_en']} ({group_name}) — already exists, skipping.")
                continue

            kw = Keyword(monitor_group_id=group.id, **data)
            session.add(kw)
            print(f"  ✓ {data['word_zh']} / {data['word_en']} ({group_name})")

    await session.flush()


async def main() -> None:
    async with async_session_factory() as session:
        group_map = await seed_monitor_groups(session)
        await seed_ai_provider(session)
        await seed_brands(session, group_map)
        await seed_keywords(session, group_map)
        await session.commit()

    print("[seed] Seed data insertion complete.")


if __name__ == "__main__":
    asyncio.run(main())
