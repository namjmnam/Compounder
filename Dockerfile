# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install konlpy requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
                g++ \
                openjdk-11-jdk \
                curl \
                sudo \
                git \
        && rm -rf /var/lib/apt/lists/*
RUN curl -s https://raw.githubusercontent.com/konlpy/konlpy/master/scripts/mecab.sh | bash && rm -rf /tmp/*

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "compounder.py"]
