FROM python:3.13-alpine
WORKDIR /app
COPY server.py renderers teletext server.py /app
EXPOSE 8080
CMD ["python", "server.py", "8080"]
