FROM python:3.12-slim
WORKDIR /app
COPY *.py run.sh ./
ENTRYPOINT ["bash", "run.sh"]
