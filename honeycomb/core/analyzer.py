from datetime import datetime
import logging
from typing import List, Dict, Any
from honeycomb.api.claude import ClaudeClient
from honeycomb.metrics import collect_log_metrics, metrics_to_json

logger = logging.getLogger(__name__)


class LogAnalyzerError(Exception):
    """Base exception for SecurityAssistant-specific errors"""

    pass


class LogAnalyzer:
    def __init__(self, config: Dict[str, Any], chunk_size: int):
        try:
            self.config = config
            self.findings = []
            self.claude_client = ClaudeClient()
            self.chunk_size = chunk_size
        except Exception as e:
            logger.error("Failed to initialize Log Analyzer", exc_info=True)
            raise LogAnalyzerError(f"Initialization failed: {str(e)}")

    def analyze(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_metrics = []
        routines = []
        interests = []

        # Analyze in chunks
        for i in range(0, len(logs), self.chunk_size):
            logger.debug(f"Processing chunk {i}")
            chunk = logs[i : i + self.chunk_size]
            # Decided to make this a non-AI task
            metrics_results = collect_log_metrics(chunk)
            all_metrics.append(metrics_results)
            logger.debug(f"Metrics {metrics_to_json(metrics_results)}")

            routine_response = self.claude_client.prompt_chain(
                None,
                [chunk, metrics_results],
                "Identify ROUTINE activity patterns",
                self.config["prompt_routine"],
            )
            routines.append(routine_response)

            ioi_response = self.claude_client.prompt_chain(
                None,
                [chunk, metrics_results, routine_response],
                "Identify indicators of interest",
                self.config["prompt_ioi"],
            )
            interests.append(ioi_response)

        # Aggregate, deduplicate and summarize
        aggregate_metrics_response = self.claude_client.prompt_chain(
            "claude-3-5-haiku-20241022",
            [all_metrics],
            "Aggregate metrics",
            self.config["prompt_aggregate_metrics"],
        )
        response_six = self.claude_client.prompt_chain(
            None,
            [routines],
            "Deduplicate routine activities",
            self.config["prompt_deduplicate_routine"],
        )

        response_four = self.claude_client.prompt_chain(
            None,
            [aggregate_metrics_response, routines, interests],
            "Summarize the data",
            self.config["prompt_summarize"],
        )
