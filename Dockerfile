FROM python:3.10-slim

WORKDIR /app

# Faylın yeri .adk/requirements.txt olduğu üçün belə köçürürük:
COPY .adk/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Digər bütün faylları köçürürük
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
