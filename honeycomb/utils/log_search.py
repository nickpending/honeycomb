# utils/log_search.py
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def search(logfile: str, days: int) -> List[Dict[str, Any]]:
    """Search and filter log entries based on date"""
    date_filter = (datetime.now() - timedelta(days)).strftime("%Y-%m-%d")
    filtered_logs = []

    with open(logfile) as hp_log:
        for line in hp_log:
            try:
                log_entry = json.loads(line)
                if log_entry["timestamp"][:10] > date_filter:
                    filtered_logs.append(log_entry)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing line: {e}")

    logger.info(f"Found {len(filtered_logs)} logs from last {days} days")
    return filtered_logs
