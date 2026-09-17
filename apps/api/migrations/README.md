# Database migrations

Phase 0 intentionally contains no domain or user tables. The initial revision only establishes
the Alembic history so future phases can add reviewed schema changes incrementally.

The database URL is read from `DATABASE_URL`; it is never stored in `alembic.ini`.
