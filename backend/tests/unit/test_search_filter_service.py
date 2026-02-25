"""Unit tests for search_service and CandidateSearchRepository filter logic (Module 6)."""
from __future__ import annotations

import base64
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.repositories.search_repository import (
    CandidateSearchRepository,
    _decode_cursor,
    _encode_cursor,
    _matches_education_tier,
)
from app.schemas.search import (
    BulkExportRequest,
    EducationTier,
    SavedSearchCreate,
    SearchCandidateRequest,
    SkillFilter,
    SkillMatchMode,
    SortBy,
    TalentPoolAddCandidates,
    TalentPoolCreate,
    WorkPreference,
)
from app.services import search_service


# ── Cursor encode / decode ─────────────────────────────────────────────────────

class TestCursorCodec:
    def test_roundtrip(self):
        now = datetime(2025, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        uid = uuid.uuid4()
        encoded = _encode_cursor(now, uid)
        ts, decoded_id = _decode_cursor(encoded)
        # isoformat roundtrip may vary in timezone suffix; compare timestamps
        assert decoded_id == uid
        assert ts.year == 2025 and ts.month == 6 and ts.day == 15

    def test_encoded_is_urlsafe_base64(self):
        now = datetime.now(timezone.utc)
        uid = uuid.uuid4()
        encoded = _encode_cursor(now, uid)
        # Should not raise
        base64.urlsafe_b64decode(encoded.encode())

    def test_different_times_give_different_cursors(self):
        uid = uuid.uuid4()
        t1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2025, 1, 2, tzinfo=timezone.utc)
        assert _encode_cursor(t1, uid) != _encode_cursor(t2, uid)

    def test_different_ids_give_different_cursors(self):
        t = datetime(2025, 1, 1, tzinfo=timezone.utc)
        assert _encode_cursor(t, uuid.uuid4()) != _encode_cursor(t, uuid.uuid4())


# ── Education tier helper ──────────────────────────────────────────────────────

class TestMatchesEducationTier:
    def test_any_always_true(self):
        assert _matches_education_tier("B.Tech", EducationTier.ANY) is True
        assert _matches_education_tier(None, EducationTier.ANY) is True

    def test_none_degree_returns_true(self):
        assert _matches_education_tier(None, EducationTier.UNDERGRADUATE) is True

    def test_ug_btech(self):
        assert _matches_education_tier("B.Tech Computer Science", EducationTier.UNDERGRADUATE) is True

    def test_ug_bsc(self):
        assert _matches_education_tier("B.Sc Mathematics", EducationTier.UNDERGRADUATE) is True

    def test_ug_bca(self):
        assert _matches_education_tier("BCA Information Technology", EducationTier.UNDERGRADUATE) is True

    def test_pg_mtech(self):
        assert _matches_education_tier("M.Tech Data Science", EducationTier.POSTGRADUATE) is True

    def test_pg_mba(self):
        assert _matches_education_tier("MBA Finance", EducationTier.POSTGRADUATE) is True

    def test_pg_msc(self):
        assert _matches_education_tier("M.Sc Computer Science", EducationTier.POSTGRADUATE) is True

    def test_phd(self):
        assert _matches_education_tier("Ph.D Computer Science", EducationTier.PHD) is True

    def test_phd_doctor(self):
        assert _matches_education_tier("Doctor of Philosophy", EducationTier.PHD) is True

    def test_ug_does_not_match_pg(self):
        assert _matches_education_tier("M.Tech Software Engineering", EducationTier.UNDERGRADUATE) is False

    def test_pg_does_not_match_ug(self):
        assert _matches_education_tier("B.Tech Computer Engineering", EducationTier.POSTGRADUATE) is False

    def test_case_insensitive(self):
        assert _matches_education_tier("b.tech computer science", EducationTier.UNDERGRADUATE) is True
        assert _matches_education_tier("M.TECH", EducationTier.POSTGRADUATE) is True


# ── SearchCandidateRequest validation ─────────────────────────────────────────

