"""OpenAI Batch API client for asynchronous symbol analysis."""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from named.logging import get_logger

logger = get_logger("batch_client")


@dataclass
class BatchJob:
    """Represents a batch processing job.

    Attributes:
        batch_id: Unique identifier for the batch job
        input_file_id: ID of the uploaded input JSONL file
        status: Current status (validating, in_progress, completed, failed, expired, cancelled)
        symbols: Original symbol data for result mapping
        created_at: Unix timestamp when batch was created
        completed_at: Unix timestamp when batch completed (if completed)
        output_file_id: ID of the output file containing results (if completed)
        error: Error message if batch failed
    """

    batch_id: str
    input_file_id: str
    status: str
    symbols: list[dict[str, Any]]
    created_at: int
    completed_at: int | None = None
    output_file_id: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert BatchJob to dictionary for serialization."""
        return {
            "batch_id": self.batch_id,
            "input_file_id": self.input_file_id,
            "status": self.status,
            "symbols": self.symbols,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "output_file_id": self.output_file_id,
            "error": self.error,
        }


class BatchAnalysisClient:
    """Client for batch analysis using OpenAI Batch API.

    This client handles the full workflow of batch processing:
    1. Create batch requests in JSONL format
    2. Upload to OpenAI and submit batch job
    3. Poll status until completion
    4. Download and parse results
    5. Map results back to original symbols

    Example:
        >>> client = BatchAnalysisClient(api_key="sk-...")
        >>> requests = client.create_batch_requests(symbols, system_prompt, rules_context)
        >>> job = client.submit_batch(requests, symbols)
        >>> completed_job = client.poll_batch(job)
        >>> results = client.download_results(completed_job)
        >>> parsed = client.parse_batch_results(results, completed_job)
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """Initialize batch analysis client.

        Args:
            api_key: OpenAI API key
            model: Model to use for analysis (default: gpt-4o)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def create_batch_requests(
        self, symbols: list[dict[str, Any]], system_prompt: str, rules_context: str
    ) -> list[dict[str, Any]]:
        """Generate batch requests in OpenAI JSONL format.

        Args:
            symbols: List of symbols with name, kind, context, etc.
            system_prompt: System role message
            rules_context: Rules and guardrails context

        Returns:
            List of request dicts ready for JSONL serialization

        Example:
            >>> symbols = [{"name": "foo", "kind": "method", "context": "void foo() {}"}]
            >>> requests = client.create_batch_requests(symbols, system_prompt, rules)
            >>> len(requests)
            1
            >>> requests[0]["custom_id"]
            'symbol-0'
        """
        requests = []
        for idx, symbol in enumerate(symbols):
            # Build prompt for this symbol
            user_prompt = self._build_symbol_prompt(symbol, rules_context)

            request = {
                "custom_id": f"symbol-{idx}",  # For result mapping
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000,
                },
            }
            requests.append(request)

        logger.info(f"Created {len(requests)} batch requests")
        return requests

    def _build_symbol_prompt(self, symbol: dict[str, Any], rules_context: str) -> str:
        """Build prompt for a single symbol.

        Args:
            symbol: Symbol dict with name, kind, context, etc.
            rules_context: Rules and guardrails context

        Returns:
            User prompt string
        """
        # Build symbol context
        symbol_info = f"""Symbol to analyze:
Name: {symbol['name']}
Kind: {symbol['kind']}
Context:
```
{symbol.get('context', '')}
```
"""

        # Add annotations if present
        if symbol.get("annotations"):
            annotations_str = ", ".join(symbol["annotations"])
            symbol_info += f"\nAnnotations: {annotations_str}"

        # Combine with rules
        prompt = f"""{rules_context}

{symbol_info}

