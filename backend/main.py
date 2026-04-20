from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routes.analyze import router as analyze_router
from routes.history import router as history_router
from routes.feedback import router as feedback_router
from routes.chatbot import router as chatbot_router

app = FastAPI(title="FarmLens API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "http://localhost:8081", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(analyze_router)
app.include_router(history_router)
app.include_router(feedback_router)
app.include_router(chatbot_router, prefix="/api/chatbot", tags=["chatbot"])


@app.get("/")
def root():
    return {"status": "FarmLens API is running"}
