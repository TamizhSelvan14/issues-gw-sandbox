from fastapi import FastAPI

app = FastAPI(title="GitHub Issues Gateway (Starter)")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
