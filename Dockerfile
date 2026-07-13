# Self-contained image for the Drosophila Activity Analysis GUI.
# Build:  docker build -t dam-gui .
# Run:    docker run -p 8501:8501 dam-gui
# Then open http://localhost:8501
FROM python:3.11-slim

# matplotlib/pandas/numpy ship manylinux wheels, so no compiler is needed.
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dam/ ./dam/
COPY app.py make_sample_data.py ./

EXPOSE 8501
# Bind to all interfaces so the port is reachable from the host / a cloud LB.
ENTRYPOINT ["streamlit", "run", "app.py", \
            "--server.port=8501", "--server.address=0.0.0.0", \
            "--browser.gatherUsageStats=false"]
