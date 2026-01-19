
import pytest
import json
from onet_scraper.pipelines import JsonWriterPipeline

@pytest.fixture
def pipeline():
    return JsonWriterPipeline()

@pytest.fixture
def spider(mocker):
    mock_spider = mocker.MagicMock()
    mock_spider.logger = mocker.MagicMock()
    return mock_spider

def test_open_spider_creates_timestamped_file(pipeline, spider, mocker):
    # Mock datetime
    fixed_time = "2026-05-20_12-00-00"
    mock_datetime = mocker.patch('onet_scraper.pipelines.datetime')
    mock_datetime.now.return_value.strftime.return_value = fixed_time
    
    # Mock open and json dump if needed (not needed for open_spider)
    mocked_open = mocker.patch('builtins.open', mocker.mock_open())
    
    pipeline.open_spider(spider)
    
    expected_filename = f'data_{fixed_time}.jsonl'
    mocked_open.assert_called_once_with(expected_filename, 'w', encoding='utf-8')
    assert pipeline.filename == expected_filename

def test_process_item_writes_jsonl(pipeline, spider, mocker):
    # Setup pipeline with a mocked file handle
    mock_file = mocker.MagicMock()
    pipeline.file = mock_file
    
    item = {'title': 'Test Title', 'url': 'http://test.com'}
    
    pipeline.process_item(item, spider)
    
    expected_line = json.dumps(item, ensure_ascii=False) + "\n"
    mock_file.write.assert_called_once_with(expected_line)

def test_close_spider_closes_file(pipeline, spider, mocker):
    mock_file = mocker.MagicMock()
    pipeline.file = mock_file
    
    pipeline.close_spider(spider)
    
    mock_file.close.assert_called_once()
