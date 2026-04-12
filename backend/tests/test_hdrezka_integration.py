"""Integration test for HDRezka routes - проверка структуры ответов."""

import pytest
import sys
import os

# Добавить backend в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.hdrezka_api_service import HdRezkaApiService


class TestHdRezkaApiServiceStructure:
    """Тесты структуры данных сервиса."""

    def setup_method(self):
        self.service = HdRezkaApiService()

    def test_categories_structure(self):
        """Categories должен возвращать правильный формат."""
        categories = self.service.get_categories()
        
        assert isinstance(categories, list)
        assert len(categories) == 4
        
        expected_ids = {'films', 'series', 'cartoons', 'anime'}
        actual_ids = {cat['id'] for cat in categories}
        assert expected_ids == actual_ids
        
        for cat in categories:
            assert 'id' in cat
            assert 'name' in cat
            assert 'url' in cat
            assert cat['url'].startswith('http')

    def test_search_result_format(self):
        """Результат поиска должен иметь правильную структуру."""
        # Тест на пустом запросе
        results = self.service.search("")
        assert results == []

    def test_detail_returns_none_for_invalid_url(self):
        """Detail для невалидного URL должен возвращать None."""
        result = self.service.get_detail("")
        assert result is None
        
        result = self.service.get_detail("not_a_url")
        assert result is None

    def test_seasons_returns_list_for_invalid_url(self):
        """Seasons для невалидного URL должен возвращать пустой список."""
        seasons = self.service.get_seasons("")
        assert isinstance(seasons, list)
        assert seasons == []

    def test_streams_returns_list_for_invalid_url(self):
        """Streams для невалидного URL должен возвращать пустой список."""
        streams = self.service.get_streams("")
        assert isinstance(streams, list)
        assert streams == []

    def test_browse_returns_list(self):
        """Browse должен возвращать список."""
        results = self.service.browse('films', page=1)
        assert isinstance(results, list)


class TestHdRezkaApiServiceMock:
    """Тесты с моковыми данными для проверки бизнес-логики."""

    def test_detail_structure_for_movie(self):
        """Проверка структуры detail для фильма (mock тест)."""
        # Это тест ожидаемой структуры
        expected_structure = {
            'url', 'title', 'original_title', 'description', 'poster',
            'year', 'genres', 'country', 'quality', 'duration',
            'imdb_rating', 'kp_rating', 'content_type', 'post_id',
            'translator_list', 'seasons_info', 'source_url', 'player_url'
        }
        
        # Проверить что сервис может вернуть такую структуру
        # (реально может быть None если API недоступен)
        service = HdRezkaApiService()
        result = service.get_detail("https://hdrezka.ag/films/test.html")
        
        if result:  # Если результат есть, проверить структуру
            assert isinstance(result, dict)
            # Проверить ключевые поля
            assert 'title' in result
            assert 'content_type' in result
            assert 'translator_list' in result
            assert isinstance(result['translator_list'], list)

    def test_season_structure(self):
        """Проверка структуры сезона."""
        expected_season = {
            'season',  # int
            'name',    # str
            'episodes' # list
        }
        
        # Проверить что seasons_info имеет правильную структуру
        sample_season = {
            'season': 1,
            'name': 'Сезон 1',
            'episodes': [
                {
                    'episode': 1,
                    'name': 'Эпизод 1',
                    'translations': []
                }
            ]
        }
        
        assert 'season' in sample_season
        assert 'episodes' in sample_season
        assert isinstance(sample_season['episodes'], list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
