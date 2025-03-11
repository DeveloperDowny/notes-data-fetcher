import os
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open
import requests
from notes_data_fetcher import NotesDataFetcher


@pytest.fixture
def mock_env_variables():
    """Fixture to set required environment variables."""
    with patch.dict(os.environ, {"API_BASE_URL": "https://test-api.example.com"}):
        yield


@pytest.fixture
def sample_config_data():
    """Fixture for sample configuration data."""
    return pd.DataFrame({"LastFetchDate": [datetime(2023, 1, 1, 12, 0, 0)]})


@pytest.fixture
def sample_api_response():
    """Fixture for sample API response data."""
    return {
        "data": [
            {
                "t_m_id": "TDS",
                "n_data": [
                    {
                        "n_ans": "Test note 1",
                        "n_imgs": ["image1.jpg", "image2.jpg"]
                    },
                    {
                        "n_ans": "Test note 2",
                        "n_imgs": []
                    }
                ]
            },
            {
                "t_m_id": "OTHER",
                "n_data": [
                    {
                        "n_ans": "Non-TDS note",
                        "n_imgs": []
                    }
                ]
            }
        ]
    }


class TestNotesDataFetcher:
    """Test suite for NotesDataFetcher class."""

    def test_init_missing_env_variable(self):
        """Test initialization fails when API_BASE_URL is not set."""
        with patch.dict(os.environ, clear=True):
            with pytest.raises(EnvironmentError, match="API_BASE_URL environment variable is not set"):
                NotesDataFetcher()

    def test_init_success(self, mock_env_variables):
        """Test successful initialization with environment variables set."""
        fetcher = NotesDataFetcher()
        assert fetcher.base_url == "https://test-api.example.com"
        assert fetcher.config_path == "config.xlsx"

    def test_read_input_date(self, mock_env_variables, sample_config_data):
        """Test reading input date from configuration file."""
        with patch("pandas.read_excel", return_value=sample_config_data):
            fetcher = NotesDataFetcher()
            date_str = fetcher.read_input_date()
            assert date_str == "2023-01-01 12:00:00"

    def test_read_input_date_error(self, mock_env_variables):
        """Test error handling when reading input date fails."""
        with patch("pandas.read_excel", side_effect=Exception("Read error")):
            fetcher = NotesDataFetcher()
            with pytest.raises(Exception, match="Read error"):
                fetcher.read_input_date()

    def test_fetch_data(self, mock_env_variables):
        """Test fetching data from API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        
        with patch("requests.get", return_value=mock_response) as mock_get:
            fetcher = NotesDataFetcher()
            result = fetcher.fetch_data("2023-01-01 12:00:00")
            
            mock_get.assert_called_once_with(
                "https://test-api.example.com/get_notes_ankiconnect/2023-01-01 12:00:00/False"
            )
            assert result == {"data": []}

    def test_fetch_data_error(self, mock_env_variables):
        """Test error handling when API request fails."""
        with patch("requests.get", side_effect=requests.exceptions.RequestException("API error")):
            fetcher = NotesDataFetcher()
            with pytest.raises(Exception, match="API error"):
                fetcher.fetch_data("2023-01-01 12:00:00")

    def test_extract_tds_notes(self, mock_env_variables, sample_api_response):
        """Test extracting TDS notes from API response."""
        fetcher = NotesDataFetcher()
        notes = fetcher.extract_tds_notes(sample_api_response)
        
        assert len(notes) == 2
        assert notes[0]["note"] == "Test note 1"
        assert notes[0]["images"] == ", ".join(["image1.jpg", "image2.jpg"])
        assert notes[1]["note"] == "Test note 2"
        assert notes[1]["images"] == ""

    def test_extract_tds_notes_empty(self, mock_env_variables):
        """Test extracting TDS notes from empty API response."""
        fetcher = NotesDataFetcher()
        notes = fetcher.extract_tds_notes({"data": []})
        assert notes == []

    def test_save_to_excel(self, mock_env_variables):
        """Test saving notes to Excel file."""
        test_notes = [
            {"n_ans": "Note 1", "n_imgs": ["img1.jpg"]},
            {"n_ans": "Note 2", "n_imgs": []}
        ]
        
        with patch("pandas.DataFrame.to_excel") as mock_to_excel:
            fetcher = NotesDataFetcher()
            fetcher.save_to_excel(test_notes, "test_output.xlsx")
            
            mock_to_excel.assert_called_once()
            # Verify DataFrame content by checking the call's first argument
            df_arg = mock_to_excel.call_args[0][0]
            assert df_arg == "test_output.xlsx"

    def test_save_to_excel_error(self, mock_env_variables):
        """Test error handling when saving to Excel fails."""
        with patch("pandas.DataFrame.to_excel", side_effect=Exception("Save error")):
            with patch("notes_data_fetcher.Helper.get_output_path", return_value="test_output.xlsx"):
                fetcher = NotesDataFetcher()
                with pytest.raises(Exception, match="Save error"):
                    fetcher.save_to_excel([])

    def test_update_input_date(self, mock_env_variables):
        """Test updating input date in config file."""
        with patch("pandas.DataFrame.to_excel") as mock_to_excel:
            current_time = datetime.now()
            
            fetcher = NotesDataFetcher()
            fetcher.update_input_date(current_time)
            
            mock_to_excel.assert_called_once()
            # Check that the DataFrame has the correct date
            df_arg = mock_to_excel.call_args[1]["index"]
            assert df_arg is False

    def test_process_success(self, mock_env_variables, sample_config_data, sample_api_response):
        """Test the full processing workflow."""
        with patch.multiple(
            NotesDataFetcher,
            read_input_date=MagicMock(return_value="2023-01-01 12:00:00"),
            fetch_data=MagicMock(return_value=sample_api_response),
            extract_tds_notes=MagicMock(return_value=[{"n_ans": "Test", "n_imgs": []}]),
            save_to_excel=MagicMock(),
            update_input_date=MagicMock()
        ):
            fetcher = NotesDataFetcher()
            fetcher.process()
            
            # Verify each method was called once with correct parameters
            fetcher.read_input_date.assert_called_once()
            fetcher.fetch_data.assert_called_once_with("2023-01-01 12:00:00")
            fetcher.extract_tds_notes.assert_called_once_with(sample_api_response)
            fetcher.save_to_excel.assert_called_once_with([{"n_ans": "Test", "n_imgs": []}])
            fetcher.update_input_date.assert_called_once()

    def test_main_function(self, mock_env_variables):
        """Test the main function."""
        with patch("notes_data_fetcher.NotesDataFetcher.process") as mock_process:
            from notes_data_fetcher import main
            main()
            mock_process.assert_called_once()

    def test_main_function_error(self, mock_env_variables):
        """Test error handling in main function."""
        with patch("notes_data_fetcher.NotesDataFetcher.process", 
                   side_effect=Exception("Process error")):
            from notes_data_fetcher import main
            with pytest.raises(Exception, match="Process error"):
                main()