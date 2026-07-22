"""Run GraphRAG with certifi instead of the malformed Windows CA store."""

import ssl

import certifi


_original_create_default_context = ssl.create_default_context


def _create_certifi_context(*args, **kwargs):
    if not any(kwargs.get(name) is not None for name in ("cafile", "capath", "cadata")):
        kwargs["cafile"] = certifi.where()
    return _original_create_default_context(*args, **kwargs)


ssl.create_default_context = _create_certifi_context

from graphrag.cli.main import app


if __name__ == "__main__":
    app(prog_name="graphrag")
