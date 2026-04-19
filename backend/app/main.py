"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.responses import error_response, success_response  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables (SQLite) + seed data. Shutdown: cleanup."""
    from app.database import create_all_tables, async_session_factory

    # Import all models so metadata is populated
    import app.models  # noqa: F401

    # Create tables (safe for SQLite; PostgreSQL uses Alembic)
    if settings.DATABASE_URL.startswith("sqlite"):
        await create_all_tables()
        logger.info("SQLite tables created")

        # Seed default data
        await _seed_default_data()

    yield


async def _seed_default_data():
    """Insert default admin user + monitor groups if they don't exist."""
    import bcrypt
    from sqlalchemy import select
    from app.database import async_session_factory
    from app.models.user import User
    from app.models.monitor_group import MonitorGroup
    from cryptography.fernet import Fernet

    async with async_session_factory() as session:
        # Admin user
        existing = (
            await session.execute(
                select(User).where(User.username == settings.DEFAULT_ADMIN_USERNAME)
            )
        ).scalar_one_or_none()
        if not existing:
            pw = bcrypt.hashpw(
                settings.DEFAULT_ADMIN_PASSWORD.encode(),
                bcrypt.gensalt(),
            ).decode()
            session.add(
                User(
                    username=settings.DEFAULT_ADMIN_USERNAME,
                    password_hash=pw,
                    display_name=settings.DEFAULT_ADMIN_DISPLAY_NAME,
                )
            )
            logger.info(
                "Created default admin user (%s)",
                settings.DEFAULT_ADMIN_USERNAME,
            )

        # Monitor groups
        groups = [
            ("Luxury", "奢侈品", 1), ("Sports", "运动", 2),
            ("Outdoor", "户外", 3), ("Rap/Culture", "说唱/文化", 4),
        ]
        for name, display, order in groups:
            exists = (await session.execute(select(MonitorGroup).where(MonitorGroup.name == name))).scalar_one_or_none()
            if not exists:
                session.add(MonitorGroup(name=name, display_name=display, sort_order=order))

        await session.commit()
        logger.info("Seed data ready")

        # Seed RSS sources
        await _seed_sources(session)

        # Seed brands, keywords, and knowledge base
        await _seed_brands(session)
        await _seed_keywords(session)
        await _seed_knowledge(session)


async def _seed_sources(session):
    """Insert default RSS sources for fashion/streetwear news.

    NOTE: These are international sources that will work when deployed to an
    overseas server. They may not work from China without a proxy.
    """
    from sqlalchemy import select
    from app.models.source import Source
    from app.models.monitor_group import MonitorGroup

    # Get monitor group IDs
    groups = {}
    for row in (await session.execute(select(MonitorGroup))).scalars().all():
        groups[row.name] = row.id

    # Check if sources already exist
    existing_count = (await session.execute(select(Source))).scalars().all()
    if existing_count:
        return

    sources = [
        # Luxury
        ("Hypebeast", "https://hypebeast.com/feed", "rss", "Luxury"),
        ("Highsnobiety", "https://www.highsnobiety.com/feed/", "rss", "Luxury"),
        ("WWD", "https://wwd.com/feed/", "rss", "Luxury"),
        ("Business of Fashion", "https://www.businessoffashion.com/feed", "rss", "Luxury"),
        ("Vogue", "https://www.vogue.com/feed/rss", "rss", "Luxury"),

        # Sports
        ("Sneaker News", "https://sneakernews.com/feed/", "rss", "Sports"),
        ("Nice Kicks", "https://www.nicekicks.com/feed/", "rss", "Sports"),
        ("Modern Notoriety", "https://modernnotoriety.com/feed/", "rss", "Sports"),
        ("Sole Collector", "https://solecollector.com/feed", "rss", "Sports"),

        # Outdoor
        ("GearJunkie", "https://gearjunkie.com/feed", "rss", "Outdoor"),
        ("Switchback Travel", "https://www.switchbacktravel.com/feed", "rss", "Outdoor"),

        # Rap/Culture
        ("Complex Style", "https://www.complex.com/style/feed", "rss", "Rap/Culture"),
        ("The Hundreds", "https://thehundreds.com/blogs/content.atom", "rss", "Rap/Culture"),
        ("SNOBETTE", "https://snobette.com/feed", "rss", "Rap/Culture"),
    ]

    for name, url, stype, group_name in sources:
        gid = groups.get(group_name)
        if gid:
            session.add(Source(
                name=name, url=url, source_type=stype,
                monitor_group_id=gid, is_enabled=True,
                collect_interval_minutes=60,
            ))

    await session.commit()
    logger.info("Seeded %d RSS sources", len(sources))

    # Seed sample articles for UI preview
    await _seed_sample_articles(session, groups)


