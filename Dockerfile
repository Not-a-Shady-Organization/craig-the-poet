# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.7-slim

# Get source files & API key
COPY app.py \
     craig_the_poet.py \
     upload_video.py \
     requirements.txt \
     auth-key-file.json \
     client_secrets.json \
     youtube-oauth2.json.example \
     ./

# Copy in utils and note where to find them when imported
COPY not-shady-utils /usr/local/not-shady-utils
ENV PYTHONPATH=$PYTHONPATH:usr/local/not-shady-utils

# Note credential location for use of Google APIs
ENV GOOGLE_APPLICATION_CREDENTIALS=./auth-key-file.json

# Note the endpoints we need
ENV CRAIGSLIST_SCRAPER_ENDPOINT=https://craigslist-scraper-ekdapyzpva-uc.a.run.app
ENV POEM_MAKER_ENDPOINT=https://poem-maker-ekdapyzpva-uc.a.run.app

# Set amount of scrapers & video requests allowed to live at once
ENV MAX_REQUESTS_LIVE=50

# Set time allowed for scraping & video generating jobs
ENV WORKER_TIMEOUT=600

# Install Python dependencies
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn

# Install other dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Define the entrypoint (we only want this container for this program anyways)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
