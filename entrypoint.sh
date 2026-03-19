#!/bin/sh

echo "Warte auf MariaDB..."
until flask seed 2>/dev/null; do
  echo "Datenbank noch nicht bereit – warte 3 Sekunden..."
  sleep 3
done

exec gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
