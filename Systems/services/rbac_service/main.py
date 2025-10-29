from fastapi import FastAPI
import uvicorn

app = FastAPI(title="rbac_service")

@app.get("/health")
def health():
    return {"status":"ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8103)
