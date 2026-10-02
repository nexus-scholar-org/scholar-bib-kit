"""E3/T-110b regression guard: no relative editable sibling source, direct ref.

scholar-bib-kit declared ``"scholar-search-kit"`` as a BARE name that was only
resolvable through the relative editable ``[tool.uv.sources]`` entry
``scholar-search-kit = { path = "../scholar-search-kit", editable = true }``.
That entry resolves only inside the harness monorepo (or beside a sibling
checkout on disk). For a standalone ``uv pip install`` of this kit's wheel the
requirement was unresolvable, and for a git checkout of this kit alone the
relative path does not exist at all -- pip/uv aborts with
``has no subdirectory '../scholar-search-kit'``.

This test locks in the T-110b fix: the sibling is a PEP 508 direct git
reference pinned to a full 40-hex canonical SHA and no relative path source may
come back. It is hermetic -- it reads the checked-in ``pyproject.toml`` only and
never touches the network. When a wheel has already been built into ``dist/``,
the built METADATA is additionally checked.
"""

from __future__ import annotations

import re
import tomllib
import zipfile
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"

# scholar-<name>[@ git+https://github.com/nexus-scholar-org/scholar-<name>@<40-hex>]
# with an optional PEP 508 extras suffix, e.g. scholar-pdf-kit[extract].
DIRECT_REF = re.compile(
    r"^scholar-[a-z0-9-]+(\[[a-z0-9,.-]+\])? @ git\+https://github\.com/nexus-scholar-org/scholar-[a-z0-9-]+@[0-9a-f]{40}$"
)

# The canonical main SHA recorded at E3/T-110 dispatch time.
EXPECTED_SHA = {
    "scholar-search-kit": "911d864fcb6a706d4c0339f80524a46f591e2cad",
}


def _load() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def test_every_sibling_is_a_sha_pinned_direct_git_reference() -> None:
    deps = _load()["project"]["dependencies"]
    siblings = [d for d in deps if d.startswith("scholar-")]
    assert siblings, "expected declared scholar-* sibling requirements"

    for dep in siblings:
        assert DIRECT_REF.match(dep), f"not a SHA-pinned direct git reference: {dep!r}"

    declared = {re.split(r"[ @\[]", d, maxsplit=1)[0]: d for d in siblings}
    assert set(declared) == set(EXPECTED_SHA), (
        f"unexpected sibling set: {sorted(declared)}"
    )
    for name, sha in EXPECTED_SHA.items():
        assert declared[name].endswith(sha), (
            f"{name} is not pinned to canonical main {sha}: {declared[name]!r}"
        )


def test_no_relative_editable_sibling_source_can_come_back() -> None:
    sources = _load().get("tool", {}).get("uv", {}).get("sources", {})
    relative = {
        name: src
        for name, src in sources.items()
        if isinstance(src, dict) and "path" in src
    }
    assert not relative, (
        f"relative sibling sources break standalone installs: {relative}"
    )


def test_built_wheel_metadata_carries_the_direct_refs() -> None:
    wheels = sorted((PYPROJECT.parent / "dist").glob("*.whl"))
    if not wheels:
        import pytest

        pytest.skip("no built wheel in dist/; run `uv build --wheel .` first")

    metadata_name = next(
        n
        for n in zipfile.ZipFile(wheels[-1]).namelist()
        if n.endswith(".dist-info/METADATA")
    )
    requires = [
        line.removeprefix("Requires-Dist: ")
        for line in zipfile.ZipFile(wheels[-1])
        .read(metadata_name)
        .decode()
        .splitlines()
        if line.startswith("Requires-Dist: ")
    ]
    git_requires = [r for r in requires if "git+" in r]
    assert len(git_requires) == len(EXPECTED_SHA), (
        f"expected {len(EXPECTED_SHA)} git direct refs, got {git_requires}"
    )
    for name, sha in EXPECTED_SHA.items():
        assert any(name in r and r.endswith(sha) for r in git_requires), (
            f"missing {name}@{sha} in METADATA"
        )