class TestSearchCandidateRequest:
    def test_default_values(self):
        req = SearchCandidateRequest()
        assert req.page_size == 20
        assert req.sort_by == SortBy.RELEVANCE
        assert req.skill_match == SkillMatchMode.AND
        assert req.education_tier == EducationTier.ANY
        assert req.work_preference == WorkPreference.ANY
        assert req.skills == []
        assert req.cursor is None
        assert req.query is None

    def test_page_size_clamped(self):
        req = SearchCandidateRequest(page_size=50)
        assert req.page_size == 50

    def test_skill_filter_valid(self):
        sf = SkillFilter(skill="Python", min_years=2.0)
        assert sf.skill == "Python"
        assert sf.min_years == 2.0

    def test_skill_filter_no_min_years(self):
        sf = SkillFilter(skill="Java")
        assert sf.min_years is None

    def test_ctc_filters_in_lakhs(self):
        req = SearchCandidateRequest(ctc_min=5, ctc_max=20)
        assert req.ctc_min == 5
        assert req.ctc_max == 20

    def test_query_field_stored(self):
        req = SearchCandidateRequest(query="Python AND Django")
        assert req.query == "Python AND Django"


# ── Build base query (unit-level, no DB) ──────────────────────────────────────

class TestBuildBaseQuery:
    """Verify _build_base_query returns a Select without raising."""

    def _repo(self) -> CandidateSearchRepository:
        return CandidateSearchRepository()

    def test_no_filters(self):
        repo = self._repo()
        filters = SearchCandidateRequest()
        q = repo._build_base_query(filters)
        assert q is not None

    def test_with_query(self):
        repo = self._repo()
        filters = SearchCandidateRequest(query="Python AND Django")
        q = repo._build_base_query(filters)
        assert q is not None

    def test_with_skill_and(self):
        repo = self._repo()
        filters = SearchCandidateRequest(
            skills=[SkillFilter(skill="Python"), SkillFilter(skill="Django")],
            skill_match=SkillMatchMode.AND,
        )
        q = repo._build_base_query(filters)
        assert q is not None

    def test_with_skill_or(self):
        repo = self._repo()
        filters = SearchCandidateRequest(
            skills=[SkillFilter(skill="Java"), SkillFilter(skill="Kotlin")],
            skill_match=SkillMatchMode.OR,
        )
        q = repo._build_base_query(filters)
        assert q is not None

    def test_with_experience_range(self):
        repo = self._repo()
        filters = SearchCandidateRequest(experience_min=2.0, experience_max=8.0)
        q = repo._build_base_query(filters)
        assert q is not None

    def test_with_location(self):
        repo = self._repo()
        filters = SearchCandidateRequest(location="Bangalore")
        q = repo._build_base_query(filters)
        assert q is not None

    def test_with_notice_period(self):
        repo = self._repo()
        filters = SearchCandidateRequest(notice_period_max_days=30)
        q = repo._build_base_query(filters)
        assert q is not None

    def test_with_ctc_range(self):
        repo = self._repo()
        filters = SearchCandidateRequest(ctc_min=5, ctc_max=20)
        q = repo._build_base_query(filters)
        assert q is not None

    def test_with_profile_strength(self):
        repo = self._repo()
        filters = SearchCandidateRequest(profile_strength_min=70)
        q = repo._build_base_query(filters)
        assert q is not None

    def test_with_remote_preference(self):
        repo = self._repo()
        filters = SearchCandidateRequest(work_preference=WorkPreference.REMOTE)
        q = repo._build_base_query(filters)
        assert q is not None

    def test_with_education_tier_ug(self):
        repo = self._repo()
        filters = SearchCandidateRequest(education_tier=EducationTier.UNDERGRADUATE)
        q = repo._build_base_query(filters)
        assert q is not None

    def test_all_filters_combined(self):
        repo = self._repo()
        filters = SearchCandidateRequest(
            query="Python AND Django",
            skills=[SkillFilter(skill="Python", min_years=2.0)],
            skill_match=SkillMatchMode.AND,
            experience_min=3.0,
            experience_max=10.0,
            location="Bangalore",
            notice_period_max_days=60,
            ctc_min=8,
            ctc_max=25,
            education_tier=EducationTier.POSTGRADUATE,
            profile_strength_min=60,
            work_preference=WorkPreference.REMOTE,
            last_active_days=30,
            page_size=10,
            sort_by=SortBy.EXPERIENCE,
        )
        q = repo._build_base_query(filters)
        assert q is not None


# ── search_service helpers (mocked) ───────────────────────────────────────────

