"""Run GraphRAG, applying the Windows CA-store workaround only when needed."""

import ssl
import sys

import certifi


def _enable_windows_certifi_context() -> None:
    """Use certifi only for Windows, where the system CA store can be malformed."""
    original_create_default_context = ssl.create_default_context


    def create_certifi_context(*args, **kwargs):
        if not any(kwargs.get(name) is not None for name in ("cafile", "capath", "cadata")):
            kwargs["cafile"] = certifi.where()
        return original_create_default_context(*args, **kwargs)

    ssl.create_default_context = create_certifi_context


if sys.platform.startswith("win"):
    _enable_windows_certifi_context()

from graphrag.cli.main import app


if __name__ == "__main__":
    app(prog_name="graphrag")
