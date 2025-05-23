DEFAULT_GOAL := help

# Any command that has the same name as a file or folder needs to be marked as phony
.PHONY: deploy

# Everything at the top level runs every time you do anything.
# So only put fast commands up here.

dns-name ?= $(shell cat config.yml | yq e '.dns-name')
email ?= $(shell cat config.yml | yq e '.email')
name ?= $(shell cat config.yml | yq e '.name')
name-dashed ?= $(subst /,-,$(name))
name-short ?= $(shell echo $(name) | cut -d/ -f2)
git-hash ?= $(shell git rev-parse HEAD)
image-url ?= ghcr.io/$(name):$(git-hash)

help:
	@awk '/^## / \
		{ if (c) {print c}; c=substr($$0, 4); next } \
			c && /(^[[:alpha:]][[:alnum:]_-]+:)/ \
		{printf "%-30s %s\n", $$1, c; c=0} \
			END { print c }' $(MAKEFILE_LIST)

## build the project inside of a virtual environment, this is for local development
build-venv:
	poetry config virtualenvs.in-project true
	poetry lock
	poetry self add poetry-plugin-export
	poetry export -f requirements.txt --output requirements.txt --without-hashes --with dev
	pip install -r requirements.txt

## build project inside of a docker container
build:
	docker build \
		--progress plain \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--cache-from $(name):latest \
		-t $(name):$(git-hash) \
		-t $(name):latest \
		.

## publish the application docker image to the registry
publish:
	docker tag $(name):$(git-hash) $(image-url)
	docker push $(image-url)

## deploy the secrets utilized by the application
deploy-secrets:
	-@kubectl create namespace $(name-dashed)
	$(eval github-token := $(shell aws ssm get-parameter --name "/github/pat" --with-decryption --query "Parameter.Value" --output text))
	# create the secret
	kubectl create secret docker-registry docker-registry \
		--namespace="$(name-dashed)" \
		--docker-server=ghcr.io/$(name) \
		--docker-username=$(name) \
		--docker-password=$(github-token) \
		--dry-run=client -o yaml | kubectl apply -f -
	kubectl get secret aws-credentials -n external-secrets -o yaml | \
		sed "s/namespace: external-secrets/namespace: $(name-dashed)/" | \
		kubectl apply -f -

deploy:
	-@kubectl create namespace $(name-dashed)
	env \
		NAME=$(name-dashed) \
		DNS_NAME=$(dns-name) \
		IMAGE=$(image-url) \
		envsubst < deploy/main.yml | kubectl apply -f -

## run project on your plain old machine. see also: run-docker
run-native:
	poetry run uvicorn src.main:app --reload --port 4000 --host 0.0.0.0

## run project inside of a docker container. see also: run-native
run-docker:
	docker run --expose 4000 -it --rm $(name):latest
