import uvicorn
from app.main import app
from app.database.session import init_db
import os

if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Run the application with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False,
        workers=1
    ) 