sync-dev:
	uv sync --extra client --extra service --extra dev

streamlit:
	uv run streamlit run test_suite_v2/Home.py

run:
	uv run --active uvicorn main:app --host 0.0.0.0 --port 8001 --reload

cov-report:
	uv run pytest -d --tx 5*popen -vv ./tests \
	--maxfail=5 --durations=10 \
	--cov=app --cov-config=.coveragerc --cov-report=html:calc_cov

	@echo "Starting a simple HTTP server to view the coverage report..."
	@cd calc_cov && python -m http.server 8099

test:
	uv run pytest -vv ./tests --capture=no
pc:
	uv run pre-commit run --all-files

pc-changed:
	uv run pre-commit run --files $$(git ls-files --others --modified --exclude-standard)

local-action-test:
	@which act > /dev/null || (echo "Error: 'act' is not installed. Please install it from https://github.com/nektos/act" && exit 1)
	@echo "Running act for local tests..."
	act -j local-tests-job --secret-file .secrets -P ubuntu-latest=catthehacker/ubuntu:act-latest
	@echo "✅ Done: Local tests complete."

run-test-db:
	@docker ps -a | grep -q test-postgres || \
		docker run --name test-postgres -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=test_db -p 5433:5432 -d postgres:16
	@sh -c 'until docker exec test-postgres pg_isready -U user -d test_db; do sleep 1; done'
	@echo "Test database is running on port 5433"
	@uv run python cli.py init-test-db

stop-test-db:
	@docker ps -a | grep -q test-postgres && docker stop test-postgres || true
	@docker ps -a | grep -q test-postgres && docker rm -v test-postgres || true
	@echo "🧹 Test database container stopped and removed"