class TestSearchServiceCacheKey:
    def test_same_filters_same_key(self):
        from app.services.search_service import _cache_key
        f1 = SearchCandidateRequest(query="Python", location="Mumbai")
        f2 = SearchCandidateRequest(query="Python", location="Mumbai")
        assert _cache_key(f1) == _cache_key(f2)

    def test_different_filters_different_keys(self):
        from app.services.search_service import _cache_key
        f1 = SearchCandidateRequest(query="Python")
        f2 = SearchCandidateRequest(query="Java")
        assert _cache_key(f1) != _cache_key(f2)

    def test_cursor_excluded_from_key(self):
        from app.services.search_service import _cache_key
        f1 = SearchCandidateRequest(query="Python", cursor=None)
        f2 = SearchCandidateRequest(query="Python", cursor="somecursor")
        assert _cache_key(f1) == _cache_key(f2)

    def test_key_starts_with_prefix(self):
        from app.services.search_service import _cache_key
        key = _cache_key(SearchCandidateRequest(query="test"))
        assert key.startswith("search:candidates:")


@pytest.mark.asyncio
async def test_search_candidates_uses_cache():
    """search_candidates should return cached result if present and no cursor."""
    from app.schemas.search import CandidateSearchItem, SearchResult
    from app.services.search_service import search_candidates

    filters = SearchCandidateRequest(query="Python")
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    cached_result = SearchResult(
        total=1,
        candidates=[],
        next_cursor=None,
        page_size=20,
        cached=False,
    )

    with patch("app.services.search_service._get_cached", AsyncMock(return_value=cached_result)):
        result = await search_candidates(mock_db, filters, user_id)

    assert result.cached is True
    assert result.total == 1


