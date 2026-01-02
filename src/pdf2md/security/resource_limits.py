"""Resource limits for sandbox execution."""

import os
import platform
import resource as resource_module
from dataclasses import dataclass


@dataclass
class ResourceLimits:
    """Resource limits for sandboxed execution."""

    memory_limit_mb: int
    timeout_seconds: int
    cpu_limit_seconds: int | None = None


def apply_resource_limits(limits: ResourceLimits) -> None:
    """
    Apply resource limits to current process.

    This function is called within the sandboxed worker process
    to enforce memory and CPU limits.

    Args:
        limits: Resource limits to apply

    Note:
        Resource limiting is platform-dependent:
        - Linux/Mac: Uses resource.setrlimit()
        - Windows: Limited support (timeout only)
    """
    system = platform.system()

    if system in ("Linux", "Darwin"):  # Linux or macOS
        # Set memory limit (address space)
        memory_bytes = limits.memory_limit_mb * 1024 * 1024
        try:
            resource_module.setrlimit(
                resource_module.RLIMIT_AS, (memory_bytes, memory_bytes)
            )
        except (ValueError, OSError):
            # May fail if limit is too low or permission denied
            pass

        # Set CPU time limit if specified
        if limits.cpu_limit_seconds:
            try:
                resource_module.setrlimit(
                    resource_module.RLIMIT_CPU,
                    (limits.cpu_limit_seconds, limits.cpu_limit_seconds),
                )
            except (ValueError, OSError):
                pass

    elif system == "Windows":
        # Windows has limited resource control via resource module
        # Timeout is enforced by ProcessPoolExecutor.result(timeout=...)
        # Memory limiting on Windows requires job objects (win32 API)
        pass


def get_current_memory_mb() -> float:
    """
    Get current process memory usage in MB.

    Returns:
        Memory usage in megabytes
    """
    try:
        import psutil

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss / (1024 * 1024)
    except ImportError:
        # psutil not available, return 0
        return 0.0
