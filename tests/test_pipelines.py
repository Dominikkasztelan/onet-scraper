import pytest

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
    mock_datetime = mocker.patch("onet_scraper.pipelines.datetime")
    mock_datetime.now.return_value.strftime.return_value = fixed_time

    # Mock open and json dump if needed (not needed for open_spider)
    mocked_open = mocker.patch("builtins.open", mocker.mock_open())
    mocked_exporter = mocker.patch("onet_scraper.pipelines.JsonLinesItemExporter")

    pipeline.open_spider(spider)

    # Check if os.makedirs was called
    # Note: We need to mock os in the pipeline module scope if we want to verify it,
    # but since we just imported it inside the method, we rely on the file path check.

    # Construct expected path using os.path.join to match system separator
    import os

    expected_filename = os.path.join("data", f"data_{fixed_time}.jsonl")

    mocked_open.assert_called_once_with(expected_filename, "wb")
    mocked_exporter.assert_called_once()


def test_process_item_writes_jsonl(pipeline, spider, mocker):
    # Setup pipeline with a mocked file handle
    mock_exporter = mocker.MagicMock()
    pipeline.exporter = mock_exporter

    item = {"title": "Test Title", "url": "http://test.com"}

    pipeline.process_item(item, spider)

    mock_exporter.export_item.assert_called_once_with(item)


def test_close_spider_closes_file(pipeline, spider, mocker):
    mock_file = mocker.MagicMock()
    mock_exporter = mocker.MagicMock()
    pipeline.file = mock_file
    pipeline.exporter = mock_exporter

    pipeline.close_spider(spider)

    mock_exporter.finish_exporting.assert_called_once()
    mock_file.close.assert_called_once()