@pytest.mark.asyncio
async def test_search_candidates_calls_repo_when_no_cache():
    """search_candidates should call _repo.search when cache is empty."""
    from app.schemas.search import SearchResult
    from app.services.search_service import search_candidates

    filters = SearchCandidateRequest(query="Django")
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    repo_result = SearchResult(
        total=5,
        candidates=[],
        next_cursor=None,
        page_size=20,
    )

    with patch("app.services.search_service._get_cached", AsyncMock(return_value=None)), \
         patch("app.services.search_service._set_cached", AsyncMock()), \
         patch("app.services.search_service._repo") as mock_repo:
        mock_repo.search = AsyncMock(return_value=repo_result)
        # DB commit may fail in mock; that's fine — analytics failure is swallowed
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock(side_effect=Exception("mock db"))
        result = await search_candidates(mock_db, filters, user_id)

    assert result.total == 5
    mock_repo.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_candidates_with_cursor_not_cached():
    """Cursored (paged) results should bypass cache entirely."""
    from app.schemas.search import SearchResult
    from app.services.search_service import search_candidates

    now = datetime.now(timezone.utc)
    cursor = base64.urlsafe_b64encode(
        f"{now.isoformat()}|{uuid.uuid4()}".encode()
    ).decode()

    filters = SearchCandidateRequest(cursor=cursor)
    user_id = uuid.uuid4()
    mock_db = AsyncMock()

    repo_result = SearchResult(total=3, candidates=[], next_cursor=None, page_size=20)

    with patch("app.services.search_service._get_cached") as mock_get, \
         patch("app.services.search_service._set_cached") as mock_set, \
         patch("app.services.search_service._repo") as mock_repo:
        mock_repo.search = AsyncMock(return_value=repo_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock(side_effect=Exception("mock db"))
        result = await search_candidates(mock_db, filters, user_id)

    # Cache get/set should NOT be called for paged results
    mock_get.assert_not_called()
    mock_set.assert_not_called()
    assert result.total == 3


# ── Saved search operations ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_saved_search():
    from app.services.search_service import create_saved_search
    from app.models.saved_search import SavedSearch

    user_id = uuid.uuid4()
    data = SavedSearchCreate(name="Senior Python", filters={"query": "Python", "experience_min": 5})

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    saved = SavedSearch(
        id=uuid.uuid4(),
        user_id=user_id,
        name=data.name,
        filters=data.filters,
        created_at=datetime.now(timezone.utc),
    )
    mock_db.refresh = AsyncMock(side_effect=lambda obj: None)

    with patch("app.services.search_service.SavedSearch", return_value=saved):
        result = await create_saved_search(mock_db, user_id, data)

    assert result.name == "Senior Python"
    assert result.filters == {"query": "Python", "experience_min": 5}


@pytest.mark.asyncio
async def test_delete_saved_search_not_found_raises_404():
    from app.services.search_service import delete_saved_search
    from fastapi import HTTPException

    user_id = uuid.uuid4()
    search_id = uuid.uuid4()
    mock_db = AsyncMock()
    mock_db.scalar = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await delete_saved_search(mock_db, user_id, search_id)

    assert exc_info.value.status_code == 404


# ── Talent pool operations ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_talent_pool():
    from app.services.search_service import create_talent_pool
    from app.models.saved_search import TalentPool

    user_id = uuid.uuid4()
    data = TalentPoolCreate(name="Senior Developers")

    pool = TalentPool(
        id=uuid.uuid4(),
        user_id=user_id,
        name=data.name,
        created_at=datetime.now(timezone.utc),
    )
    pool.candidates = []

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    with patch("app.services.search_service.TalentPool", return_value=pool):
        result = await create_talent_pool(mock_db, user_id, data)

    assert result.name == "Senior Developers"
    assert result.candidate_count == 0


@pytest.mark.asyncio
async def test_add_to_talent_pool_not_found_raises_404():
    from app.services.search_service import add_to_talent_pool
    from fastapi import HTTPException

    user_id = uuid.uuid4()
    pool_id = uuid.uuid4()
    data = TalentPoolAddCandidates(candidate_ids=[str(uuid.uuid4())])

    mock_db = AsyncMock()
    mock_db.scalar = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await add_to_talent_pool(mock_db, user_id, pool_id, data)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_add_to_talent_pool_skips_invalid_uuids():
    """Candidates with non-UUID ids should be silently skipped."""
    from app.services.search_service import add_to_talent_pool
    from app.models.saved_search import TalentPool

    user_id = uuid.uuid4()
    pool_id = uuid.uuid4()
    pool = TalentPool(id=pool_id, user_id=user_id, name="Test Pool")
    pool.candidates = []

    data = TalentPoolAddCandidates(candidate_ids=["not-a-uuid", "also-invalid"])

    mock_db = AsyncMock()
    mock_db.scalar = AsyncMock(return_value=pool)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    result = await add_to_talent_pool(mock_db, user_id, pool_id, data)
    assert result["added"] == 0


# ── CSV export ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_csv_no_valid_ids_raises_422():
    from app.services.search_service import export_candidates_csv
    from fastapi import HTTPException

    data = BulkExportRequest(candidate_ids=["bad-id", "also-bad"])
    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await export_candidates_csv(mock_db, data)

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_export_csv_returns_csv_string():
    from app.services.search_service import export_candidates_csv
    from app.models.candidate import CandidateProfile

    cid = uuid.uuid4()
    data = BulkExportRequest(candidate_ids=[str(cid)])

    profile = MagicMock(spec=CandidateProfile)
    profile.full_name = "Jane Doe"
    profile.headline = "Senior Python Developer"
    profile.location = "Bangalore"
    profile.years_of_experience = 7.0
    profile.notice_period_days = 30
    profile.desired_salary_min = 1500000
    profile.desired_salary_max = 2000000
    profile.profile_strength = 90
    profile.resume_filename = "jane_doe_resume.pdf"
    profile.skills = []

    mock_db = AsyncMock()
    mock_db.scalars = AsyncMock()
    mock_db.scalars.return_value.all = MagicMock(return_value=[profile])

    with patch("app.services.search_service.select", return_value=MagicMock()), \
         patch.object(mock_db, "scalars", return_value=AsyncMock(
             __aiter__=MagicMock(),
             all=MagicMock(return_value=[profile]),
         )):
        # Direct scalars mock
        scalars_result = MagicMock()
        scalars_result.all.return_value = [profile]
        mock_db.scalars = AsyncMock(return_value=scalars_result)
        result = await export_candidates_csv(mock_db, data)

    assert "Name" in result or "Jane" in result
    assert isinstance(result, str)


def test_csv_escape_commas():
    from app.services.search_service import _csv_esc
    assert _csv_esc("Hello, World") == '"Hello, World"'


def test_csv_escape_quotes():
    from app.services.search_service import _csv_esc
    assert _csv_esc('Say "Hello"') == '"Say ""Hello"""'


def test_csv_escape_none():
    from app.services.search_service import _csv_esc
    assert _csv_esc(None) == ""


def test_csv_escape_plain_string():
    from app.services.search_service import _csv_esc
    assert _csv_esc("JaneDoe") == "JaneDoe"
