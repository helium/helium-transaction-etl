.PHONY: help docker-stop

help: #: Show this help message
  @awk '/^[A-Za-z_ -]*:.*#:/ {printf("%c[1;33m%-15s%c[0m", 27, $$1, 27); for(i=3; i<=NF; i++) { printf("%s ", $$i); } printf("\n"); }' Makefile*

default: help

docker-build: #: Build docker image
	docker build \
		-t helium-transaction-etl .

docker-start: #: Start new container
	docker run -d --init \
		--network="host" \
		--name= transaction-etl \
		--restart unless-stopped \
		--cpus 2 \
		--memory 5g \
		--memory-reservation 4g \
		--memory-swap 5g \
		helium-transaction-etl

docker-stop: #: Stop the container
	docker stop transaction-etl

docker-clean: #: Stop container and remove image
	docker stop transaction-etl
	docker rm transaction-etl
