PYTHON ?= python
VERSION_FILE ?= VERSION
INSTALL_PREFIX ?=
PYPI_TOKEN_FILE ?= ../pypi.token
KIND_CLUSTER_NAME ?= hape
KIND_CONFIG_PATH ?= infrastructure/kubernetes/kind/cluster-config.yaml
DOCKER_IMAGE ?= hazemataya/hape
DOCKERFILE_PATH ?= docker/Dockerfile
KUSTOMIZE_TARGET_PATH := $(word 2,$(MAKECMDGOALS))

.PHONY: help clean bump-version build install kind-up helmfile-sync kind-down kustomize-apply kustomize-delete publish-docker

ifneq ($(filter kustomize-apply kustomize-delete,$(firstword $(MAKECMDGOALS))),)
  ifneq ($(KUSTOMIZE_TARGET_PATH),)
$(eval $(KUSTOMIZE_TARGET_PATH):;@:)
  endif
endif

help: ## Show available commands.
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | \
	awk -F ':.*?## ' '{printf "%-20s %s\n", $$1, $$2}' | \
	sort

clean: ## Remove build artifacts.
	@echo "$$ rm -rf build dist *.egg-info"
	@rm -rf build dist *.egg-info

bump-version: ## Bump the patch version in VERSION.
	@version=$$(cat $(VERSION_FILE)); \
	major=$$(echo $$version | cut -d. -f1); \
	minor=$$(echo $$version | cut -d. -f2); \
	patch=$$(echo $$version | cut -d. -f3); \
	new_patch=$$((patch + 1)); \
	new_version="$$major.$$minor.$$new_patch"; \
	echo $$new_version > $(VERSION_FILE); \
	echo "Version updated to $$new_version"

build: bump-version ## Build sdist and wheel into dist/.
	@echo "$$ rm -rf dist"
	@rm -rf dist
	@echo "$$ $(PYTHON) -m build"
	@$(PYTHON) -m build