async def _seed_sample_articles(session, groups: dict):
    """Insert sample articles so the UI has content to display."""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select
    from app.models.article import Article
    from app.models.source import Source
    from app.models.tag import ArticleTag

    existing = (await session.execute(select(Article))).scalars().first()
    if existing:
        return

    # Get first source per group for foreign key
    source_map = {}
    for row in (await session.execute(select(Source))).scalars().all():
        gid = str(row.monitor_group_id)
        if gid not in source_map:
            source_map[gid] = row.id

    # Find source_id for each group
    def sid(group_name):
        gid = str(groups.get(group_name, ''))
        return source_map.get(gid)

    now = datetime.now(timezone.utc)
    articles_data = [
        {
            "title": "Louis Vuitton x Pharrell: A New Chapter in Luxury Streetwear",
            "url": "https://example.com/lv-pharrell",
            "summary": "Louis Vuitton 与 Pharrell Williams 联名系列正式发布，将街头文化与高级时装深度融合，标志着奢侈品牌拥抱潮流文化的新篇章。该系列包含成衣、配饰和限量球鞋，定价从 5,000 元到 50,000 元不等。",
            "group": "Luxury", "tags": [("brand", "Louis Vuitton"), ("content_type", "联名"), ("monitor_group", "Luxury")],
            "hours_ago": 1,
        },
        {
            "title": "Nike Air Max Dn Drops in Three New Colorways for Spring 2026",
            "url": "https://example.com/nike-air-max-dn",
            "summary": "Nike Air Max Dn 推出三款全新春季配色，延续 Dynamic Air 技术革新。新配色灵感来自东京街头文化，定价 ¥1,099，将于下周在 SNKRS 和指定零售商全球发售。",
            "group": "Sports", "tags": [("brand", "Nike"), ("content_type", "新品"), ("monitor_group", "Sports")],
            "hours_ago": 2,
        },
        {
            "title": "Arc'teryx Opens Its Largest Global Flagship Store in Shanghai",
            "url": "https://example.com/arcteryx-shanghai",
            "summary": "始祖鸟在上海淮海中路开设全球最大旗舰店，占地 800 平方米，融合户外体验空间与零售概念。店内设有攀岩墙和 Gore-Tex 面料展示区，进一步巩固其在中国市场的高端户外定位。",
            "group": "Outdoor", "tags": [("brand", "Arc'teryx"), ("content_type", "品牌动态"), ("monitor_group", "Outdoor")],
            "hours_ago": 3,
        },
        {
            "title": "Supreme x The North Face FW25 Collection Officially Revealed",
            "url": "https://example.com/supreme-tnf-fw25",
            "summary": "Supreme 与 The North Face 2025 秋冬联名系列完整曝光，包含冲锋衣、羽绒服、抓绒夹克和配件共 12 件单品。延续双方长达 18 年的经典合作，本季以极地探险为主题。",
            "group": "Rap/Culture", "tags": [("brand", "Supreme"), ("content_type", "联名"), ("monitor_group", "Rap/Culture")],
            "hours_ago": 4,
        },
        {
            "title": "Balenciaga Spring 2026 Runway Show Stuns Paris Fashion Week",
            "url": "https://example.com/balenciaga-ss26",
            "summary": "Balenciaga 2026 春夏系列在巴黎大皇宫发布，Demna 以解构主义手法重新诠释经典廓形。超大号西装、建筑感连衣裙和金属配饰成为亮点，秀场设计引发行业热议。",
            "group": "Luxury", "tags": [("brand", "Balenciaga"), ("content_type", "秀场"), ("monitor_group", "Luxury")],
            "hours_ago": 5,
        },
        {
            "title": "adidas and Bad Bunny Unveil New Campus Colorway",
            "url": "https://example.com/adidas-bad-bunny",
            "summary": "adidas 与 Bad Bunny 合作推出全新 Campus 配色，以波多黎各文化为灵感，鞋面采用优质麂皮材质。限量 5,000 双，定价 ¥1,299，发售当日即售罄。",
            "group": "Sports", "tags": [("brand", "adidas"), ("content_type", "球鞋配饰"), ("monitor_group", "Sports")],
            "hours_ago": 6,
        },
        {
            "title": "Gucci Unveils Sabato De Sarno's Second Cruise Collection",
            "url": "https://example.com/gucci-cruise-2026",
            "summary": "Gucci 创意总监 Sabato De Sarno 在伦敦发布第二个早春度假系列，以意大利里维埃拉为灵感，色彩明快、剪裁利落。系列延续了 De Sarno 对极简优雅的追求。",
            "group": "Luxury", "tags": [("brand", "Gucci"), ("content_type", "秀场"), ("monitor_group", "Luxury")],
            "hours_ago": 8,
        },
        {
            "title": "Salomon XT-6 Expd Gets a Premium Makeover for SS26",
            "url": "https://example.com/salomon-xt6-ss26",
            "summary": "Salomon XT-6 Expd 推出 2026 春夏高端版本，采用 Gore-Tex 防水面料和 Vibram 大底。配色灵感来自阿尔卑斯山脉，定价 ¥1,899，面向高端户外和城市机能穿搭市场。",
            "group": "Outdoor", "tags": [("brand", "Salomon"), ("content_type", "新品"), ("monitor_group", "Outdoor")],
            "hours_ago": 10,
        },
        {
            "title": "Travis Scott x Nike Air Jordan 1 Low OG 'Olive' Release Date Confirmed",
            "url": "https://example.com/travis-scott-aj1-olive",
            "summary": "Travis Scott 与 Nike 合作的 Air Jordan 1 Low OG 'Olive' 配色确认将于 5 月 15 日发售，定价 $150。反钩设计延续 Travis Scott 标志性风格，预计将成为年度最热门球鞋之一。",
            "group": "Rap/Culture", "tags": [("brand", "Nike"), ("content_type", "球鞋配饰"), ("keyword", "说唱"), ("monitor_group", "Rap/Culture")],
            "hours_ago": 12,
        },
        {
            "title": "Dior Men's Pre-Fall 2026 Collection Blends Tailoring with Sportswear",
            "url": "https://example.com/dior-men-prefall-2026",
            "summary": "Dior 男装 2026 早秋系列将经典裁缝工艺与运动元素融合，Kim Jones 以赛车文化为灵感，推出了一系列技术面料西装和运动风配饰。系列将于 6 月在全球精品店发售。",
            "group": "Luxury", "tags": [("brand", "Dior"), ("content_type", "lookbook"), ("monitor_group", "Luxury")],
            "hours_ago": 14,
        },
        {
            "title": "New Balance 1906R 'Protection Pack' Expands with Four New Colors",
            "url": "https://example.com/nb-1906r-protection",
            "summary": "New Balance 1906R 'Protection Pack' 系列新增四款配色，延续该系列标志性的 N-ergy 缓震技术和复古跑鞋设计。定价 ¥999，已在官网和指定零售商开售。",
            "group": "Sports", "tags": [("brand", "New Balance"), ("content_type", "新品"), ("monitor_group", "Sports")],
            "hours_ago": 16,
        },
        {
            "title": "BAPE x Stüssy Capsule Collection Celebrates 30 Years of Streetwear",
            "url": "https://example.com/bape-stussy-30th",
            "summary": "BAPE 与 Stüssy 推出联名胶囊系列，纪念两大街头品牌各自 30 周年。系列包含 T 恤、卫衣、帽子和配件，融合双方标志性图案元素，限量发售。",
            "group": "Rap/Culture", "tags": [("brand", "BAPE"), ("content_type", "联名"), ("keyword", "街头"), ("monitor_group", "Rap/Culture")],
            "hours_ago": 18,
        },
    ]

    for i, a in enumerate(articles_data):
        source_id = sid(a["group"])
        if not source_id:
            continue

        article = Article(
            source_id=source_id,
            original_title=a["title"],
            original_url=a["url"],
            original_language="en",
            original_excerpt=a["title"],
            chinese_summary=a["summary"],
            published_at=now - timedelta(hours=a["hours_ago"]),
            processing_status="processed",
            title_hash=f"hash_{i}",
        )
        session.add(article)
        await session.flush()

        for tag_type, tag_value in a["tags"]:
            session.add(ArticleTag(
                article_id=article.id,
                tag_type=tag_type,
                tag_value=tag_value,
                is_auto=True,
            ))

    await session.commit()
    logger.info("Seeded %d sample articles", len(articles_data))


