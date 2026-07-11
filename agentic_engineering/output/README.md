# Output Folder

This folder stores the actual work products produced by the program.

In the legacy folder-copy layout this may include generated program artifacts. In the preferred overlay layout, the product repository remains at its natural root beside `.agentic/`; do not place the product source in a nested `output/repositories` Git repository.

## Suggested Structure

| Folder | Purpose |
|---|---|
| `repositories` | Legacy only: links or references to external product repositories, not nested source repositories. |
| `documentation` | Product documentation, technical documentation, API docs, and release notes. |
| `deliverables` | Generated files, exported reports, demos, and customer-facing artifacts. |
| `release_packages` | Build outputs, deployment bundles, installers, or release archives. |

## Rules

- Source code should live in a git repository whenever possible.
- Keep generated release artifacts separate from source files.
- Link major outputs back to program trackers, requirements, and release records.
- Do not mix temporary scratch work with final deliverables.
