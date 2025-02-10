clean:
	rm -rf build dist hape.egg-info playground/* hape.zip

zip:
	zip -r hape.zip . -x ".env" ".venv/*" ".git/*" "playground/*"
	open .

.venv:
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment"; \
		python -m venv .venv; \
	fi

init-dev: .venv
	@echo "Installing venv dependencies"
	@source .venv/bin/activate && pip install -r requirements-dev.txt
	@echo "Dependencies Installed."
	@echo
	@echo "Starting docker-compose services"
	@docker-compose -f dockerfiles/docker-compose-dev.yml up -d
	@echo
	@echo "Creating .env file"
	@[ -f .env ] || cp .env.example .env
	@echo
	@echo "Now run the following to start your virtual env"
	@echo "\$$ source .venv/bin/activate"
	@echo

init-cli:
	@echo "Installing `hape` CLI"
	@pip install -r requirements-cli.txt --break-system-packages

freeze-dev:
	@pip freeze > requirements-dev.txt

freeze-cli:
	@pip freeze > requirements-cli.txt

install: init-cli
	pip install --upgrade --index-url https://pypi_link hape

bump-version:
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

publish-aws: bump-version
	@rm -rf dist/*
	@python setup.py sdist
	@python setup.py bdist_wheel --plat-name manylinux2014_x86_64
	@python setup.py bdist_wheel --plat-name manylinux2014_aarch64
	@export TWINE_USERNAME=aws && \
	export TWINE_PASSWORD=$$(aws codeartifact get-authorization-token --domain pypi --domain-owner 910325995766 --query authorizationToken --output text) && \
	twine upload --repository-url https://pypi-910325995766.d.codeartifact.eu-central-1.amazonaws.com/pypi/devops/ dist/* && \
	( \
		echo "Upload successful. Committing version bump..."; \
		git add setup.py; \
		git commit -m "Bump version"; \
		git push; \
	) || ( \
		echo "Upload failed. Not committing version bump."; \
	)

build: bump-version
	@rm -rf dist/*
	@python -m build

publish: build
	@twine upload -u __token__ -p "$$(cat ../pypi.token)" dist/* \
	&& \
	( \
		version=$(shell sed -n 's/version="\(.*\)",/\1/p' setup.py | tr -d " "); \
		echo "Pypi package has been successfully published." \
		echo; echo "Committing and tagging version $$version" \
		git add setup.py; \
	) || ( \
		echo "Upload failed. Not committing version bump."; \
	)

play:
	time python main.py play

migration-init:
	@cd hape && alembic init migrations

migration-create:
	@read -p "Enter migration message: " migration_msg && \
	 alembic revision --autogenerate -m "$$migration_msg"

migration-run:
	@ALEMBIC_CONFIG=./alembic.ini alembic upgrade head

docker-restart:
	@docker-compose -f dockerfiles/docker-compose-dev.yml down
	@docker-compose -f dockerfiles/docker-compose-dev.yml up -d --build

docker-up:
	@docker-compose -f dockerfiles/docker-compose-dev.yml up -d --build

docker-down:
	@docker-compose -f dockerfiles/docker-compose-dev.yml down

docker-ps:
	@docker-compose -f dockerfiles/docker-compose-dev.yml ps

docker-exec:
	@docker exec -it hape bash

source-env:
	@echo "Run the following command to export environment variables:"
	@grep -v '^#' .env | xargs -I {} echo export {}