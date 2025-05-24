from fastapi import FastAPI, Request
@app.get("/")
def root():
    return {"hello": "world"}
