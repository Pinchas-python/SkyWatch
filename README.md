# SkyWatch

SkyWatch is a simple weather-request pipeline:

- Flask frontend sends city requests to RabbitMQ
- Python worker consumes requests
- Worker calls Open-Meteo API and prints weather result logs

## Quick Start (Docker Compose)

1. Start services:

```bash
docker compose up --build
```

2. Open frontend:

```text
http://localhost:5000
```

3. Submit a city name.

4. Check worker logs:

```bash
docker compose logs -f worker
```

5. RabbitMQ management UI:

```text
http://localhost:15672
```

Default login:

- username: guest
- password: guest

## Project Structure

```text
.
├── app
│   ├── frontend
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── worker
│       ├── worker.py
│       ├── Dockerfile
│       └── requirements.txt
├── docker-compose.yml
└── README.md
```

## Next Steps

- Add result storage (Redis/PostgreSQL)
- Add API endpoint to read request results by request_id
- Add CI workflow and Helm chart deployment
