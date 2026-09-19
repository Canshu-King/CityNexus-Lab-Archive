# ADR-002 - SQLite first, PostgreSQL portable

Decision: SQLite is the default coursework database. SQLAlchemy is used so production-oriented migration to PostgreSQL remains possible.

Rules: integer minor-unit money; UTC timestamps; UUID text identifiers; avoid SQLite-only business logic in SQL triggers.
