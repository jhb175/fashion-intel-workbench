"""Unit tests for the AI business service layer."""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from cryptography.fernet import Fernet

from app.models.knowledge import KnowledgeEntry, KnowledgeEntryBrand, KnowledgeEntryKeyword
from app.services.ai_provider_adapter import AIProviderAdapter
from app.services.ai_service import (
    AIService,
    AIServiceBase,
    ArticleSummary,
    ArticleTags,
    DailyBriefingContent,
    DeepAnalysisResult,
    VALID_CONTENT_TYPES,
    VALID_MONITOR_GROUPS,
)
from app.services.encryption_service import EncryptionService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_adapter() -> AsyncMock:
    """Create a mock AIProviderAdapter."""
    adapter = AsyncMock(spec=AIProviderAdapter)
    return adapter


@pytest.fixture
def ai_service(mock_adapter: AsyncMock) -> AIService:
    """Create an AIService with a mocked adapter."""
    return AIService(provider_adapter=mock_adapter)


def _make_knowledge_entry(
    title: str = "Test Entry",
    category: str = "brand_profile",
    brands: list[str] | None = None,
    keywords: list[str] | None = None,
    summary: str | None = "Test summary",
) -> MagicMock:
    """Create a mock KnowledgeEntry."""
    entry = MagicMock(spec=KnowledgeEntry)
    entry.title = title
    entry.category = category
    entry.summary = summary

    brand_mocks = []
    for b in (brands or []):
        bm = MagicMock(spec=KnowledgeEntryBrand)
        bm.brand_name = b
        brand_mocks.append(bm)
    entry.brands = brand_mocks

    keyword_mocks = []
    for k in (keywords or []):
        km = MagicMock(spec=KnowledgeEntryKeyword)
        km.keyword = k
        keyword_mocks.append(km)
    entry.keywords = keyword_mocks

    return entry


# ---------------------------------------------------------------------------
# AIServiceBase is abstract
# ---------------------------------------------------------------------------


class TestAIServiceBase:
    def test_cannot_instantiate_abstract(self, mock_adapter: AsyncMock) -> None:
        with pytest.raises(TypeError):
            AIServiceBase(provider_adapter=mock_adapter)  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# generate_summary
# ---------------------------------------------------------------------------


