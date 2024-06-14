FROM python:3.11-alpine3.20
RUN apk update && apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    bzip2-dev \
    readline-dev \
    sqlite-dev \
    zlib-dev \
    pango-dev \
    cairo-dev \
    gdk-pixbuf \
    libxml2-dev \
    libxslt-dev \
    && apk add --no-cache \
    gobject-introspection \
    pango \
    cairo \
    gdk-pixbuf \
    && rm -rf /var/cache/apk/*
RUN addgroup -S botgroup && adduser -S botuser -G botgroup
WORKDIR /app/
COPY . /app/
RUN chown -R botuser:botgroup /app
USER botuser
RUN pip install --no-cache -r requirements.txt
CMD [ "python", "main.py" ]