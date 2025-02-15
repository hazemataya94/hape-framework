
clean: ## Clean up build, cache, playground and zip files.
	@echo "$$ rm -rf build dist hape.egg-info playground/* hape.zip"
	@rm -rf build dist hape.egg-info playground/* hape.zip

zip: ## Create a zip archive excluding local files and playground.
	@echo "$$ zip -r hape.zip . -x '.env' '.venv/*' '.git/*' 'playground/*'"
	zip -r hape.zip . -x ".env" ".venv/*" ".git/*" "playground/*"
	open .

.venv: ## Create a virtual environment .venv if not exists.
	@if [ ! -d ".venv" ]; then \
		echo "$$ python -m venv .venv"; \
		python -m venv .venv; \
	fi

init-dev: .venv ## Install development dependencies in .venv, docker-compose up -d, and create .env if not exist.
	@echo "$$ .venv/bin/python -m pip uninstall -y hape"
	@.venv/bin/python -m pip uninstall -y hape
	@echo
	@echo "$$ .venv/bin/python -m pip install -r requirements-dev.txt"
	@.venv/bin/python -m pip install -r requirements-dev.txt
	@echo "Dependencies Installed."
	@echo
	@echo "$$ [ -f .env ] || cp .env.example .env"
	@[ -f .env ] || cp .env.example .env
	@echo ".env file created or already exists"
	@echo
	@echo "Run the following to start docker-compose services"
	@echo "\$$ make docker-up"
	@echo "Run the following to start virtual env"
	@echo "\$$ source .venv/bin/activate"
	@echo

init-cli: ## Install CLI dependencies.
	@echo "pip install -r requirements-cli.txt --break-system-packages"
	@pip install -r requirements-cli.txt --break-system-packages

freeze-dev: ## Freeze dependencies for development.
	@echo "$$ pip freeze > requirements-dev.txt"
	@pip freeze > requirements-dev.txt

freeze-cli: ## Freeze dependencies for CLI.
	@echo "$$ pip freeze > requirements-cli.txt"
	@pip freeze > requirements-cli.txt

install: ## Install the package.
	@echo "$$ pip install --upgrade hape"
	@pip install --upgrade hape

bump-version: ## Bump the patch version in setup.py.
	@echo "🔄 Bumping patch version in setup.py..."
	@sed -i.bak -E 's/(version="([0-9]+)\.([0-9]+)\.([0-9]+)")/\1/' setup.py && \
	version=$$(grep -oE 'version="[0-9]+\.[0-9]+\.[0-9]+"' setup.py | grep -oE '[0-9]+\.[0-9]+\.[0-9]+') && \
	major=$$(echo $$version | cut -d. -f1) && \
	minor=$$(echo $$version | cut -d. -f2) && \
	patch=$$(echo $$version | cut -d. -f3) && \
	new_patch=$$((patch + 1)) && \
	new_version="$$major.$$minor.$$new_patch" && \
	sed -i.bak -E "s/version=\"[0-9]+\.[0-9]+\.[0-9]+\"/version=\"$$new_version\"/" setup.py && \
	rm -f setup.py.bak && \
	echo "Version updated to $$new_version"

build: bump-version ## Build the package in dist. Runs: bump-version.
	@echo "$$ rm -rf dist/*"
	@rm -rf dist/*
	@echo "$$ python -m build"
	@python -m build

publish: build ## Publish package to public PyPI, commit, tag, and push the version. Runs: build.
	@twine upload -u __token__ -p "$$(cat ../pypi.token)" dist/* \
	&& \
	( \
		version=$(shell sed -n 's/version="\(.*\)",/\1/p' setup.py | tr -d " "); \
		echo ""; \
		echo "Pypi package has been successfully published."; \
		echo ""; \
		echo "Committing and tagging version $$version"; \
		git add setup.py; \
		git commit -m "Bump version: $$version"; \
		echo ""; \
		echo "Tagging version $$version"; \
		git tag $$version; \
		echo ""; \
		echo "Pushing commits"; \
		git push; \
		echo ""; \
		echo "Pushing tags"; \
		git push --tags; \
	) || ( \
		echo "Upload failed. Not committing version bump."; \
	)

play: ## Run hape.playground Playground.paly() and print the execution time.
	@echo "$$ time python main.py play"
	@time python main.py play

migration-create: ## Create a new database migration.
	@read -p "Enter migration message: " migration_msg && \
	echo "$$ alembic revision --autogenerate -m \"$$migration_msg\"" && \
	alembic revision --autogenerate -m "$$migration_msg"

migration-run: ## Apply the latest database migrations.
	@echo "$$ ALEMBIC_CONFIG=./alembic.ini alembic upgrade head"
	@ALEMBIC_CONFIG=./alembic.ini alembic upgrade head

docker-restart: ## Restart Docker services.
	@echo "$$ docker-compose -f dockerfiles/docker-compose.yml down"
	@docker-compose -f dockerfiles/docker-compose.yml down
	@echo "$$ docker-compose -f dockerfiles/docker-compose.yml up -d --build"
	@docker-compose -f dockerfiles/docker-compose.yml up -d --build

docker-up: ## Start Docker services.
	@echo "$$ docker-compose -f dockerfiles/docker-compose.yml up -d --build"
	@docker-compose -f dockerfiles/docker-compose.yml up -d --build

docker-down: ## Stop Docker services.
	@echo "$$ docker-compose -f dockerfiles/docker-compose.yml down"
	@docker-compose -f dockerfiles/docker-compose.yml down

docker-ps: ## List running Docker services.
	@echo "$$ docker-compose -f dockerfiles/docker-compose.yml ps"
	@docker-compose -f dockerfiles/docker-compose.yml ps

docker-exec: ## Execute a shell in the HAPE Docker container.
	@echo "$$ docker exec -it hape bash"
	@docker exec -it hape bash

source-env: ## Print export statements for the environment variables from .env file.
	@echo "Run the following command to export environment variables:"
	@grep -v '^#' .env | xargs -I {} echo export {}

list: ## Show available commands.
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | \
	awk -F ':.*?## ' '{printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' | \
	sort
