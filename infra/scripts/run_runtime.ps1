Copy-Item .\.env.full.example .\.env -Force
docker compose -f docker-compose.full.yml --env-file .env up --build
