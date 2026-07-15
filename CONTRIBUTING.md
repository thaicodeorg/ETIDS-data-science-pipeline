# Contributing

This repository is designed for classroom use. Suggested contributions include:

- fixing lab instructions,
- improving dashboard examples,
- adding SQL exercises,
- extending data-quality rules,
- adding new Superset chart recipes,
- improving Docker startup reliability.

Before submitting changes:

```bash
docker compose config
docker compose build backend frontend superset
```

Do not commit `.env`, runtime logs, database volumes, or local cache files.
