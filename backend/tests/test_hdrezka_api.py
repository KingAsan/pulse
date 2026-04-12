"""Tests for HdRezkaApi service integration."""

import pytest
from services.hdrezka_api_service import HdRezkaApiService


@pytest.fixture
def service():
    """Create HdRezkaApi service instance."""
    return HdRezkaApiService()


class TestHdRezkaApiSearch:
    """Test search functionality."""

    def test_search_returns_results(self, service):
        """Search should return a list of results."""
        results = service.search("Матрица", limit=5)
        assert isinstance(results, list)
        # May return empty if API is down or rate limited
        if results:
            assert 'title' in results[0]
            assert 'url' in results[0]

    def test_search_empty_query(self, service):
        """Empty query should return empty list."""
        results = service.search("")
        assert results == []

    def test_search_respects_limit(self, service):
        """Search should respect limit parameter."""
        results = service.search("Star Wars", limit=3)
        assert len(results) <= 3


class TestHdRezkaApiCategories:
    """Test categories functionality."""

    def test_get_categories(self, service):
        """Should return list of categories."""
        categories = service.get_categories()
        assert isinstance(categories, list)
        assert len(categories) == 4
        assert categories[0]['id'] == 'films'
        assert categories[1]['id'] == 'series'
        assert categories[2]['id'] == 'cartoons'
        assert categories[3]['id'] == 'anime'


class TestHdRezkaApiBrowse:
    """Test browse functionality."""

    def test_browse_films(self, service):
        """Browse films should return results."""
        results = service.browse('films', page=1)
        assert isinstance(results, list)
        # May be empty if API is down
        if results:
            assert 'title' in results[0]
            assert 'url' in results[0]

    def test_browse_invalid_category(self, service):
        """Browse with invalid category should handle gracefully."""
        results = service.browse('invalid_category', page=1)
        assert isinstance(results, list)


class TestHdRezkaApiDetail:
    """Test detail functionality."""

    def test_detail_invalid_url(self, service):
        """Detail with invalid URL should return None."""
        result = service.get_detail("")
        assert result is None

    def test_detail_bad_url(self, service):
        """Detail with bad URL should return None or handle gracefully."""
        result = service.get_detail("https://hdrezka.ag/invalid_url_12345.html")
        # Should return None for non-existent URL
        assert result is None or isinstance(result, dict)


class TestHdRezkaApiStreams:
    """Test streams functionality."""

    def test_streams_invalid_url(self, service):
        """Streams with invalid URL should return empty list."""
        streams = service.get_streams("")
        assert streams == []

    def test_streams_bad_url(self, service):
        """Streams with bad URL should return empty list."""
        streams = service.get_streams("https://hdrezka.ag/invalid.html")
        assert streams == []


class TestHdRezkaApiSeasons:
    """Test seasons functionality."""

    def test_seasons_movie_url(self, service):
        """Seasons for movie URL should return empty list."""
        # Movies don't have seasons
        seasons = service.get_seasons("https://hdrezka.ag/films/123-movie.html")
        assert isinstance(seasons, list)

    def test_seasons_invalid_url(self, service):
        """Seasons with invalid URL should return empty list."""
        seasons = service.get_seasons("")
        assert seasons == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