Analyze this symbol and provide a JSON response following the schema."""

        return prompt

    def submit_batch(
        self,
        requests: list[dict[str, Any]],
        symbols: list[dict[str, Any]],
        description: str = "Named analysis batch",
    ) -> BatchJob:
        """Submit a batch job to OpenAI.

        Args:
            requests: List of batch request dicts
            symbols: Original symbol data for result mapping
            description: Human-readable batch description

        Returns:
            BatchJob object with batch_id for tracking

        Raises:
            Exception: If file upload or batch creation fails
        """
        # Write requests to JSONL format
        jsonl_lines = [json.dumps(req) for req in requests]
        jsonl_content = "\n".join(jsonl_lines)

        # Upload file
        logger.info(f"Uploading batch file with {len(requests)} requests...")
        try:
            file_response = self.client.files.create(
                file=jsonl_content.encode("utf-8"), purpose="batch"
            )
            logger.info(f"File uploaded successfully: {file_response.id}")
        except Exception as e:
            logger.error(f"Failed to upload batch file: {e}")
            raise

        # Create batch
        logger.info(f"Creating batch job (file_id={file_response.id})...")
        try:
            batch_response = self.client.batches.create(
                input_file_id=file_response.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={"description": description},
            )
            logger.info(f"Batch created successfully: {batch_response.id}")
        except Exception as e:
            logger.error(f"Failed to create batch: {e}")
            raise

        return BatchJob(
            batch_id=batch_response.id,
            input_file_id=file_response.id,
            status=batch_response.status,
            symbols=symbols,
            created_at=batch_response.created_at,
        )

    def poll_batch(
        self, batch_job: BatchJob, poll_interval: int = 60, timeout: int = 25 * 3600
    ) -> BatchJob:
        """Poll batch status until completion.

        Args:
            batch_job: BatchJob to monitor
            poll_interval: Seconds between status checks (default: 60)
            timeout: Max seconds to wait before giving up (default: 25 hours)

        Returns:
            Updated BatchJob with completion status

        Raises:
            TimeoutError: If batch doesn't complete within timeout
            RuntimeError: If batch fails, expires, or is cancelled
        """
        start_time = time.time()

        logger.info(f"Polling batch {batch_job.batch_id}...")

        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Batch {batch_job.batch_id} exceeded timeout ({timeout}s)"
                )

            # Get current status
            try:
                batch_response = self.client.batches.retrieve(batch_job.batch_id)
                batch_job.status = batch_response.status

                logger.info(
                    f"Batch status: {batch_job.status} (elapsed: {int(elapsed)}s)"
                )

                # Check completion states
                if batch_response.status == "completed":
                    batch_job.completed_at = batch_response.completed_at
                    batch_job.output_file_id = batch_response.output_file_id
                    logger.info(
                        f"Batch completed! Output file: {batch_job.output_file_id}"
                    )
                    return batch_job

                elif batch_response.status in ["failed", "expired", "cancelled"]:
                    batch_job.error = f"Batch {batch_response.status}"
                    logger.error(f"Batch failed with status: {batch_response.status}")
                    raise RuntimeError(batch_job.error)

                # Still processing
                time.sleep(poll_interval)

            except Exception as e:
                if isinstance(e, (TimeoutError, RuntimeError)):
                    raise
                logger.warning(f"Error polling batch status: {e}")
                time.sleep(poll_interval)

    def download_results(self, batch_job: BatchJob) -> list[dict[str, Any]]:
        """Download and parse batch results.

        Args:
            batch_job: Completed BatchJob with output_file_id

        Returns:
            List of response dicts with custom_id for mapping

        Raises:
            ValueError: If batch job has no output file
            Exception: If download or parsing fails
        """
        if not batch_job.output_file_id:
            raise ValueError("Batch job has no output file")

        logger.info(f"Downloading results from {batch_job.output_file_id}...")

        try:
            # Download JSONL results
            file_response = self.client.files.content(batch_job.output_file_id)
            content = file_response.read()

            # Parse JSONL (one response per line)
            results = []
            for line in content.decode("utf-8").strip().split("\n"):
                if line:
                    results.append(json.loads(line))

            logger.info(f"Downloaded {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Failed to download results: {e}")
            raise

    def parse_batch_results(
        self, results: list[dict[str, Any]], batch_job: BatchJob
    ) -> dict[int, dict[str, Any]]:
        """Parse batch results and map to symbol indices.

        Args:
            results: Raw batch API responses
            batch_job: BatchJob with original symbol data

        Returns:
            Dict mapping symbol index to parsed suggestion

        Example:
            >>> parsed = client.parse_batch_results(results, batch_job)
            >>> parsed[0]["needs_rename"]
            True
            >>> parsed[0]["suggestion"]["suggested_name"]
            'calculateTotal'
        """
        parsed = {}

        for result in results:
            # Extract custom_id (e.g., "symbol-42")
            custom_id = result.get("custom_id", "")
            if not custom_id.startswith("symbol-"):
                logger.warning(f"Invalid custom_id: {custom_id}")
                continue

            # Extract symbol index
            try:
                symbol_idx = int(custom_id.split("-")[1])
            except (IndexError, ValueError):
                logger.warning(f"Failed to parse symbol index from {custom_id}")
                continue

            # Parse LLM response
            response_body = result.get("response", {}).get("body", {})
            choices = response_body.get("choices", [])

            if not choices:
                logger.warning(f"No choices in response for {custom_id}")
                continue

            # Extract message content (JSON string)
            content = choices[0].get("message", {}).get("content", "")

            try:
                suggestion_data = json.loads(content)
                parsed[symbol_idx] = suggestion_data
                logger.debug(f"Parsed result for {custom_id}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON for {custom_id}: {e}")
                continue

        logger.info(f"Successfully parsed {len(parsed)} results")
        return parsed

    def get_batch_status(self, batch_id: str) -> str:
        """Get current status of a batch job.

        Args:
            batch_id: ID of the batch to check

        Returns:
            Current status string (validating, in_progress, completed, failed, expired, cancelled)
        """
        try:
            batch_response = self.client.batches.retrieve(batch_id)
            return batch_response.status
        except Exception as e:
            logger.error(f"Failed to get batch status: {e}")
            raise
