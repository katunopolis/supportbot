from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Sample in-memory storage (replace with DB queries later)
requests = {}

class SupportRequest(BaseModel):
    user_id: int
    issue: str

@app.get("/")
async def root():
    return {"message": "Welcome to the Telegram Support App API"}

@app.post("/request")
async def create_request(request: SupportRequest):
    request_id = len(requests) + 1
    requests[request_id] = {"user_id": request.user_id, "issue": request.issue, "status": "Open"}
    return {"request_id": request_id, "message": "Request submitted successfully"}

@app.get("/requests/{request_id}")
async def get_request(request_id: int):
    if request_id in requests:
        return requests[request_id]
    return {"error": "Request not found"}

import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
