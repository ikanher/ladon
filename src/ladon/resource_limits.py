"""Shared defaults and user-facing diagnostics for supervised process limits."""

DEFAULT_MAX_RSS_MIB = 12 * 1024
DEFAULT_MAX_RSS_BYTES = DEFAULT_MAX_RSS_MIB * 1024 * 1024


def memory_limit_message(
    cap_bytes: int | None, peak_bytes: int | None = None, *, supports_override: bool = True,
) -> str:
    """Explain a measured memory failure without guessing missing measurements."""
    message = "Stop progress and report back to user: process memory limit reached."
    if cap_bytes is not None:
        message += f" Configured process-tree RSS limit: {cap_bytes / 1024**3:g} GiB ({cap_bytes} bytes)."
    if peak_bytes is not None:
        message += f" Observed sampled peak {peak_bytes / 1024**3:g} GiB ({peak_bytes} bytes)."
    message += " Ask the user before retrying"
    if supports_override:
        message += " with a higher --max-rss-mib limit."
    else:
        message += "."
    return message
