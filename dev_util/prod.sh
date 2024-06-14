#!/bin/bash

declare -a images=("ring-worker" "ring-api" "ring-frontend" "ring-beat")

for i in "${images[@]}"
do
    docker pull public.ecr.aws/z2k1e8p1/"$i":latest
    docker tag public.ecr.aws/z2k1e8p1/"$i":latest "prod-$i":latest
    docker rmi public.ecr.aws/z2k1e8p1/"$i":latest
done