from datetime import datetime
from typing import List


class Helper:
    @staticmethod
    def get_output_path(topic_ids: List[str]) -> str:
        """Get the output Excel file path.

        Returns:
            Output Excel file path
        """
        current_time = datetime.now() 
        timestamp = current_time.strftime("%Y%m%d_%H%M%S")
        excel_file_name = f"{'_'.join(topic_ids)}_notes_{timestamp}.xlsx"
        ouput_directory = "output"
        output_path = f"{ouput_directory}/{excel_file_name}"
        return output_path
