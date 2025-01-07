from collections import defaultdict
from typing import Dict, List, Any
import requests
import json
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


def get_geolocation(ip: str, token: str) -> Dict[str, str]:
    """
    Fetch geolocation data for a given IP using IPinfo API.

    Args:
        ip: IP address to lookup
        token: API token for IPinfo

    Returns:
        Dictionary containing country and city information
    """
    try:
        response = requests.get(f"https://ipinfo.io/{ip}", params={"token": token})
        if response.status_code == 200:
            data = response.json()
            return {"country": data.get("country"), "city": data.get("city")}
        else:
            logger.error(
                f"Error status code {response.status_code} from IPinfo for IP {ip}"
            )
            return {"country": None, "city": None}
    except Exception as e:
        logger.error(f"Error fetching geolocation for IP {ip}: {e}")
        return {"country": None, "city": None}


def collect_log_metrics(log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Collect pure statistical measurements from honeypot log entries.

    Args:
        log_entries: List of log entry dictionaries containing request data

    Returns:
        Dictionary with metrics for the log entries
    """
    # Get the IPinfo token - this is required
    ipinfo_token = os.getenv("IPINFO_TOKEN")
    if not ipinfo_token:
        raise ValueError(
            "IPINFO_TOKEN environment variable must be set for geolocation lookup"
        )

    # Initialize counters using defaultdict for automatic handling of new keys
    methods_count = defaultdict(int)
    status_codes_count = defaultdict(int)
    paths_count = defaultdict(int)
    parameters_count = defaultdict(int)
    headers_count = defaultdict(lambda: defaultdict(int))
    user_agents_count = defaultdict(int)

    # Track unique items
    unique_ips = set()
    unique_paths = set()
    unique_parameters = set()
    unique_headers = set()
    unique_user_agents = set()

    # Track IP metadata
    ip_metadata = defaultdict(
        lambda: {"request_count": 0, "country": None, "city": None}
    )

    # Track payload information
    payload_info = defaultdict(lambda: defaultdict(int))

    # Initialize timestamps
    start_time = None
    end_time = None

    for entry in log_entries:
        try:
            # Update timestamps using strptime instead of fromisoformat
            timestamp_str = entry["timestamp"].rstrip("Z")
            entry_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")

            if start_time is None or entry_time < start_time:
                start_time = entry_time
            if end_time is None or entry_time > end_time:
                end_time = entry_time

            # Extract and count method
            if "method" in entry:
                methods_count[entry["method"]] += 1

            # Extract and count URL/path
            if "url" in entry:
                url = entry["url"]
                paths_count[url] += 1
                unique_paths.add(url)

            # Extract and count IP
            if "remote_addr" in entry:
                remote_addr = entry["remote_addr"]
                ip = remote_addr.split(":")[0] if ":" in remote_addr else remote_addr
                unique_ips.add(ip)

                # Update IP metadata - always attempt geolocation since token is required
                ip_metadata[ip]["request_count"] += 1
                geolocation = get_geolocation(ip, ipinfo_token)
                ip_metadata[ip]["country"] = geolocation["country"]
                ip_metadata[ip]["city"] = geolocation["city"]

            # Process headers
            headers = entry.get("headers", {})
            if headers:
                for header_name, header_value in headers.items():
                    unique_headers.add(header_name)
                    headers_count[header_name][str(header_value)] += 1

            # Count user agents
            user_agent = entry.get("user_agent")
            if user_agent:
                user_agents_count[user_agent] += 1
                unique_user_agents.add(user_agent)

            # Count status codes if present
            if "status_code" in entry:
                status_codes_count[str(entry["status_code"])] += 1

            # Process parameters if present
            params = entry.get("parameters", {})
            if params:
                if isinstance(params, dict):
                    for param_name in params:
                        unique_parameters.add(param_name)
                        parameters_count[param_name] += 1

            # Process payload if present
            if "body" in entry:
                content_type = entry.get("content_type", "application/octet-stream")
                size = len(str(entry["body"]))  # Convert to string to safely get length
                payload_key = f"{content_type}_{size}"
                payload_info[payload_key]["size"] = size
                payload_info[payload_key]["content_type"] = content_type
                payload_info[payload_key]["count"] += 1

        except Exception as e:
            logger.error(f"Error processing log entry: {entry}. Error: {e}")
            continue

    # Format the chunk_id based on start timestamp
    chunk_id = start_time.strftime("%Y-%m-%d_%H-%M-%S") if start_time else "unknown"

    # Construct the output dictionary
    metrics = {
        "chunk_id": chunk_id,
        "timespan": {
            "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ") if start_time else None,
            "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ") if end_time else None,
        },
        "counters": {
            "total_requests": len(log_entries),
            "unique_ips": len(unique_ips),
            "unique_paths": len(unique_paths),
            "unique_parameters": len(unique_parameters),
            "unique_headers": len(unique_headers),
            "unique_user_agents": len(unique_user_agents),
        },
        "lists": {
            "methods": dict(methods_count),
            "status_codes": dict(status_codes_count),
            "paths": dict(paths_count),
            "parameters": dict(parameters_count),
            "headers": dict(headers_count),
            "user_agents": dict(user_agents_count),
        },
        "entities": {
            "ips": [
                {
                    "ip": ip,
                    "country": data["country"],
                    "city": data["city"],
                    "request_count": data["request_count"],
                }
                for ip, data in ip_metadata.items()
            ],
            "payloads": [
                {
                    "size": info["size"],
                    "content_type": info["content_type"],
                    "count": info["count"],
                }
                for info in payload_info.values()
            ],
        },
    }

    return metrics


def metrics_to_json(metrics: Dict[str, Any]) -> str:
    """
    Convert metrics dictionary to JSON string with consistent formatting.

    Args:
        metrics: Collected metrics dictionary

    Returns:
        JSON string representation of metrics
    """
    return json.dumps(metrics, indent=2, sort_keys=True)
