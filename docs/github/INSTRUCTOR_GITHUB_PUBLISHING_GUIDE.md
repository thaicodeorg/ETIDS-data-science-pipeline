# Instructor Guide: Publish the ETIDS Docker Project to GitHub

This guide prepares the project so students can clone, install, and run the labs easily.

## 1. Recommended repository name

```text
etids-manufacturing-data-science-pipeline
```

## 2. Create a GitHub repository

On GitHub:

1. Click **New repository**.
2. Set repository name to `etids-manufacturing-data-science-pipeline`.
3. Choose **Public** if students should clone without authentication.
4. Do not initialize with README if this project already has one.

## 3. Initialize local Git repository

From the project root:

```bash
git init
git branch -M main
git add .
git commit -m "Initial ETIDS Docker data science pipeline"
```

## 4. Add GitHub remote

Replace `<OWNER>` with your GitHub username or organization.

```bash
git remote add origin https://github.com/<OWNER>/etids-manufacturing-data-science-pipeline.git
git push -u origin main
```

## 5. Student clone command

Give students this command:

```bash
git clone https://github.com/<OWNER>/etids-manufacturing-data-science-pipeline.git
cd etids-manufacturing-data-science-pipeline
cp .env.example .env
docker compose up -d --build
```

For Windows PowerShell:

```powershell
git clone https://github.com/<OWNER>/etids-manufacturing-data-science-pipeline.git
cd etids-manufacturing-data-science-pipeline
Copy-Item .env.example .env
docker compose up -d --build
```

## 6. Recommended GitHub settings

| Setting | Recommendation |
|---|---|
| Visibility | Public for class use; private only if students have access |
| Default branch | `main` |
| Issues | Enable, for lab problems |
| Discussions | Optional, for Q&A |
| Wiki | Optional |
| Releases | Use for tagged stable lab versions |

## 7. Suggested release tags

```bash
git tag -a v1.0.0 -m "ETIDS Lecture 3-4 Docker lab release"
git push origin v1.0.0
```

Create a GitHub release named:

```text
v1.0.0 - ETIDS Lecture 3-4 Docker Lab
```

## 8. Repository hygiene

Do not commit:

- `.env`
- local database volumes
- Airflow logs
- Superset local state
- `node_modules`
- Python cache folders

These are already covered in `.gitignore`.

## 9. Large file note

The included synthetic dataset ZIP is about 14 MB, so it is acceptable for GitHub. If future datasets exceed 100 MB, move them to GitHub Releases, Google Drive, or Git LFS.
