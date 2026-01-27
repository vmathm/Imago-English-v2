DC = docker compose -f docker-compose.prod.yml

up:
	$(DC) up -d

down:
	$(DC) down

logs:
	$(DC) logs -f

migrate:
	$(DC) run --rm web alembic upgrade head

build:
	$(DC) build --no-cache web

shell:
	$(DC) exec web bash
