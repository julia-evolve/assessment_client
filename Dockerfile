FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

ARG PIP_TIMEOUT=120
ENV PIP_DEFAULT_TIMEOUT=${PIP_TIMEOUT} PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --timeout ${PIP_TIMEOUT} -r requirements.txt

COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app/src

EXPOSE 8501

CMD ["streamlit", "run", "src/assessment_client/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
