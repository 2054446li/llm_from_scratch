# Repository Guidelines

## Project Structure & Module Organization

This repository is a Chinese-language knowledge base for LLM engineering and interview preparation. Core teaching material lives in `docs/`, topic notes in `common_knowledge/`, question banks in `qa/`, and the focused interview curriculum in `interview_prep/`. Keep post-training material under `post_training/`; place model and company analyses, source PDFs, and their reading notes in `industry_reports/` or `paper/`. Jupyter demonstrations belong in `code/`, reusable plotting utilities in `scripts/`, generated figures in `assets/`, and curated SOP datasets in `data/`.

## Build, Test, and Development Commands

There is no package build or automated test suite. Work from the repository root so relative asset paths resolve correctly.

- `source .venv/bin/activate` activates the existing local Python environment when available.
- `jupyter lab code/` opens the computational examples for editing and execution.
- `python scripts/plot_silu.py` regenerates `assets/silu_curve.png`.
- `python scripts/plot_flash_attention.py` regenerates the Flash Attention diagram.
- `python -m compileall scripts` performs a quick syntax check on utility scripts.

Do not assume dependencies are reproducible from a lockfile; none is currently committed.

## Coding Style & Naming Conventions

Write explanatory prose in Simplified Chinese and preserve the existing direct, instructional tone. Use Markdown headings hierarchically, fenced code blocks for examples, and LaTeX for formulas: `$x$` inline and `$$...$$` for display equations. Follow existing numbered topic names such as `14_ppo.md`; use lowercase `snake_case` for new Python and descriptive Markdown filenames. Python uses four-space indentation, standard PEP 8 spacing, and comments only where they clarify the mathematics or visualization.

## Testing Guidelines

For Markdown changes, preview rendering and verify local links, tables, code fences, and equations. For notebooks, restart the kernel and run all cells in order before committing; clear accidental tracebacks and avoid committing checkpoint files. For plotting changes, run the affected script and inspect both the image and `git diff --stat` for unexpected generated files.

## Commit & Pull Request Guidelines

The short history uses brief plain-language subjects (for example, `add pdf`); no formal convention is established. Prefer a concise imperative subject with a scope when useful, such as `docs: explain DPO loss`. Keep unrelated notes, notebooks, datasets, and binaries in separate commits. Pull requests should summarize the learning-content change, list key paths, identify source papers or links, and include before/after images when diagrams or notebook output changes. Note any large PDFs or datasets explicitly and link the relevant issue when one exists.
