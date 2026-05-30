FROM python:3.10-slim

WORKDIR /app

# Asılılıqları köçürür və yükləyirik
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bütün layihə fayllarını (main.py, static.html və s.) köçürürük
COPY . .
 
# FastAPI-ni Cloud Run-ın təyin etdiyi PORT üzərindən açırıq
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
