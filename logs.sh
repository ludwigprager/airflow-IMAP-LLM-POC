#!/bin/bash
set -eu
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

source .env
docker compose logs -f &
#docker exec -ti postfix tail -f /var/log/mail.log
