from __future__ import annotations

import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Queue


@dataclass(frozen=True, slots=True)
class CommandResult:
    label: str
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    started_at: str
    finished_at: str


class CommandRunner:
    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root
        self._results: Queue[CommandResult] = Queue()
        self._active_lock = threading.Lock()
        self._active = False

    def is_busy(self) -> bool:
        with self._active_lock:
            return self._active

    def start(self, *, label: str, module: str, args: tuple[str, ...] = ()) -> bool:
        with self._active_lock:
            if self._active:
                return False
            self._active = True

        thread = threading.Thread(
            target=self._run_command,
            kwargs={"label": label, "module": module, "args": args},
            daemon=True,
        )
        thread.start()
        return True

    def get_result_nowait(self) -> CommandResult | None:
        try:
            return self._results.get_nowait()
        except Empty:
            return None

    def _run_command(self, *, label: str, module: str, args: tuple[str, ...]) -> None:
        argv = (sys.executable, "-m", module, *args)
        started_at = datetime.now(timezone.utc).isoformat()

        try:
            completed = subprocess.run(
                argv,
                cwd=self._repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            returncode = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except Exception as exc:  # pragma: no cover - defensive subprocess guard
            returncode = 1
            stdout = ""
            stderr = f"{type(exc).__name__}: {exc}"
        finally:
            finished_at = datetime.now(timezone.utc).isoformat()
            with self._active_lock:
                self._active = False

        self._results.put(
            CommandResult(
                label=label,
                argv=argv,
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
                started_at=started_at,
                finished_at=finished_at,
            )
        )
