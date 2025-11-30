FROM postgres:16

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-partman postgresql-16-cron \
    && rm -rf /var/lib/apt/lists/*

ENV POSTGRES_DB=superscooters
ENV POSTGRES_USER=superscooters
ENV POSTGRES_PASSWORD=superscooters