install: ## Install to $(INSTALL_PREFIX)/bin via pip.
	@wheel=$$(ls -t dist/*.whl 2>/dev/null | head -n 1); \
	if [ -z "$$wheel" ]; then \
		echo "No wheels found in dist/"; \
		exit 1; \
	fi; \
	if [ -n "$(INSTALL_PREFIX)" ]; then \
		echo "$$ $(PYTHON) -m pip install --upgrade --force-reinstall --prefix $(INSTALL_PREFIX) $$wheel"; \
		$(PYTHON) -m pip install --upgrade --force-reinstall --prefix $(INSTALL_PREFIX) $$wheel; \
	else \
		echo "$$ $(PYTHON) -m pip install --upgrade --force-reinstall $$wheel"; \
		$(PYTHON) -m pip install --upgrade --force-reinstall $$wheel; \
	fi

kind-up: ## Create local kind cluster named $(KIND_CLUSTER_NAME).
	@if kind get clusters | grep -xq "$(KIND_CLUSTER_NAME)"; then \
		echo "kind cluster $(KIND_CLUSTER_NAME) is already running"; \
	else \
		kind create cluster --name $(KIND_CLUSTER_NAME) --config $(KIND_CONFIG_PATH); \
	fi

helmfile-sync: ## Sync Helmfile releases for local cluster tooling.
	helmfile -f infrastructure/kubernetes/helmfile.yaml sync

kind-down: ## Delete local kind cluster named $(KIND_CLUSTER_NAME).
	@if kind get clusters | grep -xq "$(KIND_CLUSTER_NAME)"; then \
		kind delete cluster --name $(KIND_CLUSTER_NAME); \
	else \
		echo "kind cluster $(KIND_CLUSTER_NAME) is not running"; \
	fi

kustomize-apply: ## Apply kustomization path passed as second make argument.
	@if [ -z "$(KUSTOMIZE_TARGET_PATH)" ]; then \
		echo "Usage: make kustomize-apply <kustomization-path>"; \
		exit 1; \
	fi
	@if [ ! -d "$(KUSTOMIZE_TARGET_PATH)" ]; then \
		echo "Error: directory not found: $(KUSTOMIZE_TARGET_PATH)"; \
		exit 1; \
	fi
	@if [ ! -f "$(KUSTOMIZE_TARGET_PATH)/kustomization.yaml" ]; then \
		echo "Error: kustomization.yaml not found in: $(KUSTOMIZE_TARGET_PATH)"; \
		exit 1; \
	fi
	kubectl kustomize --load-restrictor=LoadRestrictionsNone "$(KUSTOMIZE_TARGET_PATH)" | kubectl apply -f -

kustomize-delete: ## Delete kustomization path passed as second make argument.
	@if [ -z "$(KUSTOMIZE_TARGET_PATH)" ]; then \
		echo "Usage: make kustomize-delete <kustomization-path>"; \
		exit 1; \
	fi
	@if [ ! -d "$(KUSTOMIZE_TARGET_PATH)" ]; then \
		echo "Error: directory not found: $(KUSTOMIZE_TARGET_PATH)"; \
		exit 1; \
	fi
	@if [ ! -f "$(KUSTOMIZE_TARGET_PATH)/kustomization.yaml" ]; then \
		echo "Error: kustomization.yaml not found in: $(KUSTOMIZE_TARGET_PATH)"; \
		exit 1; \
	fi
	kubectl kustomize --load-restrictor=LoadRestrictionsNone "$(KUSTOMIZE_TARGET_PATH)" | kubectl delete -f -

publish: ## Publish package to public PyPI. Commit, tag, and push the version.
	@if [ ! -f "$(PYPI_TOKEN_FILE)" ]; then \
		echo "Error: PyPI token file not found at $(PYPI_TOKEN_FILE). Set PYPI_TOKEN_FILE to a valid token file path."; \
		exit 1; \
	fi
	@if [ ! -s "$(PYPI_TOKEN_FILE)" ]; then \
		echo "Error: PyPI token file is empty at $(PYPI_TOKEN_FILE)."; \
		exit 1; \
	fi
	@TWINE_USERNAME=__token__ TWINE_PASSWORD="$$(cat "$(PYPI_TOKEN_FILE)")" twine upload dist/* \
	&& \
	( \
		version=$$(cat $(VERSION_FILE)); \
		echo ""; \
		echo "Pypi package has been successfully published."; \
		echo ""; \
		echo "Committing and tagging version $$version"; \
		git add VERSION setup.py; \
		git commit -m "Bump version: $$version"; \
		echo ""; \
		echo "Tagging version $$version"; \
		git tag $$version; \
		echo ""; \
		echo "Pushing commits"; \
		git push origin main; \
		echo ""; \
		echo "Pushing tags"; \
		git push origin --tags; \
		echo ""; \
		echo "Publishing Docker image"; \
		sleep 2; \
		$(MAKE) publish-docker; \
	) || ( \
		echo "Upload failed. Not committing version bump."; \
	)

publish-docker: ## Build and publish Docker image with latest and VERSION tags.
	@set -eu; \
	version=$$(cat $(VERSION_FILE)); \
	echo "$$ docker build --no-cache -f $(DOCKERFILE_PATH) -t $(DOCKER_IMAGE):latest ."; \
	docker build --no-cache -f $(DOCKERFILE_PATH) -t $(DOCKER_IMAGE):latest .; \
	echo "$$ docker tag $(DOCKER_IMAGE):latest $(DOCKER_IMAGE):$$version"; \
	docker tag $(DOCKER_IMAGE):latest $(DOCKER_IMAGE):$$version; \
	echo "$$ docker push $(DOCKER_IMAGE):latest"; \
	docker push $(DOCKER_IMAGE):latest; \
	echo "$$ docker push $(DOCKER_IMAGE):$$version"; \
	docker push $(DOCKER_IMAGE):$$version
