import os
import requests
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Any
from note import Note
from helper import Helper
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NotesDataFetcher:
    """Fetches notes data from an API and processes it according to requirements."""

    def __init__(self, config_path: str = "config.xlsx"):
        """Initialize the fetcher with paths and settings.

        Args:
            config_path: Path to the Excel file containing the date configuration
        """
        self.config_path = config_path
        self.base_url = os.environ.get("API_BASE_URL", "")
        if not self.base_url:
            raise EnvironmentError("API_BASE_URL environment variable is not set")

    def read_input_date(self) -> str:
        """Read the input date from the Excel configuration file.

        Returns:
            Formatted date string for API request
        """
        try:
            df = pd.read_excel(self.config_path)
            date_str = df.iloc[0, 0]  # Assuming date is in the first cell

            # Convert to datetime if it's not already
            if not isinstance(date_str, datetime):
                date_str = pd.to_datetime(date_str)

            formatted_date = date_str.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Read input date: {formatted_date}")
            return formatted_date
        except Exception as e:
            logger.error(f"Error reading input date: {e}")
            raise

    def fetch_data(self, date_str: str) -> Dict[str, Any]:
        """Fetch data from the API using the provided date.

        Args:
            date_str: Formatted date string for the API request

        Returns:
            JSON response from the API
        """
        try:
            url = f"{self.base_url}/get_notes_ankiconnect/{date_str}/False"
            logger.info(f"Fetching data from: {url}")

            response = requests.get(url)
            response.raise_for_status()

            return response.json()
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise

    def extract_tds_notes(self, data: Dict[str, Any]) -> List[str]:
        """Extract notes with t_m_id 'TDS' from the API response.

        Args:
            data: API response JSON

        Returns:
            List of n_data content strings
        """
        tds_notes = []

        for topic in data.get("data", []):
            if topic.get("t_m_id") == "TDS":
                for note in topic.get("n_data", []):
                    note_obj = Note(**note)
                    tds_notes.append({"note": note_obj.note, "images": note_obj.images})

        logger.info(f"Extracted {len(tds_notes)} TDS notes")
        return tds_notes

    def save_to_excel(
        self, notes: List[dict], output_path: str = Helper.get_output_path()
    ) -> None:
        """Save the extracted notes to an Excel file.

        Args:
            notes: List of note content strings
            output_path: Path to save the output Excel file
        """
        try:
            df = pd.DataFrame(notes)
            df.to_excel(output_path, index=False)
            logger.info(f"Saved {len(notes)} notes to {output_path}")
        except Exception as e:
            logger.error(f"Error saving to Excel: {e}")
            raise

    def update_input_date(self, current_date: datetime = datetime.now()) -> None:
        """Update the input date in the config file to the current date."""
        try:
            df = pd.DataFrame({"LastFetchDate": [current_date]})
            df.to_excel(self.config_path, index=False)
            logger.info(f"Updated input date to: {current_date}")
        except Exception as e:
            logger.error(f"Error updating input date: {e}")
            raise

    def process(self) -> None:
        """Run the complete data fetching and processing workflow."""
        input_date = self.read_input_date()
        api_data = self.fetch_data(input_date)
        tds_notes = self.extract_tds_notes(api_data)
        self.save_to_excel(tds_notes)
        self.update_input_date()
        logger.info("Process completed successfully")


def main():
    """Main entry point of the script."""
    try:
        fetcher = NotesDataFetcher()
        fetcher.process()
    except Exception as e:
        logger.error(f"Process failed: {e}")
        raise


if __name__ == "__main__":
    main()
