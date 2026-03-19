"""OpenAI Batch API client for asynchronous symbol analysis."""

import io
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from named.logging import get_logger
from named.suggestions.client_factory import create_openai_client
from named.suggestions.common import (
    CHUNK_SIZE,
    CHUNK_THRESHOLD,
    TOKENS_BASE,
    TOKENS_MAX,
    TOKENS_MIN,
    TOKENS_PER_SYMBOL,
    strip_markdown_fences,
)

logger = get_logger("batch_client")


@dataclass
class BatchJob:
    """Represents a batch processing job.

    Attributes:
        batch_id: Unique identifier for the batch job
        input_file_id: ID of the uploaded input JSONL file
        status: Current status (validating, in_progress, completed, failed, expired, cancelled)
        symbols: Original symbol data for result mapping (flat list)
        created_at: Unix timestamp when batch was created
        completed_at: Unix timestamp when batch completed (if completed)
        output_file_id: ID of the output file containing results (if completed)
        error: Error message if batch failed
        file_map: Maps custom_id -> [global_start_idx, symbol_count] for per-file results
    """

    batch_id: str
    input_file_id: str
    status: str
    symbols: list[dict[str, Any]]
    created_at: int
    completed_at: int | None = None
    output_file_id: str | None = None
    error: str | None = None
    file_map: dict[str, list[int]] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert BatchJob to dictionary for serialization."""
        d = {
            "batch_id": self.batch_id,
            "input_file_id": self.input_file_id,
            "status": self.status,
            "symbols": self.symbols,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "output_file_id": self.output_file_id,
            "error": self.error,
        }
        if self.file_map is not None:
            d["file_map"] = self.file_map
        return d


class BatchAnalysisClient:
    """Client for batch analysis using OpenAI Batch API.

    This client handles the full workflow of batch processing:
    1. Create batch requests in JSONL format (one per file, using full source context)
    2. Upload to OpenAI and submit batch job
    3. Poll status until completion
    4. Download and parse results
    5. Map results back to original symbols
    """

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None):
        """Initialize batch analysis client."""
        self.client = create_openai_client(api_key=api_key, base_url=base_url)
        self.model = model

    def create_file_batch_requests(
        self,
        file_groups: list[dict[str, Any]],
        system_prompt: str,
        rules_context: str,
    ) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
        """Generate batch requests grouped by file, using the same FileAnalysisPrompt as streaming.

        Each file becomes one JSONL request (or multiple if chunked for large files).
        This matches the streaming mode behavior exactly.

        Args:
            file_groups: List of dicts with keys:
                - file_path: str path to the Java file
                - file_source: Full source code of the file
                - symbols: List of symbol dicts for this file
            system_prompt: System role message
            rules_context: Rules and guardrails context

        Returns:
            Tuple of (requests, file_map) where:
                - requests: List of JSONL request dicts
                - file_map: Maps custom_id -> [global_start_idx, symbol_count]
        """
        from named.prompts.analysis import FileAnalysisPrompt

        prompt_builder = FileAnalysisPrompt()
        requests = []
        file_map = {}
        global_idx = 0

        for file_idx, fg in enumerate(file_groups):
            file_path = fg["file_path"]
            file_source = fg["file_source"]
            symbols = fg["symbols"]
            file_name = Path(file_path).name

            # Build symbol dicts for the prompt (same format as streaming)
            symbol_dicts = [
                {
                    "name": s["name"],
                    "kind": s["kind"],
                    "line": s.get("line"),
                    "annotations": (
                        ", ".join(f"@{a}" for a in s["annotations"])
                        if s.get("annotations")
                        else "None"
                    ),
                }
                for s in symbols
            ]

            # Chunk large files (same thresholds as streaming)
            if len(symbols) <= CHUNK_THRESHOLD:
                chunks = [(0, symbols, symbol_dicts)]
            else:
                chunks = []
                for chunk_start in range(0, len(symbols), CHUNK_SIZE):
                    chunk_end = min(chunk_start + CHUNK_SIZE, len(symbols))
                    chunks.append((
                        chunk_start,
                        symbols[chunk_start:chunk_end],
                        symbol_dicts[chunk_start:chunk_end],
                    ))
                logger.info(
                    f"Large file {file_name}: {len(symbols)} symbols → "
                    f"{len(chunks)} chunks of {CHUNK_SIZE}"
                )

            for chunk_idx, (chunk_start, chunk_symbols, chunk_symbol_dicts) in enumerate(chunks):
                custom_id = f"file-{file_idx}-chunk-{chunk_idx}"

                # Render prompt using FileAnalysisPrompt (same as streaming)
                user_prompt = prompt_builder.render(
                    file_name=file_name,
                    file_source=file_source,
                    symbols=chunk_symbol_dicts,
                    rules_context=rules_context,
                )

                # Dynamic max_tokens (same formula as streaming)
                max_tokens = min(
                    max(TOKENS_MIN, len(chunk_symbols) * TOKENS_PER_SYMBOL + TOKENS_BASE),
                    TOKENS_MAX,
                )

                request = {
                    "custom_id": custom_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": max_tokens,
                    },
                }
                requests.append(request)

                # Track mapping: custom_id -> [global_start, count]
                file_map[custom_id] = [global_idx, len(chunk_symbols)]
                global_idx += len(chunk_symbols)

        logger.info(f"Created {len(requests)} file-based batch requests")
        return requests, file_map

    def submit_batch(
        self,
        requests: list[dict[str, Any]],
        symbols: list[dict[str, Any]],
        description: str = "Named analysis batch",
        file_map: dict[str, list[int]] | None = None,
    ) -> BatchJob:
        """Submit a batch job to OpenAI.

        Args:
            requests: List of batch request dicts
            symbols: Original symbol data for result mapping
            description: Human-readable batch description
            file_map: Maps custom_id -> [global_start, count] for per-file results

        Returns:
            BatchJob object with batch_id for tracking
        """
        # Write requests to JSONL format
        jsonl_lines = [json.dumps(req) for req in requests]
        jsonl_content = "\n".join(jsonl_lines)

        # Upload file (filename must end in .jsonl for Azure; expires_after frees quota)
        logger.info(f"Uploading batch file with {len(requests)} requests...")
        try:
            content_bytes = jsonl_content.encode("utf-8")
            file_response = self.client.files.create(
                file=("batch_requests.jsonl", io.BytesIO(content_bytes)),
                purpose="batch",
                expires_after={"anchor": "created_at", "seconds": 259200},  # 3 days
            )
            logger.info(f"File uploaded successfully: {file_response.id}")
        except Exception as e:
            logger.error(f"Failed to upload batch file: {e}")
            raise

        # Create batch (output_expires_after so output files auto-expire too)
        logger.info(f"Creating batch job (file_id={file_response.id})...")
        try:
            batch_response = self.client.batches.create(
                input_file_id=file_response.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={"description": description},
                extra_body={
                    "output_expires_after": {
                        "anchor": "created_at",
                        "seconds": 259200,  # 3 days
                    }
                },
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
            file_map=file_map,
        )

    def poll_batch(
        self, batch_job: BatchJob, poll_interval: int = 60, timeout: int = 25 * 3600
    ) -> BatchJob:
        """Poll batch status until completion."""
        start_time = time.time()
        logger.info(f"Polling batch {batch_job.batch_id}...")

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Batch {batch_job.batch_id} exceeded timeout ({timeout}s)"
                )

            try:
                batch_response = self.client.batches.retrieve(batch_job.batch_id)
                batch_job.status = batch_response.status

                logger.info(
                    f"Batch status: {batch_job.status} (elapsed: {int(elapsed)}s)"
                )

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

                time.sleep(poll_interval)

            except Exception as e:
                if isinstance(e, (TimeoutError, RuntimeError)):
                    raise
                logger.warning(f"Error polling batch status: {e}")
                time.sleep(poll_interval)

    def download_results(self, batch_job: BatchJob) -> list[dict[str, Any]]:
        """Download and parse batch results."""
        if not batch_job.output_file_id:
            raise ValueError("Batch job has no output file")

        logger.info(f"Downloading results from {batch_job.output_file_id}...")

        try:
            file_response = self.client.files.content(batch_job.output_file_id)
            content = file_response.read()

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

        Handles both formats:
        - Per-file (file_map present): each response has {"results": [{"symbol_index": 0, ...}]}
        - Legacy per-symbol: each response is a single suggestion

        Returns:
            Dict mapping global symbol index to parsed suggestion data.
        """
        if batch_job.file_map:
            return self._parse_file_results(results, batch_job)
        return self._parse_legacy_results(results)

    def _parse_file_results(
        self, results: list[dict[str, Any]], batch_job: BatchJob
    ) -> dict[int, dict[str, Any]]:
        """Parse per-file batch results using file_map for index mapping."""
        parsed = {}

        for result in results:
            custom_id = result.get("custom_id", "")

            if custom_id not in batch_job.file_map:
                logger.warning(f"Unknown custom_id in results: {custom_id}")
                continue

            global_start, count = batch_job.file_map[custom_id]

            # Extract LLM response content
            response_body = result.get("response", {}).get("body", {})
            choices = response_body.get("choices", [])

            if not choices:
                logger.warning(f"No choices in response for {custom_id}")
                continue

            content = choices[0].get("message", {}).get("content", "")
            stripped = strip_markdown_fences(content)

            try:
                response_data = json.loads(stripped)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON for {custom_id}: {e}")
                continue

            # Extract results array (same format as streaming response)
            results_array = response_data.get("results", [])
            if not results_array:
                logger.warning(f"No results array in response for {custom_id}")
                continue

            for item in results_array:
                local_idx = item.get("symbol_index")
                if local_idx is None or not isinstance(local_idx, int):
                    continue
                if local_idx < 0 or local_idx >= count:
                    logger.warning(
                        f"symbol_index {local_idx} out of range for {custom_id} (count={count})"
                    )
                    continue

                if not item.get("needs_rename", False):
                    continue

                suggestion = item.get("suggestion")
                if not suggestion:
                    continue

                global_idx = global_start + local_idx
                parsed[global_idx] = item

            logger.debug(f"Parsed results for {custom_id}: {len(results_array)} entries")

        logger.info(f"Successfully parsed {len(parsed)} file-based results")
        return parsed

    def _parse_legacy_results(
        self, results: list[dict[str, Any]]
    ) -> dict[int, dict[str, Any]]:
        """Parse legacy per-symbol batch results (backward compatibility)."""
        parsed = {}

        for result in results:
            custom_id = result.get("custom_id", "")
            if not custom_id.startswith("symbol-"):
                logger.warning(f"Invalid custom_id: {custom_id}")
                continue

            try:
                symbol_idx = int(custom_id.split("-")[1])
            except (IndexError, ValueError):
                logger.warning(f"Failed to parse symbol index from {custom_id}")
                continue

            response_body = result.get("response", {}).get("body", {})
            choices = response_body.get("choices", [])

            if not choices:
                logger.warning(f"No choices in response for {custom_id}")
                continue

            content = choices[0].get("message", {}).get("content", "")
            stripped = strip_markdown_fences(content)

            try:
                suggestion_data = json.loads(stripped)
                parsed[symbol_idx] = suggestion_data
                logger.debug(f"Parsed result for {custom_id}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON for {custom_id}: {e}")
                continue

        logger.info(f"Successfully parsed {len(parsed)} results")
        return parsed

    def get_batch_status(self, batch_id: str) -> str:
        """Get current status of a batch job."""
        try:
            batch_response = self.client.batches.retrieve(batch_id)
            return batch_response.status
        except Exception as e:
            logger.error(f"Failed to get batch status: {e}")
            raise

    def get_batch(self, batch_id: str) -> Any:
        """Get full batch job details (e.g. input_file_id for cleanup)."""
        return self.client.batches.retrieve(batch_id)

    def cancel_batch(self, batch_id: str) -> None:
        """Cancel an in-progress batch job."""
        self.client.batches.cancel(batch_id)
        logger.info(f"Cancelled batch {batch_id}")

    def delete_file(self, file_id: str) -> None:
        """Delete a file from the API."""
        self.client.files.delete(file_id)
        logger.info(f"Deleted file {file_id}")

    def list_files(self, purpose: str | None = "batch", limit: int = 500) -> list[Any]:
        """List files in the API.

        Args:
            purpose: Filter by purpose (default batch); None for all.
            limit: Max files to return per page.

        Returns:
            List of file objects.
        """
        params: dict[str, Any] = {"limit": limit}
        if purpose is not None:
            params["purpose"] = purpose
        page = self.client.files.list(**params)
        return list(page.data)
