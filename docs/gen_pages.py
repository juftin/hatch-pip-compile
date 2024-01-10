"""
Generate the code reference pages and navigation.
"""

import logging
from pathlib import Path

import mkdocs_gen_files

logger = logging.getLogger(__name__)

project_dir = Path(__file__).resolve().parent.parent
source_code = project_dir.joinpath("hatch_pip_compile")

for path in sorted(source_code.rglob("*.py")):
    module_path = path.relative_to(project_dir).with_suffix("")
    doc_path = path.relative_to(source_code).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        fd.write(f"# `{parts[-1]}`\n\n::: {'.'.join(parts)}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

readme_content = Path("README.md").read_text(encoding="utf-8")
# Exclude parts that are between two exact `<!--skip-->` lines
readme_content = "\n".join(readme_content.split("\n<!--skip-->\n")[::2])
with mkdocs_gen_files.open("index.md", "w") as index_file:
    index_file.write(readme_content)
