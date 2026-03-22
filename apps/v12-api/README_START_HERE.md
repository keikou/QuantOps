# PhaseH Sprint4 Source Code

## Run

```powershell
python -m pytest -q
powershell -ExecutionPolicy Bypass -File .\scripts\check_phaseh_sprint4.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\check_phaseh_sprint4.ps1 -StartLocalApi
```

## Docker

```powershell
docker compose down -v
docker compose up --build
```

## Key endpoints

- `GET /alpha/overview`
- `GET /alpha/registry`
- `POST /alpha/generate`
- `POST /alpha/test`
- `POST /alpha/evaluate`
- `GET /alpha/ranking`
- `GET /alpha/library`
- `GET /dashboard/alpha-factory`
- `GET /dashboard/global`
