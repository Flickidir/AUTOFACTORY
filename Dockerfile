FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY app.py /app/app.py
COPY providers/ /app/providers/
ENV PORT=10000
CMD ["python", "-u", "app.py"]
