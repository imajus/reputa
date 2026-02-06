#!/bin/sh
docker build -t evm-score-oracle:dev .
docker tag evm-score-oracle:dev majus/evm-score-oracle:node-reproducible-amd64
DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' majus/evm-score-oracle:node-reproducible-amd64)
sed -i "s|^[[:space:]]*image:.*|    image: $DIGEST|" app/docker-compose.yml
oyster-cvm simulate --docker-compose docker-compose.yml -p 3000