import asyncio
import json
import os
import sys
from typing import AsyncIterator, Any

from src.messages import constants

working_dir = constants.env_config.WORKING_DIR

# Platform detection
IS_WINDOWS = sys.platform == 'win32'

if not IS_WINDOWS:
    import pty
    import select


class AsyncClaudeCLI:
    def __init__(self, model: str = "sonnet"):
        self.model = model

    async def send_prompt(self, prompt: str) -> str:
        """
        Send a prompt to Claude CLI and return the complete response as a string

        Args:
            prompt: The text prompt to send to Claude

        Returns:
            Complete response from Claude as a string
        """
        responses = []

        async for response_data in self.send_prompt_stream(prompt):
            if response_data.get('type') == 'text':
                responses.append(response_data.get('text', ''))

        return ''.join(responses)

    async def send_prompt_stream(
            self,
            prompt: str,
    ) -> AsyncIterator[dict[Any, Any]]:
        """
        Send a prompt to Claude CLI and yield streaming responses

        Args:
            prompt: The text prompt to send to Claude

        Yields:
            Dict containing parsed JSON responses from Claude CLI
        """
        if IS_WINDOWS:
            async for response in self._send_prompt_stream_windows(prompt):
                yield response
        else:
            async for response in self._send_prompt_stream_unix(prompt):
                yield response

    async def _send_prompt_stream_windows(
            self,
            prompt: str,
    ) -> AsyncIterator[dict[Any, Any]]:
        """Windows implementation using PIPE"""
        # Build Claude CLI command
        args = [
            'claude',
            '--continue',
            '--output-format', 'stream-json',
            '--verbose',
            '--print', prompt,
        ]

        # Start Claude process with PIPE
        process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=working_dir,
        )

        buffer = b""

        try:
            # Read output line by line
            while True:
                try:
                    # Read with timeout
                    chunk = await asyncio.wait_for(
                        process.stdout.read(1024),
                        timeout=0.1
                    )

                    if not chunk:
                        break

                    buffer += chunk

                    # Process complete lines
                    while b'\n' in buffer:
                        line_bytes, buffer = buffer.split(b'\n', 1)
                        line = line_bytes.decode('utf-8', errors='replace').strip()

                        if not line:
                            continue

                        try:
                            # Parse JSON response
                            response = json.loads(line)
                            yield response
                        except json.JSONDecodeError:
                            # If not JSON, yield as raw text
                            yield {'type': 'raw', 'text': line}

                except asyncio.TimeoutError:
                    # No data available, check if process is still running
                    if process.returncode is not None:
                        break
                    continue

            # Process any remaining buffer
            if buffer:
                remaining_text = buffer.decode('utf-8', errors='replace').strip()
                if remaining_text:
                    for line in remaining_text.split('\n'):
                        line = line.strip()
                        if line:
                            try:
                                response = json.loads(line)
                                yield response
                            except json.JSONDecodeError:
                                yield {'type': 'raw', 'text': line}

            # Wait for process to complete
            await process.wait()

            # Handle any errors
            if process.returncode != 0:
                raise RuntimeError(f"Claude CLI failed with code {process.returncode}")

        finally:
            # Make sure process is terminated
            if process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

    async def _send_prompt_stream_unix(
            self,
            prompt: str,
    ) -> AsyncIterator[dict[Any, Any]]:
        """Unix implementation using PTY"""
        master, slave = pty.openpty()
        process = None
        try:
            # Build Claude CLI command
            args = [
                'claude',
                '--continue',
                '--output-format', 'stream-json',
                '--verbose',
                '--print', prompt,
            ]

            # Start Claude process with PTY
            process = await asyncio.create_subprocess_exec(
                *args,
                stdin=slave,
                stdout=slave,
                stderr=slave,
                cwd=working_dir,
            )

            # Close slave in parent process
            os.close(slave)

            # Read output asynchronously
            buffer = b""

            while True:
                try:
                    # Check if data is available to read (non-blocking)
                    ready, _, _ = select.select([master], [], [], 0.1)

                    if ready:
                        chunk = os.read(master, 1024)
                        if not chunk:
                            break

                        buffer += chunk

                        # Process complete lines
                        while b'\n' in buffer:
                            line_bytes, buffer = buffer.split(b'\n', 1)
                            line = line_bytes.decode('utf-8', errors='replace').strip()

                            if not line:
                                continue

                            try:
                                # Parse JSON response
                                response = json.loads(line)
                                yield response
                            except json.JSONDecodeError:
                                # If not JSON, yield as raw text
                                yield {'type': 'raw', 'text': line}

                    # Check if process is still running
                    if process.returncode is not None:
                        # Process finished, read all remaining data
                        while True:
                            try:
                                remaining = os.read(master, 1024)
                                if not remaining:
                                    break
                                buffer += remaining
                            except OSError:
                                break
                        break

                    # Yield control to other coroutines
                    await asyncio.sleep(0.01)

                except OSError:
                    break

            # Process any remaining buffer
            if buffer:
                remaining_text = buffer.decode('utf-8', errors='replace').strip()
                if remaining_text:
                    for line in remaining_text.split('\n'):
                        line = line.strip()
                        if line:
                            try:
                                response = json.loads(line)
                                yield response
                            except json.JSONDecodeError:
                                yield {'type': 'raw', 'text': line}

            # Wait for process to complete
            await process.wait()

            # Handle any errors
            if process.returncode != 0:
                raise RuntimeError(f"Claude CLI failed with code {process.returncode}")

        finally:
            # Clean up
            try:
                os.close(master)
            except OSError:
                pass

            # Make sure process is terminated
            if process is not None and process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