async def _seed_brands(session):
    """Insert comprehensive brand pool with official naming info."""
    from sqlalchemy import select
    from app.models.brand import Brand
    from app.models.monitor_group import MonitorGroup

    # Check if brands already exist
    existing = (await session.execute(select(Brand))).scalars().first()
    if existing:
        return

    # Get monitor group IDs
    groups = {}
    for row in (await session.execute(select(MonitorGroup))).scalars().all():
        groups[row.name] = row.id

    brands_data = [
        # Luxury (20 brands)
        ("路易威登", "Louis Vuitton", "LOUIS VUITTON", "Louis Vuitton", "全大写", "Luxury"),
        ("古驰", "Gucci", "GUCCI", "Gucci", "全大写", "Luxury"),
        ("迪奥", "Dior", "DIOR", "Dior", "全大写", "Luxury"),
        ("巴黎世家", "Balenciaga", "BALENCIAGA", "Balenciaga", "全大写", "Luxury"),
        ("普拉达", "Prada", "PRADA", "Prada", "全大写", "Luxury"),
        ("香奈儿", "Chanel", "CHANEL", "CHANEL", "全大写", "Luxury"),
        ("爱马仕", "Hermès", "Hermès", "Hermès", "注意 è 重音符号", "Luxury"),
        ("葆蝶家", "Bottega Veneta", "BOTTEGA VENETA", "Bottega Veneta", "全大写", "Luxury"),
        ("圣罗兰", "Saint Laurent", "SAINT LAURENT", "Saint Laurent", "全大写，不再使用 Yves", "Luxury"),
        ("华伦天奴", "Valentino", "VALENTINO", "Valentino", "全大写", "Luxury"),
        ("范思哲", "Versace", "VERSACE", "Versace", "全大写", "Luxury"),
        ("博柏利", "Burberry", "BURBERRY", "Burberry", "全大写", "Luxury"),
        ("罗意威", "Loewe", "LOEWE", "LOEWE", "全大写", "Luxury"),
        ("缪缪", "Miu Miu", "MIU MIU", "Miu Miu", "全大写", "Luxury"),
        ("赛琳", "Celine", "CELINE", "CELINE", "全大写，已去掉重音符号", "Luxury"),
        ("纪梵希", "Givenchy", "GIVENCHY", "Givenchy", "全大写", "Luxury"),
        ("芬迪", "Fendi", "FENDI", "Fendi", "全大写", "Luxury"),
        ("Off-White", "Off-White", "Off-White™", "Off-White", "含™符号，O 和 W 大写，中间连字符", "Luxury"),
        ("瑞克·欧文斯", "Rick Owens", "RICK OWENS", "Rick Owens", "全大写", "Luxury"),
        ("马吉拉", "Maison Margiela", "Maison Margiela", "Maison Margiela", "首字母大写", "Luxury"),

        # Sports (12 brands)
        ("耐克", "Nike", "Nike", "Nike", "首字母大写", "Sports"),
        ("阿迪达斯", "adidas", "adidas", "adidas", "全小写", "Sports"),
        ("新百伦", "New Balance", "New Balance", "New Balance", "每个单词首字母大写", "Sports"),
        ("彪马", "PUMA", "PUMA", "PUMA", "全大写", "Sports"),
        ("亚瑟士", "ASICS", "ASICS", "ASICS", "全大写", "Sports"),
        ("锐步", "Reebok", "Reebok", "Reebok", "首字母大写", "Sports"),
        ("匡威", "Converse", "Converse", "Converse", "首字母大写", "Sports"),
        ("万斯", "Vans", "Vans", "Vans", "首字母大写", "Sports"),
        ("乔丹", "Jordan", "Jordan", "Jordan", "首字母大写，Air Jordan 的子品牌", "Sports"),
        ("HOKA", "HOKA", "HOKA", "HOKA", "全大写", "Sports"),
        ("昂跑", "On", "On", "On", "首字母大写", "Sports"),
        ("索康尼", "Saucony", "Saucony", "Saucony", "首字母大写", "Sports"),

        # Outdoor (9 brands)
        ("北面", "The North Face", "The North Face", "The North Face", "每个单词首字母大写", "Outdoor"),
        ("始祖鸟", "Arc'teryx", "Arc'teryx", "Arc'teryx", "注意撇号和小写 t", "Outdoor"),
        ("巴塔哥尼亚", "Patagonia", "Patagonia", "Patagonia", "首字母大写", "Outdoor"),
        ("萨洛蒙", "Salomon", "Salomon", "Salomon", "首字母大写", "Outdoor"),
        ("哥伦比亚", "Columbia", "Columbia", "Columbia", "首字母大写", "Outdoor"),
        ("猛犸象", "Mammut", "Mammut", "Mammut", "首字母大写", "Outdoor"),
        ("老人头", "Norrøna", "Norrøna", "Norrøna", "注意 ø 字符", "Outdoor"),
        ("雪峰", "Snow Peak", "Snow Peak", "Snow Peak", "两个单词，首字母大写", "Outdoor"),
        ("and wander", "and wander", "and wander", "and wander", "全小写", "Outdoor"),

        # Rap/Culture (14 brands)
        ("Supreme", "Supreme", "Supreme", "Supreme", "首字母大写", "Rap/Culture"),
        ("猿人头", "BAPE", "A BATHING APE®", "BAPE", "全大写，官方全称含 ® 符号", "Rap/Culture"),
        ("斯图西", "Stüssy", "Stüssy", "Stussy", "注意 ü 字符", "Rap/Culture"),
        ("Palace", "Palace", "Palace Skateboards", "Palace", "首字母大写", "Rap/Culture"),
        ("KITH", "KITH", "KITH", "Kith", "全大写", "Rap/Culture"),
        ("Fear of God", "Fear of God", "Fear of God", "Fear of God", "每个单词首字母大写", "Rap/Culture"),
        ("ESSENTIALS", "ESSENTIALS", "Fear of God ESSENTIALS", "ESSENTIALS", "全大写", "Rap/Culture"),
        ("川久保玲", "Comme des Garçons", "COMME des GARÇONS", "Comme des Garçons", "注意大小写混合和 ç 字符", "Rap/Culture"),
        ("NEIGHBORHOOD", "NEIGHBORHOOD", "NEIGHBORHOOD", "NEIGHBORHOOD", "全大写", "Rap/Culture"),
        ("WTAPS", "WTAPS", "WTAPS", "WTAPS", "全大写", "Rap/Culture"),
        ("visvim", "visvim", "visvim", "visvim", "全小写", "Rap/Culture"),
        ("Human Made", "Human Made", "HUMAN MADE", "Human Made", "全大写", "Rap/Culture"),
        ("Ambush", "Ambush", "AMBUSH", "AMBUSH", "全大写", "Rap/Culture"),
        ("sacai", "sacai", "sacai", "sacai", "全小写", "Rap/Culture"),
    ]

    for name_zh, name_en, official, social, notes, group_name in brands_data:
        gid = groups.get(group_name)
        session.add(Brand(
            name_zh=name_zh,
            name_en=name_en,
            official_name=official,
            social_media_name=social,
            naming_notes=notes,
            monitor_group_id=gid,
        ))

    await session.commit()
    logger.info("Seeded %d brands", len(brands_data))


