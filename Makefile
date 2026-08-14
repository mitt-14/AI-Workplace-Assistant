.PHONY: build up down restart logs ps health clean

build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d --build

logs:
	docker compose logs -f

ps:
	docker compose ps

health:
	@echo "Frontend:"
	@curl -fsS http://localhost:$${FRONTEND_PORT:-8080}/healthz && echo
	@echo "Backend:"
	@curl -fsS http://localhost:$${BACKEND_PORT:-8000}/health && echo

clean:
	docker compose down --remove-orphans
