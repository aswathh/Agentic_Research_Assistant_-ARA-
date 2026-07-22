# FastAPI — Complete Guide for ML and AI Deployment

A structured reference for building and deploying machine learning APIs using FastAPI. This guide covers everything from basic routing to production deployment, written for developers who already understand Python and want to serve ML models as REST APIs.

---

## Table of Contents

- [What is FastAPI](#what-is-fastapi)
- [Installation](#installation)
- [Your First App](#your-first-app)
- [Routes and Endpoints](#routes-and-endpoints)
- [Pydantic Models](#pydantic-models)
- [Serving an ML Model](#serving-an-ml-model)
- [Lifespan Events](#lifespan-events)
- [File Uploads](#file-uploads)
- [CORS and Middleware](#cors-and-middleware)
- [Response Models and Status Codes](#response-models-and-status-codes)
- [API Key Authentication](#api-key-authentication)
- [Auto-Generated Docs](#auto-generated-docs)
- [Project Structure](#project-structure)
- [Deployment](#deployment)

---

## What is FastAPI

FastAPI is a modern Python web framework for building APIs. It is designed to be fast, easy to use, and production-ready out of the box.

**Why it fits ML/AI workflows:**

- Async support means it handles many concurrent prediction requests efficiently
- Pydantic handles input validation automatically, so you do not need to write custom checks
- Interactive Swagger docs are generated for free with zero configuration
- Lightweight enough to run inside Docker containers and deploy on any cloud

**How it works conceptually:**

A client (browser, another service, or a frontend app) sends an HTTP request to a URL. FastAPI receives the request, runs the corresponding Python function, and returns the result as JSON. The ML model lives inside that Python function.

---

## Installation

```bash
pip install fastapi uvicorn
```

- `fastapi` is the web framework
- `uvicorn` is the ASGI server that actually runs the app

For production, also install:

```bash
pip install gunicorn
```

---

## Your First App

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "API is running"}
```

Run the server:

```bash
uvicorn main:app --reload
```

- `main` refers to the filename `main.py`
- `app` refers to the FastAPI instance
- `--reload` restarts the server automatically on file save (use only in development)

Visit `http://127.0.0.1:8000` in your browser and you will see the JSON response.

---

## Routes and Endpoints

An endpoint is a URL path mapped to a Python function. FastAPI supports the standard HTTP methods.

```python
@app.get("/items")          # Fetch data
@app.post("/predict")       # Send data and get a result
@app.put("/items/{id}")     # Update an existing resource
@app.delete("/items/{id}")  # Delete a resource
```

### Path Parameters

Values embedded directly in the URL.

```python
@app.get("/user/{name}")
def greet(name: str):
    return {"message": f"Hello {name}"}
```

Calling `/user/Aswath` returns `{"message": "Hello Aswath"}`.

### Query Parameters

Values passed after the `?` symbol in the URL.

```python
@app.get("/items")
def get_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

Calling `/items?skip=5&limit=20` returns `{"skip": 5, "limit": 20}`.

FastAPI infers path parameters from the URL pattern and everything else becomes a query parameter automatically.

---

## Pydantic Models

Pydantic is used to define the shape of data coming into your API. FastAPI validates the incoming request body against the model before your function even runs.

```python
from pydantic import BaseModel

class PredictRequest(BaseModel):
    feature1: float
    feature2: float
    label: str = "unknown"   # Optional field with a default value

@app.post("/predict")
def predict(request: PredictRequest):
    return {"received": request.model_dump()}
```

If the client sends `feature1: "abc"`, FastAPI rejects the request with a clear error message. You do not need to write any validation logic yourself.

**Nested models** work the same way:

```python
class Metadata(BaseModel):
    source: str
    version: int

class PredictRequest(BaseModel):
    features: list[float]
    meta: Metadata
```

---

## Serving an ML Model

### Step 1: Train and save the model

```python
# train.py
import pickle
from sklearn.linear_model import LogisticRegression
import numpy as np

X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
y = np.array([0, 0, 1, 1])

model = LogisticRegression()
model.fit(X, y)

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model saved to model.pkl")
```

### Step 2: Load and serve the model in FastAPI

```python
# main.py
import pickle
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Load the model once when the server starts
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

class InputData(BaseModel):
    feature1: float
    feature2: float

@app.post("/predict")
def predict(data: InputData):
    features = np.array([[data.feature1, data.feature2]])
    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0].tolist()

    return {
        "prediction": int(prediction),
        "probability": probability
    }
```

### Step 3: Test with curl

```bash
curl -X POST "http://127.0.0.1:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{"feature1": 5.0, "feature2": 6.0}'
```

Expected response:

```json
{
  "prediction": 1,
  "probability": [0.23, 0.77]
}
```

**Important:** Load the model at startup, not inside the prediction function. Loading inside the function means the model is read from disk on every request, which is slow and wasteful.

---

## Lifespan Events

The recommended approach in modern FastAPI is to use a lifespan context manager. This gives you a clean place to load and unload resources like ML models.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import pickle

model_store = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs at startup
    with open("model.pkl", "rb") as f:
        model_store["model"] = pickle.load(f)
    print("Model loaded")

    yield  # The application runs here

    # Runs at shutdown
    model_store.clear()
    print("Model unloaded")

app = FastAPI(lifespan=lifespan)

@app.post("/predict")
def predict(data: InputData):
    model = model_store["model"]
    prediction = model.predict([[data.feature1, data.feature2]])
    return {"prediction": int(prediction[0])}
```

This replaces the older `@app.on_event("startup")` pattern which is now deprecated.

---

## File Uploads

Useful when your model takes images, CSVs, or documents as input.

```python
from fastapi import FastAPI, UploadFile, File
import shutil
import os

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)

    with open(f"uploads/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "status": "saved"
    }
```

For image classification with a CNN, you would read the uploaded file into memory, preprocess it, and pass it to the model:

```python
from PIL import Image
import io

@app.post("/classify-image")
async def classify_image(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    # preprocess and run through model here
    return {"label": "cat", "confidence": 0.92}
```

---

## CORS and Middleware

CORS (Cross-Origin Resource Sharing) must be enabled when a frontend running on a different port or domain calls your API. Without it, browsers block the request.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # List specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For development you can use `allow_origins=["*"]`, but in production always specify the exact domains.

---

## Response Models and Status Codes

Defining a response model tells FastAPI what the output will look like. It also filters out any extra fields you do not want to expose.

```python
from fastapi import HTTPException
from pydantic import BaseModel

class PredictResponse(BaseModel):
    prediction: int
    confidence: float
    label: str

@app.post("/predict", response_model=PredictResponse)
def predict(data: InputData):
    if data.feature1 < 0:
        raise HTTPException(status_code=400, detail="Feature values cannot be negative")

    features = [[data.feature1, data.feature2]]
    pred = model.predict(features)[0]
    conf = model.predict_proba(features)[0].max()

    return PredictResponse(
        prediction=int(pred),
        confidence=round(float(conf), 3),
        label="Positive" if pred == 1 else "Negative"
    )
```

Common HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | OK — request succeeded |
| 201 | Created — new resource created |
| 400 | Bad Request — invalid input |
| 401 | Unauthorized — authentication required |
| 403 | Forbidden — not allowed |
| 404 | Not Found |
| 422 | Unprocessable Entity — validation error (FastAPI default for bad input) |
| 500 | Internal Server Error |

---

## API Key Authentication

A simple approach for protecting endpoints without a full authentication system.

```python
from fastapi import Header, HTTPException

VALID_API_KEY = "your-secret-key"

@app.get("/secure-predict")
def secure_predict(x_api_key: str = Header(...)):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return {"result": "authorized prediction"}
```

The client passes the key as a header: `X-Api-Key: your-secret-key`.

For production, use environment variables to store the key:

```python
import os
VALID_API_KEY = os.getenv("API_KEY")
```

---

## Auto-Generated Docs

FastAPI generates interactive documentation automatically with no extra code.

| URL | Description |
|-----|-------------|
| `/docs` | Swagger UI — interactive, lets you test endpoints from the browser |
| `/redoc` | ReDoc — cleaner read-only documentation view |
| `/openapi.json` | Raw OpenAPI schema, usable by other tools |

You can customize the docs page:

```python
app = FastAPI(
    title="ML Prediction API",
    description="Serves a logistic regression classifier",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

---

## Project Structure

For anything beyond a single script, organize your project like this:

```
ml_api/
├── main.py                  # App entry point, includes routers
├── model.pkl                # Saved ML model
├── requirements.txt
├── Dockerfile
│
├── routers/
│   ├── __init__.py
│   ├── predict.py           # Prediction endpoints
│   └── health.py            # Health check endpoint
│
├── schemas/
│   ├── __init__.py
│   └── predict_schema.py    # Pydantic input/output models
│
└── services/
    ├── __init__.py
    └── ml_service.py        # Model loading and inference logic
```

Using APIRouter to split routes:

```python
# routers/predict.py
from fastapi import APIRouter
from schemas.predict_schema import InputData, PredictResponse
from services.ml_service import run_inference

router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
def predict(data: InputData):
    return run_inference(data)
```

```python
# main.py
from fastapi import FastAPI
from routers import predict, health

app = FastAPI(title="ML API")
app.include_router(predict.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
```

The `prefix` and `tags` arguments keep your API organized and make the auto-docs easier to read.

---

## Deployment

### Local development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production with Gunicorn

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

`-w 4` spawns 4 worker processes. A common rule of thumb is `2 * CPU cores + 1`.

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t ml-api .
docker run -p 8000:8000 ml-api
```

### Cloud options

| Platform | Best for |
|----------|---------|
| AWS EC2 + Docker | Full control, custom setups |
| AWS ECS / Fargate | Container-native, no server management |
| Google Cloud Run | Serverless containers, scales to zero |
| Azure App Service | Straightforward PaaS deployment |
| Railway / Render | Fast deployment for portfolio projects |

---

## Quick Reference

```
Request comes in
       |
FastAPI matches route
       |
Pydantic validates input
       |
Your function runs (model inference happens here)
       |
Response model filters output
       |
JSON sent back to client
```

---

## Requirements

```
fastapi
uvicorn
gunicorn
pydantic
scikit-learn
numpy
pillow       # for image uploads
python-multipart  # required for file uploads
```

Install all at once:

```bash
pip install fastapi uvicorn gunicorn pydantic scikit-learn numpy pillow python-multipart
```

---

*Built as part of the AI Engineering portfolio. For questions or improvements, open an issue or pull request.*
