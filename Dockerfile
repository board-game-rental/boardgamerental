# Użyj oficjalnego obrazu Pythona jako obrazu bazowego
FROM python:3.10

# Ustaw zmienne środowiskowe
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.5.0

# Zainstaluj Poetry
RUN pip install --upgrade pip
RUN pip install "poetry==$POETRY_VERSION"

# Ustaw katalog roboczy
WORKDIR /code

# Skopiuj tylko pliki wymagań, aby je zbuforować w warstwie dockera
COPY pyproject.toml poetry.lock /code/

# Inicjalizacja projektu:
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Skopiuj zawartość bieżącego katalogu do kontenera w /code
COPY . /code/

# Określ komendę, która ma zostać uruchomiona przy starcie kontenera
CMD bash -c "python manage.py migrate && gunicorn boardgamerental.wsgi --bind 0.0.0.0:8000"
