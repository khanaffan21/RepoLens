# Remaining production roadmap

- Implement robust GitHub API retries, rate-limit-aware backoff, subtree traversal for truncated trees, file budgets and repository refresh/stale-chunk cleanup.
- Add retrieval quality evaluation, similarity thresholds, hybrid lexical/vector retrieval, reranking and citation validation.
- Add persisted chat histories, user accounts, authorization and repository ownership controls.
- Persist career analyses securely with retention/deletion controls; support DOCX and scanned-PDF OCR only with explicit consent.
- Replace starter skill maps with job-description ingestion from a permitted provider, source URLs and retrieval dates.
- Improve GitHub evidence by inspecting selected repository contents; never infer authorship or proficiency from commit counts alone.
- Add report export, frontend validation/accessibility, streaming chat and richer dashboards.
- Add integration tests using real PostgreSQL, CI, monitoring, rate limits, backups and deployment hardening.
