FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
# Note: If you encounter SSL certificate issues during build, you may need to use
# pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
ARG PIP_TIMEOUT=120
ENV PIP_DEFAULT_TIMEOUT=${PIP_TIMEOUT} PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --timeout ${PIP_TIMEOUT} -r requirements.txt

# Copy application code
COPY examples/ ./examples/
COPY modules/ ./modules/
COPY app.py .

# Expose Streamlit default port
EXPOSE 8501

# Health check (optional, requires curl to be installed)
# HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
