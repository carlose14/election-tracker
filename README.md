# Election Results Tracker 🗳️

Automated tracker for Peru's second-round election results (ONPE). A GitHub Actions workflow runs every 30 minutes, fetches the latest vote counts from the public ONPE API, and appends a new row to `results.csv`.

## How it works

1. **GitHub Actions cron** triggers every 30 minutes (and on manual dispatch).
2. **`fetch_results.py`** sends a GET request to the ONPE results API.
3. The script validates the response, extracts vote data for both candidates, and appends a timestamped row to `results.csv`.
4. The workflow commits and pushes the updated CSV back to the repository.

## CSV format

| Column | Description |
|---|---|
| `Date` | Timestamp in UTC-5 (Peru time) |
| `nombreAgrupacionPolitica1` | Name of the first political party |
| `totalVotosValidos1` | Total valid votes for party 1 |
| `porcentajeVotosValidos1` | Percentage of valid votes for party 1 |
| `porcentajeVotosEmitidos1` | Percentage of emitted votes for party 1 |
| `nombreAgrupacionPolitica2` | Name of the second political party |
| `totalVotosValidos2` | Total valid votes for party 2 |
| `porcentajeVotosValidos2` | Percentage of valid votes for party 2 |
| `porcentajeVotosEmitidos2` | Percentage of emitted votes for party 2 |

## Running locally

```bash
pip install -r requirements.txt
python fetch_results.py
```

## Setup on GitHub

1. Create a new GitHub repository.
2. Push this project to the repository:
   ```bash
   cd election-tracker
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<your-user>/<your-repo>.git
   git push -u origin main
   ```
3. The workflow will start running automatically on the cron schedule.
4. You can also trigger it manually from the **Actions** tab → **Fetch Election Results** → **Run workflow**.

## Assumptions

- The API always returns exactly **two** participants in a consistent order.
- The default `GITHUB_TOKEN` has write permissions to repository contents (this is the default for most repos).
- Timestamps use **UTC-5** (Peru time / PET).

## API source

```
GET https://resultadosegundavuelta.onpe.gob.pe/presentacion-backend/resumen-general/participantes?idEleccion=10&tipoFiltro=eleccion
```
