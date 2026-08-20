"""Serialized git commit queue — prevents concurrent push conflicts.

On approval, the review router enqueues a commit. Background worker
processes one commit at a time (asyncio.Queue). Max 3 retries with
exponential backoff on push failure.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class GitCommitTask:
    file_path: str
    content: str
    commit_message: str
    entity_type: str
    entity_id: str


_queue: asyncio.Queue[GitCommitTask] = asyncio.Queue()
_worker_started = False


async def enqueue_commit(task: GitCommitTask) -> None:
    """Add a git commit task to the serial queue."""
    await _queue.put(task)


async def _process_commit(task: GitCommitTask) -> None:
    """Write file and push to remote. Retries up to 3 times."""
    import pathlib
    import subprocess

    if not settings.GIT_REMOTE_URL:
        logger.warning("GIT_REMOTE_URL not set — skipping git commit")
        return

    repo_dir = pathlib.Path(settings.GIT_REPO_LOCAL_PATH)
    if not repo_dir.exists():
        logger.warning("Git repo path does not exist: %s", repo_dir)
        return

    for attempt in range(3):
        try:
            file_path = repo_dir / task.file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(task.content, encoding="utf-8")

            subprocess.run(
                ["git", "add", str(file_path)], cwd=repo_dir, check=True
            )
            subprocess.run(
                ["git", "commit", "-m", task.commit_message, "--allow-empty"],
                cwd=repo_dir,
                check=True,
            )
            subprocess.run(
                ["git", "push", "origin", "main"], cwd=repo_dir, check=True
            )
            logger.info(
                "Git commit OK: %s/%s", task.entity_type, task.entity_id
            )
            return
        except subprocess.CalledProcessError as exc:
            wait = 2**attempt  # 1s, 2s, 4s
            logger.warning(
                "Git push failed (attempt %d/3): %s. Retrying in %ds",
                attempt + 1,
                exc,
                wait,
            )
            if attempt < 2:
                await asyncio.sleep(wait)

    logger.error(
        "Git commit permanently failed after 3 attempts: %s/%s",
        task.entity_type,
        task.entity_id,
    )


async def _queue_worker() -> None:
    """Process git commits serially from the queue."""
    while True:
        task = await _queue.get()
        try:
            await _process_commit(task)
        except Exception as exc:
            logger.error("Unexpected error in git queue worker: %s", exc)
        finally:
            _queue.task_done()


def start_git_queue_worker(app: object) -> None:  # noqa: ARG001
    """Call this from app startup event to launch the background worker."""
    global _worker_started
    if not _worker_started:
        asyncio.get_event_loop().create_task(_queue_worker())
        _worker_started = True
