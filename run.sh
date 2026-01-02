#!/usr/bin/env bash
set -e

IMAGE_NAME="playlist-downloader"

# Build image (cached if unchanged)
docker build -t "$IMAGE_NAME" .

# Ensure downloads folder exists
mkdir -p downloads

# Use links.example.txt by default, or first arg if provided
INPUT_FILE="${1:-links.example.txt}"

docker run --rm \
  -v "$(pwd)/$INPUT_FILE:/input/links.txt:ro" \
  -v "$(pwd)/downloads:/music" \
  "$IMAGE_NAME" \
  /input/links.txt \
  /music
