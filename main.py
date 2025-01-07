import logging
import sys
import argparse

from honeycomb.logging import setup_logging
from honeycomb.config import load_config, ConfigurationError
from honeycomb.utils import search
from honeycomb.core.analyzer import LogAnalyzer, LogAnalyzerError

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Honeycomb - Chain-of-Density Security Log Analysis",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument(
        "--config", type=str, default="config.yaml", help="Path to configuration file"
    )

    parser.add_argument(
        "--input", type=str, default="hp.log", help="Input log file to analyze"
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=2,
        help="Number of log entries to analyze per chunk",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of log entries to analyze (default: analyze all)",
    )

    parser.add_argument(
        "--output", type=str, default=None, help="Output directory for analysis results"
    )

    parser.add_argument(
        "--speak", action="store_true", help="Speak the analysis results (experimental)"
    )

    return parser.parse_args()


def main():
    """Main entry point for Honeycomb."""
    args = parse_args()

    # Setup logging based on debug flag
    setup_logging(args.debug)

    try:
        # Load configuration
        config = load_config(args.config)

        # Load and filter logs
        filtered_logs = search(args.input, 1)
        logger.debug("Found %d logs", len(filtered_logs))

        # Apply limit if specified
        if args.limit is not None:
            filtered_logs = filtered_logs[: args.limit]
            logger.debug("Limited to %d logs", len(filtered_logs))

        # Show sample of logs in debug mode
        if args.debug:
            logger.debug("First few logs: %s", filtered_logs[0:3])

        # Initialize analyzer
        analyzer = LogAnalyzer(config, args.chunk_size)

        # Run analysis
        results = analyzer.analyze(filtered_logs)

        # Handle output
        if args.output:
            # TODO: Implement output saving
            logger.info("Saving results to %s", args.output)

        # Handle speech output if requested
        if args.speak:
            # TODO: Implement text-to-speech
            logger.info("Speech output not yet implemented")

    except ConfigurationError:
        logger.error("Could not load config file: %s", args.config)
        sys.exit(1)
    except FileNotFoundError:
        logger.error("Could not find log file: %s", args.input)
        sys.exit(1)
    except PermissionError:
        logger.error("Permission denied when trying to read files")
        sys.exit(1)
    except LogAnalyzerError as e:
        logger.error("Log analysis error occurred: %s", e)
        sys.exit(1)
    except IOError as e:
        logger.error("IO Error occurred: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error occurred: %s", e)
        logger.debug("Exception details:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
