# EHA LaTeX v1.1 Migration Checklist

Date: 2026-05-15

## Deliverables And Success Criteria

- Create a canonical LaTeX manuscript under `paper/`.
- Compile the manuscript with `make pdf` and produce `paper/main.pdf`.
- Replace related-work TODOs in the formal manuscript with verified citations and BibTeX.
- Use real PDF figures with captions and labels, not artifact-path placeholders.
- Preserve fixed model order: `gpt-5.4`, `claude-opus-4-7`, `gemini-3.1-pro-preview`, `deepseek-v4-pro`, `kimi-k2.6`.
- Add uncertainty for main operational escape and keep descriptive/n caveats.
- Formalize reproducibility appendices for dataset construction, scoring contract, model invocation, extra tables, and artifact map.
- Preserve the no-temperature/no-cap model-selection diagnostic: empty outputs under capped profiles should not be treated as upstream model unavailability.
- Run an external Codex CLI GPT-5.5 xhigh read-only audit through tmux.

## Prompt-To-Artifact Checklist

| Requirement | Artifact | Status |
| --- | --- | --- |
| LaTeX manuscript is canonical | `paper/main.tex`, `paper/sections/*.tex`, `paper/appendix/*.tex` | Done |
| PDF builds | `paper/main.pdf` via `paper/Makefile` | Done |
| Related work has verified citations | `paper/sections/07_related_work.tex`, `paper/references.bib` | Done |
| Figures are paper figures with captions/labels | `paper/figures/*.pdf`, figure environments in sections | Done |
| Booktabs tables and fixed provider order | `paper/tables/*.tex` | Done |
| Wilson intervals for operational escape | `paper/tables/main_model_decomposition.tex` | Done |
| Dataset and scoring reproducibility appendix | `paper/appendix/a_dataset_construction.tex`, `paper/appendix/b_scoring_contract.tex` | Done |
| Model invocation and cap/no-cap diagnostic | `paper/appendix/c_model_invocation.tex`, model-selection artifacts | Done |
| External GPT-5.5 xhigh audit | `.codex-workflows/eha-latex-v11-audit/reviewer/review-to-worker.md` | Done |
| Old Markdown not canonical | `epistemic-hygiene-arena-preprint.md` status line | Done |

## Verification

- `make pdf` in `paper/` succeeded with `tectonic main.tex`.
- `pdfinfo paper/main.pdf` reports 17 pages and no encryption.
- `pdftotext paper/main.pdf -` contains no TODO, unresolved `??`, or undefined-reference text.
- Figure PDFs are one-page PDFs and rendered nonblank in raster checks:
  - `fig1_task_schematic.pdf`: nonwhite ratio 0.1006
  - `fig2_capability_decomposition.pdf`: nonwhite ratio 0.2645
  - `fig3_task_family_breakdown.pdf`: nonwhite ratio 0.2401
  - `fig4_generated_lore_role_decomposition.pdf`: nonwhite ratio 0.2598
  - `fig5_prompt_hygiene_slope.pdf`: nonwhite ratio 0.0588
- GPT-5.5 xhigh read-only reviewer returned `status: no_issues`.

## Residual Risks

- The reproducibility appendix is intentionally concise; a venue submission should add exact dataset seed, full family-by-condition cross distribution, and more scorer edge-case examples.
- `make pdf` emits one underfull hbox warning in `appendix/c_model_invocation.tex`; it is not a build failure.
- Bibliography entries were checked against primary or bibliographic source pages, but a final submission should still do venue-style bibliography formatting.
