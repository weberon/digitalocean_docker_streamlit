FROM python:3.12-slim
	
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR app/
COPY ./app .

RUN pip3 install -r requirements.txt

EXPOSE 8501

#HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

CMD ["streamlit", "run", "app.py"]