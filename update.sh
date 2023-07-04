#!/bin/bash
# Run script from the root directory
cd $(dirname $0)

git remote update >/dev/null 2>&1
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse @{u})

if [[ "$LOCAL" == "$REMOTE" ]]; then
  echo "No updates available."
  exit 0
fi

# Fetch the updates and reset to the latest commit
git pull origin main

# Execute the deployment command
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d