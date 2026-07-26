"""Code execution tool — runs Python in a subprocess sandbox with timeout."""
import asyncio
import sys
import logging

logger = logging.getLogger(__name__)

TIMEOUT = 10  # seconds
MAX_OUTPUT = 2000  # chars


async def execute_python(code: str) -> str:
    """Execute Python code in a sandboxed subprocess and return stdout/stderr."""
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            await asyncio.shield(asyncio.create_task(proc.wait()))
            return f"[Timeout] Execution exceeded {TIMEOUT}s limit"

        out = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip()

        result_parts = []
        if out:
            result_parts.append(f"```\n{out}\n```")
        if err:
            result_parts.append(f"⚠️ stderr:\n```\n{err}\n```")
        if not result_parts:
            return "✅ Code executed successfully (no output)"

        result = "\n".join(result_parts)
        if len(result) > MAX_OUTPUT:
            result = result[:MAX_OUTPUT] + "\n…（output truncated）"
        return result

    except Exception as e:
        logger.error(f"Code execution error: {e}")
        return f"❌ Execution error: {e}"