async def _seed_keywords(session):
    """Insert comprehensive keywords per monitor group."""
    from sqlalchemy import select
    from app.models.keyword import Keyword
    from app.models.monitor_group import MonitorGroup

    # Check if keywords already exist
    existing = (await session.execute(select(Keyword))).scalars().first()
    if existing:
        return

    # Get monitor group IDs
    groups = {}
    for row in (await session.execute(select(MonitorGroup))).scalars().all():
        groups[row.name] = row.id

    keywords_data = {
        "Luxury": [
            ("联名", "collaboration"), ("高定", "haute couture"),
            ("秀场", "runway"), ("新品", "new release"),
            ("广告大片", "campaign"), ("campaign", "campaign"),
            ("lookbook", "lookbook"), ("创意总监", "creative director"),
            ("品牌动态", "brand news"), ("快闪", "pop-up"),
        ],
        "Sports": [
            ("球鞋", "sneakers"), ("联名", "collaboration"),
            ("复刻", "retro"), ("运动装备", "sportswear"),
            ("跑鞋", "running shoes"), ("篮球鞋", "basketball shoes"),
            ("发售日期", "release date"), ("限量", "limited edition"),
        ],
        "Outdoor": [
            ("山系", "gorpcore"), ("机能", "techwear"),
            ("户外装备", "outdoor gear"), ("联名", "collaboration"),
            ("冲锋衣", "shell jacket"), ("Gore-Tex", "Gore-Tex"),
            ("露营", "camping"),
        ],
        "Rap/Culture": [
            ("街头", "streetwear"), ("限量", "limited edition"),
            ("说唱", "rap"), ("涂鸦", "graffiti"),
            ("滑板", "skateboarding"), ("Drop", "drop"),
            ("联名", "collaboration"), ("二手市场", "resale market"),
        ],
    }

    count = 0
    for group_name, kw_list in keywords_data.items():
        gid = groups.get(group_name)
        if not gid:
            continue
        for word_zh, word_en in kw_list:
            session.add(Keyword(
                word_zh=word_zh,
                word_en=word_en,
                monitor_group_id=gid,
            ))
            count += 1

    await session.commit()
    logger.info("Seeded %d keywords", count)


