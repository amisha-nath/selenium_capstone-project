import csv
import os
from utilis.logger import get_logger

logger = get_logger(__name__)

def read_csv_data(filename):
    """
    Reads CSV test data and returns a list of dictionaries.
    Each row becomes a dictionary where headers are keys.
    """
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", filename)

    data_list = []
    if not os.path.exists(data_path):
        logger.error(f"File not found: {repr(data_path)}")
        return []

    try:
        with open(data_path, mode="r", encoding="utf-8") as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                data_list.append(row)
        logger.info(f"Loaded data from: {filename} ({len(data_list)} records)")
    except Exception as e:
        logger.error(f"Error reading {filename}: {repr(e)}")
    return data_list