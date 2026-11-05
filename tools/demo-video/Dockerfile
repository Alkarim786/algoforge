# Headless Chromium (Playwright) for recording the app, plus ffmpeg for editing the clips into one video.
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir playwright==1.49.0
WORKDIR /work
RUN pip install --no-cache-dir numpy==1.26.4