async def _seed_knowledge(session):
    """Insert knowledge base entries for major brands and styles."""
    from sqlalchemy import select
    from app.models.knowledge import (
        KnowledgeEntry,
        KnowledgeEntryBrand,
        KnowledgeEntryKeyword,
    )

    # Check if knowledge entries already exist
    existing = (await session.execute(select(KnowledgeEntry))).scalars().first()
    if existing:
        return

    entries = [
        # --- Brand Profiles ---
        {
            "title": "Louis Vuitton",
            "category": "brand_profile",
            "summary": "法国奢侈品牌，1854年创立，以旅行箱包起家，现为LVMH集团旗舰品牌",
            "content": {
                "founded_year": 1854,
                "founder": "Louis Vuitton",
                "headquarters": "Paris, France",
                "timeline": [
                    {"year": 1854, "event": "路易·威登在巴黎创立品牌"},
                    {"year": 1896, "event": "推出经典Monogram图案"},
                    {"year": 1997, "event": "Marc Jacobs出任创意总监"},
                    {"year": 2018, "event": "Virgil Abloh出任男装创意总监"},
                    {"year": 2023, "event": "Pharrell Williams接任男装创意总监"},
                ],
                "key_facts": [
                    "全球最大奢侈品集团LVMH旗舰品牌",
                    "Monogram是全球最具辨识度的奢侈品标识之一",
                    "与Supreme、Fragment等潮流品牌的联名开创了奢侈品×街头的先河",
                ],
                "related_styles": ["高级时装", "旅行箱包", "奢侈街头"],
            },
            "brands": ["Louis Vuitton"],
            "keywords": ["奢侈品", "LVMH", "联名"],
        },
        {
            "title": "Nike",
            "category": "brand_profile",
            "summary": "全球最大运动品牌，1964年创立，以创新运动科技和球鞋文化闻名",
            "content": {
                "founded_year": 1964,
                "founder": "Phil Knight & Bill Bowerman",
                "headquarters": "Beaverton, Oregon, USA",
                "timeline": [
                    {"year": 1964, "event": "Blue Ribbon Sports成立"},
                    {"year": 1971, "event": "正式更名为Nike，Swoosh标志诞生"},
                    {"year": 1984, "event": "签约Michael Jordan，推出Air Jordan系列"},
                    {"year": 1987, "event": "Air Max 1发布，可视气垫革命"},
                    {"year": 2017, "event": "Off-White x Nike 'The Ten'系列引爆球鞋市场"},
                    {"year": 2024, "event": "Air Max Dn发布，Dynamic Air技术"},
                ],
                "key_facts": [
                    "全球运动品牌市值第一",
                    "Air Jordan系列是球鞋文化的基石",
                    "与Travis Scott、Off-White等的联名持续引领潮流",
                ],
                "related_styles": ["运动", "球鞋文化", "街头"],
            },
            "brands": ["Nike"],
            "keywords": ["球鞋", "运动", "联名"],
        },
        {
            "title": "Supreme",
            "category": "brand_profile",
            "summary": "美国街头潮流品牌，1994年创立于纽约，以限量发售和跨界联名闻名",
            "content": {
                "founded_year": 1994,
                "founder": "James Jebbia",
                "headquarters": "New York, USA",
                "timeline": [
                    {"year": 1994, "event": "James Jebbia在纽约Lafayette Street开设第一家店"},
                    {"year": 2017, "event": "与Louis Vuitton联名，街头×奢侈品里程碑"},
                    {"year": 2020, "event": "被VF Corporation以21亿美元收购"},
                    {"year": 2024, "event": "被EssilorLuxottica收购"},
                ],
                "key_facts": [
                    "每周四限量发售（Drop）模式的开创者",
                    "Box Logo是街头文化最具标志性的图案之一",
                    "与Nike SB Dunk的联名系列是球鞋收藏经典",
                ],
                "related_styles": ["街头", "滑板", "限量"],
            },
            "brands": ["Supreme"],
            "keywords": ["街头", "限量", "联名"],
        },
        # --- Style History ---
        {
            "title": "Gorpcore",
            "category": "style_history",
            "summary": "将户外功能性服饰融入日常穿搭的时尚趋势，2017年前后兴起",
            "content": {
                "timeline": [
                    {"year": 2017, "event": "Gorpcore一词首次出现在时尚媒体"},
                    {"year": 2019, "event": "Salomon XT-6成为时尚圈热门单品"},
                    {"year": 2021, "event": "Arc'teryx成为中国市场最热门户外品牌"},
                    {"year": 2023, "event": "Gorpcore从亚文化进入主流时尚"},
                ],
                "key_facts": [
                    "Gorp = Good Old Raisins and Peanuts，指户外零食",
                    "核心品牌：Arc'teryx、Salomon、The North Face",
                    "从功能性穿着演变为时尚态度表达",
                ],
                "related_styles": ["户外", "机能", "山系"],
                "description": "Gorpcore是一种将户外功能性服饰（冲锋衣、登山鞋、抓绒衣等）融入日常城市穿搭的时尚趋势。它不仅是穿衣风格，更代表了一种亲近自然、注重实用性的生活态度。",
            },
            "brands": ["Arc'teryx", "Salomon", "The North Face"],
            "keywords": ["户外", "机能", "山系"],
        },
        {
            "title": "Streetwear",
            "category": "style_history",
            "summary": "起源于1980年代美国滑板和嘻哈文化的服装风格，现已成为全球时尚主流",
            "content": {
                "timeline": [
                    {"year": 1984, "event": "Stüssy在加州创立，被视为街头服饰先驱"},
                    {"year": 1994, "event": "Supreme在纽约开店，定义了街头品牌模式"},
                    {"year": 2017, "event": "Louis Vuitton x Supreme联名，街头正式进入奢侈品殿堂"},
                    {"year": 2018, "event": "Virgil Abloh出任Louis Vuitton男装创意总监"},
                ],
                "key_facts": [
                    "街头服饰的核心元素：T恤、卫衣、球鞋、棒球帽",
                    "限量发售（Drop）文化是街头品牌的核心商业模式",
                    "从亚文化到主流时尚的转变在2010年代加速",
                ],
                "related_styles": ["嘻哈", "滑板", "潮流"],
                "description": "街头服饰（Streetwear）起源于1980年代的美国西海岸滑板文化和东海岸嘻哈文化，经过四十年的发展，已从亚文化服装演变为全球时尚的主流力量。",
            },
            "brands": ["Supreme", "BAPE", "Stüssy", "Palace"],
            "keywords": ["街头", "潮流", "限量"],
        },
        # --- Classic Items ---
        {
            "title": "Air Jordan 1",
            "category": "classic_item",
            "summary": "Nike为Michael Jordan打造的第一双签名球鞋，1985年发售，球鞋文化的奠基之作",
            "content": {
                "timeline": [
                    {"year": 1984, "event": "Nike签约新秀Michael Jordan"},
                    {"year": 1985, "event": "Air Jordan 1正式发售，因违反NBA着装规定被罚款"},
                    {"year": 2015, "event": "'Chicago'配色复刻引发全球抢购"},
                    {"year": 2019, "event": "Travis Scott联名反钩AJ1成为年度最热球鞋"},
                ],
                "key_facts": [
                    "设计师：Peter Moore",
                    "原价：$65（1985年）",
                    "被NBA禁止穿着的故事成为最成功的营销案例之一",
                    "Travis Scott反钩版本二级市场价格超过$2,000",
                ],
                "related_styles": ["球鞋文化", "街头", "收藏"],
                "description": "Air Jordan 1不仅是一双球鞋，它是整个球鞋文化的起点。从1985年被NBA禁止穿着的叛逆故事，到如今每次复刻都引发全球抢购，AJ1定义了球鞋作为文化符号的意义。",
            },
            "brands": ["Nike", "Jordan"],
            "keywords": ["球鞋", "经典", "收藏"],
        },
        {
            "title": "Birkin Bag",
            "category": "classic_item",
            "summary": "Hermès最具标志性的手袋，1984年诞生，被视为奢侈品投资的标杆",
            "content": {
                "timeline": [
                    {"year": 1984, "event": "Jean-Louis Dumas在飞机上遇到Jane Birkin，灵感诞生"},
                    {"year": 1990, "event": "Birkin包开始出现等待名单制度"},
                    {"year": 2010, "event": "二级市场价格开始系统性超过零售价"},
                    {"year": 2023, "event": "部分稀有款式拍卖价格超过50万美元"},
                ],
                "key_facts": [
                    "以英国女演员Jane Birkin命名",
                    "每只包由一位工匠手工制作，耗时约18-24小时",
                    "购买通常需要在Hermès有长期消费记录",
                    "被视为比黄金更好的投资品",
                ],
                "related_styles": ["奢侈品", "手袋", "投资"],
                "description": "Birkin包是Hermès的镇店之宝，也是全球最难买到的奢侈品之一。它不仅是一个手袋，更是身份、品味和财富的象征，其二级市场价值持续超越零售价。",
            },
            "brands": ["Hermès"],
            "keywords": ["奢侈品", "手袋", "经典"],
        },
    ]

    for entry_data in entries:
        entry = KnowledgeEntry(
            title=entry_data["title"],
            category=entry_data["category"],
            summary=entry_data["summary"],
            content=entry_data["content"],
        )
        session.add(entry)
        await session.flush()  # Get the generated ID

        # Add brand associations
        for brand_name in entry_data.get("brands", []):
            session.add(KnowledgeEntryBrand(
                knowledge_entry_id=entry.id,
                brand_name=brand_name,
            ))

        # Add keyword associations
        for keyword in entry_data.get("keywords", []):
            session.add(KnowledgeEntryKeyword(
                knowledge_entry_id=entry.id,
                keyword=keyword,
            ))

    await session.commit()
    logger.info("Seeded %d knowledge entries", len(entries))


app = FastAPI(
    title="Fashion Intel Workbench",
    description="AI-powered fashion intelligence platform for trend editors",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
from app.utils.errors import register_exception_handlers  # noqa: E402
register_exception_handlers(app)

@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=error_response(message="Internal server error", code=500))

# Routers
from app.routers.auth import router as auth_router  # noqa: E402
from app.routers.ai_providers import router as ai_providers_router  # noqa: E402
from app.routers.articles import router as articles_router  # noqa: E402
from app.routers.bookmarks import router as bookmarks_router  # noqa: E402
from app.routers.briefings import router as briefings_router  # noqa: E402
from app.routers.knowledge import router as knowledge_router  # noqa: E402
from app.routers.admin import router as admin_router  # noqa: E402
from app.routers.dashboard import router as dashboard_router  # noqa: E402

app.include_router(auth_router)
app.include_router(ai_providers_router)
app.include_router(articles_router)
app.include_router(bookmarks_router)
app.include_router(briefings_router)
app.include_router(knowledge_router)
app.include_router(admin_router)
app.include_router(dashboard_router)

@app.get("/health")
async def health_check() -> dict:
    return success_response(data={"status": "healthy"})
