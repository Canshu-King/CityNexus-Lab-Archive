from fastapi import FastAPI

app = FastAPI(title="CityNexus MVP API", version="0.1.0")


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "database": "ok", "ai": "disabled"}
