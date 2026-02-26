.PHONY: dev stop logs migrate seed test test-cov lint gen-keys shell build

# ── Docker ───────────────────────────────────────────────────────────────────

dev:
	docker compose up --build -d
	@echo "✅ BharatAI running at http://localhost:3000 (frontend) | http://localhost:8000 (API)"

stop:
	docker compose down

stop-v:
	docker compose down -v

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-worker:
	docker compose logs -f worker

build:
	docker compose build

restart:
	docker compose restart

# ── Database ─────────────────────────────────────────────────────────────────

migrate:
	docker compose exec backend alembic upgrade head
	@echo "✅ Migrations applied"

migrate-down:
	docker compose exec backend alembic downgrade -1

migrate-gen:
	@read -p "Migration message: " msg; \
	docker compose exec backend alembic revision --autogenerate -m "$$msg"

seed:
	docker compose exec backend python scripts/seed.py
	@echo "✅ Database seeded"

# ── Testing ───────────────────────────────────────────────────────────────────

test:
	docker compose exec backend python -m pytest tests/ -v --tb=short

test-cov:
	docker compose exec backend python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing --cov-report=html

test-unit:
	docker compose exec backend python -m pytest tests/unit/ -v --tb=short

test-integration:
	docker compose exec backend python -m pytest tests/integration/ -v --tb=short

test-watch:
	docker compose exec backend python -m pytest tests/ -v --tb=short -f

# ── Linting ───────────────────────────────────────────────────────────────────

lint:
	docker compose exec backend black app/ tests/ scripts/
	docker compose exec backend isort app/ tests/ scripts/
	docker compose exec backend ruff check app/ tests/ --fix
	@echo "✅ Lint complete"

lint-check:
	docker compose exec backend black --check app/ tests/
	docker compose exec backend isort --check app/ tests/
	docker compose exec backend ruff check app/ tests/

# ── Keys ─────────────────────────────────────────────────────────────────────

gen-keys:
	@echo "Generating RSA key pair for JWT..."
	openssl genrsa -out backend/jwt_private.pem 2048
	openssl rsa -in backend/jwt_private.pem -pubout -out backend/jwt_public.pem
	@echo "✅ Keys generated at backend/jwt_private.pem + backend/jwt_public.pem"

# ── Shell ────────────────────────────────────────────────────────────────────

shell:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U bharatai -d bharatai_db

shell-redis:
	docker compose exec redis redis-cli

# ── Scraping ─────────────────────────────────────────────────────────────────

scrape:
	docker compose exec backend python -m app.workers.scrape_tasks scrape_all

# ── Load Testing ─────────────────────────────────────────────────────────────

load-test:
	docker compose exec backend locust -f tests/load/locustfile.py --host=http://localhost:8000

# ── Backup ───────────────────────────────────────────────────────────────────

backup:
	docker compose exec postgres pg_dump -U bharatai bharatai_db | gzip > backups/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "✅ Backup created"

# ── Setup ────────────────────────────────────────────────────────────────────

setup:
	cp .env.example .env
	$(MAKE) gen-keys
	$(MAKE) dev
	sleep 10
	$(MAKE) migrate
	$(MAKE) seed
	@echo ""
	@echo "🎉 BharatAI is ready!"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   API Docs:  http://localhost:8000/docs"
	@echo "   Grafana:   http://localhost:3001 (admin/admin)"
