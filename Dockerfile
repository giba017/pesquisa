FROM python:3.12-slim
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /pesquisa
COPY . .

# Instale o tzdata para configurar o fuso horário
RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

# Defina a variável de ambiente TZ para o fuso horário correto
ENV TZ="America/Sao_Paulo"

COPY entrypoint.sh /pesquisa/entrypoint.sh
RUN chmod +x /pesquisa/entrypoint.sh && pip install poetry \
&& poetry config installer.max-workers 10 \
&& poetry install --no-interaction --no-ansi

EXPOSE 8001

# Comando para iniciar o servidor UVicorn
CMD ["poetry", "run", "uvicorn", "--host", "0.0.0.0", "--port", "8002", "app.app:app"]