class TestGenerateSummary:
    """Tests for AIService.generate_summary."""

    async def test_chinese_content_skips_ai(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        result = await ai_service.generate_summary(
            title="测试标题",
            content="这是一段中文内容",
            source_lang="zh",
        )
        assert result == "这是一段中文内容"
        mock_adapter.chat_completion.assert_not_called()

    async def test_chinese_zh_cn_variant_skips_ai(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        result = await ai_service.generate_summary(
            title="测试标题",
            content="这是简体中文内容",
            source_lang="zh-CN",
        )
        assert result == "这是简体中文内容"
        mock_adapter.chat_completion.assert_not_called()

    async def test_chinese_content_truncated_to_200(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        long_content = "中" * 300
        result = await ai_service.generate_summary(
            title="标题", content=long_content, source_lang="zh"
        )
        assert len(result) == 200
        mock_adapter.chat_completion.assert_not_called()

    async def test_chinese_empty_content_uses_title(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        result = await ai_service.generate_summary(
            title="测试标题", content="", source_lang="zh"
        )
        assert result == "测试标题"
        mock_adapter.chat_completion.assert_not_called()

    async def test_english_content_calls_ai(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = "Nike 发布了新款跑鞋"
        result = await ai_service.generate_summary(
            title="Nike releases new running shoes",
            content="Nike has released a new line of running shoes...",
            source_lang="en",
        )
        assert result == "Nike 发布了新款跑鞋"
        mock_adapter.chat_completion.assert_called_once()

    async def test_english_summary_truncated_to_200(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = "字" * 250
        result = await ai_service.generate_summary(
            title="Title", content="Content", source_lang="en"
        )
        assert len(result) == 200


# ---------------------------------------------------------------------------
# extract_tags
# ---------------------------------------------------------------------------


class TestExtractTags:
    """Tests for AIService.extract_tags."""

    async def test_valid_json_response(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = json.dumps(
            {
                "brands": ["Nike", "Adidas"],
                "monitor_groups": ["Sports"],
                "content_types": ["新品"],
                "keywords": ["跑鞋"],
            }
        )
        result = await ai_service.extract_tags(
            title="Nike x Adidas",
            content="A collaboration...",
            brand_pool=["Nike", "Adidas", "Puma"],
            keyword_pool=["跑鞋", "联名"],
        )
        assert isinstance(result, ArticleTags)
        assert "Nike" in result.brands
        assert "Adidas" in result.brands
        assert "Sports" in result.monitor_groups
        assert "新品" in result.content_types
        assert "跑鞋" in result.keywords

    async def test_filters_brands_to_pool(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = json.dumps(
            {
                "brands": ["Nike", "FakeBrand"],
                "monitor_groups": ["Sports"],
                "content_types": ["新品"],
                "keywords": [],
            }
        )
        result = await ai_service.extract_tags(
            title="Test",
            content="Test",
            brand_pool=["Nike"],
            keyword_pool=[],
        )
        assert result.brands == ["Nike"]

    async def test_filters_invalid_monitor_groups(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = json.dumps(
            {
                "brands": [],
                "monitor_groups": ["Sports", "InvalidGroup"],
                "content_types": [],
                "keywords": [],
            }
        )
        result = await ai_service.extract_tags(
            title="Test", content="Test", brand_pool=[], keyword_pool=[]
        )
        assert result.monitor_groups == ["Sports"]

    async def test_filters_invalid_content_types(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = json.dumps(
            {
                "brands": [],
                "monitor_groups": [],
                "content_types": ["联名", "无效类型"],
                "keywords": [],
            }
        )
        result = await ai_service.extract_tags(
            title="Test", content="Test", brand_pool=[], keyword_pool=[]
        )
        assert result.content_types == ["联名"]

    async def test_malformed_json_returns_empty_tags(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = "This is not JSON at all"
        result = await ai_service.extract_tags(
            title="Test", content="Test", brand_pool=["Nike"], keyword_pool=[]
        )
        assert result.brands == []
        assert result.monitor_groups == []
        assert result.content_types == []
        assert result.keywords == []

    async def test_json_with_code_fences(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = (
            "```json\n"
            '{"brands": ["Nike"], "monitor_groups": ["Sports"], '
            '"content_types": ["新品"], "keywords": ["跑鞋"]}\n'
            "```"
        )
        result = await ai_service.extract_tags(
            title="Test",
            content="Test",
            brand_pool=["Nike"],
            keyword_pool=["跑鞋"],
        )
        assert result.brands == ["Nike"]
        assert result.monitor_groups == ["Sports"]

    async def test_brand_matching_case_insensitive(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = json.dumps(
            {
                "brands": ["nike"],
                "monitor_groups": [],
                "content_types": [],
                "keywords": [],
            }
        )
        result = await ai_service.extract_tags(
            title="Test", content="Test", brand_pool=["Nike"], keyword_pool=[]
        )
        # "nike" matches "Nike" case-insensitively
        assert len(result.brands) == 1


# ---------------------------------------------------------------------------
# generate_deep_analysis
# ---------------------------------------------------------------------------


class TestGenerateDeepAnalysis:
    """Tests for AIService.generate_deep_analysis."""

    async def test_valid_json_response(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = json.dumps(
            {
                "importance": "这条资讯非常重要",
                "industry_background": "行业背景分析",
                "follow_up_suggestions": "建议跟进方向",
            }
        )
        tags = ArticleTags(brands=["Nike"], monitor_groups=["Sports"])
        result = await ai_service.generate_deep_analysis(
            title="Test", summary="Test summary", tags=tags
        )
        assert isinstance(result, DeepAnalysisResult)
        assert result.importance == "这条资讯非常重要"
        assert result.industry_background == "行业背景分析"
        assert result.follow_up_suggestions == "建议跟进方向"

    async def test_all_fields_non_empty(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = json.dumps(
            {
                "importance": "",
                "industry_background": "背景",
                "follow_up_suggestions": "",
            }
        )
        tags = ArticleTags()
        result = await ai_service.generate_deep_analysis(
            title="Test", summary="Summary", tags=tags
        )
        # Empty fields should be filled with fallback
        assert result.importance != ""
        assert result.industry_background == "背景"
        assert result.follow_up_suggestions != ""

    async def test_malformed_json_uses_fallback(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = "Not valid JSON"
        tags = ArticleTags()
        result = await ai_service.generate_deep_analysis(
            title="Test", summary="Summary", tags=tags
        )
        assert result.importance != ""
        assert result.industry_background != ""
        assert result.follow_up_suggestions != ""


# ---------------------------------------------------------------------------
# generate_daily_briefing
# ---------------------------------------------------------------------------


class TestGenerateDailyBriefing:
    """Tests for AIService.generate_daily_briefing."""

    async def test_empty_articles_returns_no_news(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        result = await ai_service.generate_daily_briefing(
            articles=[], briefing_date=date(2024, 1, 15)
        )
        assert isinstance(result, DailyBriefingContent)
        assert "无新增资讯" in result.summary
        mock_adapter.chat_completion.assert_not_called()

    async def test_valid_json_response(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = json.dumps(
            {
                "summary": "今日重点",
                "sections": [
                    {
                        "monitor_group": "Luxury",
                        "highlights": [
                            {
                                "article_id": "abc-123",
                                "title": "LV 新品",
                                "summary": "LV 发布新品",
                            }
                        ],
                    }
                ],
                "trends": ["奢侈品数字化"],
                "follow_up_suggestions": ["关注 LV 新品发布"],
            }
        )
        articles = [
            ArticleSummary(
                id="abc-123",
                title="LV 新品",
                summary="LV 发布新品",
                monitor_group="Luxury",
            )
        ]
        result = await ai_service.generate_daily_briefing(
            articles=articles, briefing_date=date(2024, 1, 15)
        )
        assert result.summary == "今日重点"
        assert len(result.sections) == 1
        assert result.sections[0]["monitor_group"] == "Luxury"
        assert len(result.trends) == 1
        assert len(result.follow_up_suggestions) == 1

    async def test_malformed_json_returns_fallback(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = "Not JSON"
        articles = [
            ArticleSummary(id="1", title="T", summary="S", monitor_group="Sports")
        ]
        result = await ai_service.generate_daily_briefing(
            articles=articles, briefing_date=date(2024, 1, 15)
        )
        assert isinstance(result, DailyBriefingContent)
        # Should have fallback values
        assert result.summary != ""
        assert len(result.trends) > 0
        assert len(result.follow_up_suggestions) > 0

    def test_to_dict(self) -> None:
        content = DailyBriefingContent(
            summary="Test",
            sections=[{"monitor_group": "Luxury", "highlights": []}],
            trends=["Trend1"],
            follow_up_suggestions=["Suggestion1"],
        )
        d = content.to_dict()
        assert d["summary"] == "Test"
        assert len(d["sections"]) == 1
        assert d["trends"] == ["Trend1"]
        assert d["follow_up_suggestions"] == ["Suggestion1"]


# ---------------------------------------------------------------------------
# generate_history_analysis
# ---------------------------------------------------------------------------


class TestGenerateHistoryAnalysis:
    """Tests for AIService.generate_history_analysis."""

    async def test_empty_knowledge_returns_empty(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        result = await ai_service.generate_history_analysis(
            article_summary="Test summary", knowledge_entries=[]
        )
        assert result == ""
        mock_adapter.chat_completion.assert_not_called()

    async def test_calls_ai_with_knowledge(
        self, ai_service: AIService, mock_adapter: AsyncMock
    ) -> None:
        mock_adapter.chat_completion.return_value = "历史背景分析结果"
        entry = _make_knowledge_entry(
            title="Nike 品牌档案",
            brands=["Nike"],
            keywords=["跑鞋"],
        )
        result = await ai_service.generate_history_analysis(
            article_summary="Nike 发布新跑鞋",
            knowledge_entries=[entry],
        )
        assert result == "历史背景分析结果"
        mock_adapter.chat_completion.assert_called_once()


# ---------------------------------------------------------------------------
# match_knowledge_entries
# ---------------------------------------------------------------------------


class TestMatchKnowledgeEntries:
    """Tests for AIService.match_knowledge_entries."""

    async def test_matches_by_brand(self, ai_service: AIService) -> None:
        tags = ArticleTags(brands=["Nike"], keywords=[])
        entry_match = _make_knowledge_entry(brands=["Nike"])
        entry_no_match = _make_knowledge_entry(brands=["Adidas"])

        result = await ai_service.match_knowledge_entries(
            article_tags=tags, knowledge_entries=[entry_match, entry_no_match]
        )
        assert len(result) == 1
        assert result[0] is entry_match

    async def test_matches_by_keyword(self, ai_service: AIService) -> None:
        tags = ArticleTags(brands=[], keywords=["跑鞋"])
        entry_match = _make_knowledge_entry(keywords=["跑鞋"])
        entry_no_match = _make_knowledge_entry(keywords=["手表"])

        result = await ai_service.match_knowledge_entries(
            article_tags=tags, knowledge_entries=[entry_match, entry_no_match]
        )
        assert len(result) == 1
        assert result[0] is entry_match

    async def test_matches_case_insensitive(self, ai_service: AIService) -> None:
        tags = ArticleTags(brands=["nike"], keywords=[])
        entry = _make_knowledge_entry(brands=["Nike"])

        result = await ai_service.match_knowledge_entries(
            article_tags=tags, knowledge_entries=[entry]
        )
        assert len(result) == 1

    async def test_no_match_returns_empty(self, ai_service: AIService) -> None:
        tags = ArticleTags(brands=["Nike"], keywords=["跑鞋"])
        entry = _make_knowledge_entry(brands=["Gucci"], keywords=["手表"])

        result = await ai_service.match_knowledge_entries(
            article_tags=tags, knowledge_entries=[entry]
        )
        assert len(result) == 0

    async def test_empty_tags_returns_empty(self, ai_service: AIService) -> None:
        tags = ArticleTags()
        entry = _make_knowledge_entry(brands=["Nike"], keywords=["跑鞋"])

        result = await ai_service.match_knowledge_entries(
            article_tags=tags, knowledge_entries=[entry]
        )
        assert len(result) == 0

    async def test_matches_by_both_brand_and_keyword(
        self, ai_service: AIService,
    ) -> None:
        tags = ArticleTags(brands=["Nike"], keywords=["跑鞋"])
        entry = _make_knowledge_entry(brands=["Nike"], keywords=["跑鞋"])

        result = await ai_service.match_knowledge_entries(
            article_tags=tags, knowledge_entries=[entry]
        )
        # Should appear only once even if both brand and keyword match
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _parse_tags edge cases
# ---------------------------------------------------------------------------


class TestParseTagsEdgeCases:
    """Direct tests for the static _parse_tags method."""

    def test_empty_json_object(self) -> None:
        result = AIService._parse_tags("{}", ["Nike"])
        assert result == ArticleTags()

    def test_non_string_values_filtered(self) -> None:
        raw = json.dumps(
            {
                "brands": ["Nike", 123, None],
                "monitor_groups": ["Sports", True],
                "content_types": ["联名", []],
                "keywords": ["跑鞋", ""],
            }
        )
        result = AIService._parse_tags(raw, ["Nike"])
        assert result.brands == ["Nike"]
        assert result.monitor_groups == ["Sports"]
        assert result.content_types == ["联名"]
        # Empty string keyword is filtered out
        assert result.keywords == ["跑鞋"]


# ---------------------------------------------------------------------------
# _parse_deep_analysis edge cases
# ---------------------------------------------------------------------------


class TestParseDeepAnalysisEdgeCases:
    """Direct tests for the static _parse_deep_analysis method."""

    def test_json_with_code_fences(self) -> None:
        raw = (
            "```json\n"
            '{"importance": "重要", "industry_background": "背景", '
            '"follow_up_suggestions": "建议"}\n'
            "```"
        )
        result = AIService._parse_deep_analysis(raw)
        assert result.importance == "重要"
        assert result.industry_background == "背景"
        assert result.follow_up_suggestions == "建议"

    def test_completely_empty_response(self) -> None:
        result = AIService._parse_deep_analysis("")
        assert result.importance != ""
        assert result.industry_background != ""
        assert result.follow_up_suggestions != ""
