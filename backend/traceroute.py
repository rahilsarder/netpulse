from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Tuple


@dataclass
class TraceResult:
    summary: str
    output: str


class TraceRunner:
    def run_incident_trace(self, target: str) -> TraceResult:
        # Try mtr first, then fall back to traceroute when mtr is unavailable
        # or cannot open raw sockets in the current runtime environment.
        mtr_command = ["mtr", "-r", "-c", "10", target]
        try:
            mtr_code, mtr_output = self._run_command(mtr_command, timeout=30)
            if mtr_code == 0 and mtr_output:
                summary = self._build_summary(mtr_output, tool_name="mtr")
                return TraceResult(summary=summary, output=mtr_output)

            if self._looks_like_socket_error(mtr_output):
                traceroute_result = self._run_traceroute_fallback(target)
                if traceroute_result is not None:
                    return traceroute_result

            # Return mtr output even when non-zero if it contains useful details.
            summary = self._build_summary(mtr_output, tool_name="mtr")
            return TraceResult(summary=summary, output=mtr_output)
        except FileNotFoundError:
            traceroute_result = self._run_traceroute_fallback(target)
            if traceroute_result is not None:
                return traceroute_result
            return TraceResult(summary="trace tools missing", output=self._missing_tools_text())
        except subprocess.TimeoutExpired:
            return TraceResult(
                summary="mtr timeout",
                output="mtr execution timed out after 30 seconds.",
            )

    @staticmethod
    def _build_summary(output: str, tool_name: str) -> str:
        if not output:
            return "Empty trace output"

        lines = [line.strip() for line in output.splitlines() if line.strip()]
        hop_lines = [line for line in lines if line[:1].isdigit()]
        if len(hop_lines) < 1:
            return "Insufficient hops captured"

        return f"Captured {len(hop_lines)} hop lines from {tool_name} output"

    @staticmethod
    def _run_command(command: list[str], timeout: int) -> Tuple[int, str]:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
        output = (completed.stdout or "").strip() or (completed.stderr or "").strip()
        return completed.returncode, output

    @staticmethod
    def _looks_like_socket_error(output: str) -> bool:
        text = output.lower()
        socket_indicators = [
            "failure to open ipv4 sockets",
            "failure to open ipv6 sockets",
            "failure to start mtr-packet",
            "operation not permitted",
            "permission denied",
        ]
        return any(indicator in text for indicator in socket_indicators)

    def _run_traceroute_fallback(self, target: str) -> TraceResult | None:
        commands = [
            ["traceroute", "-n", "-q", "1", "-m", "20", target],
            ["traceroute", target],
        ]

        for command in commands:
            try:
                code, output = self._run_command(command, timeout=30)
                if code == 0 and output:
                    summary = self._build_summary(output, tool_name="traceroute")
                    return TraceResult(summary=f"{summary} (fallback from mtr)", output=output)
                if output:
                    return TraceResult(
                        summary="traceroute failed after mtr fallback",
                        output=output,
                    )
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                return TraceResult(
                    summary="traceroute timeout after mtr fallback",
                    output="traceroute execution timed out after 30 seconds.",
                )
        return None

    @staticmethod
    def _missing_tools_text() -> str:
        return (
            "Neither mtr nor traceroute is available on host.\n"
            "Install one of the following:\n"
            "- Ubuntu/Debian: apt install mtr-tiny traceroute\n"
            "- macOS: brew install mtr traceroute"
        )
