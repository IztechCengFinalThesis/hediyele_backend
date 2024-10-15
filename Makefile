C_NAME ?= app_api
M_NAME ?= migration

up:
	docker compose down && docker compose up --build --remove-orphans -d

down:
	docker compose down

logs:
	docker logs -f --tail 100 $(C_NAME)

bash:
	docker exec -it $(C_NAME) bash

tests:
	docker exec $(C_NAME) pytest . -n auto # -rP
