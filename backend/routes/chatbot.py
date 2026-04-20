from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    response: str
    is_agriculture_related: bool

# Agriculture-specific system prompt
AGRICULTURE_SYSTEM_PROMPT = """You are FarmLens AI Assistant, an expert agricultural advisor specializing in:
- Crop diseases and pest management
- Fertilizer and nutrient management
- Irrigation and water management
- Soil health and crop rotation
- Organic farming practices
- Agricultural best practices
- Crop selection and planting guidance
- Harvest timing and post-harvest management
- Weather-related farming advice
- Sustainable agriculture

IMPORTANT RULES:
1. ONLY answer questions related to agriculture, farming, crops, livestock, and related topics
2. If a question is NOT about agriculture, politely decline and say: "I'm FarmLens AI Assistant, specialized in agriculture. I can only help with farming, crops, and agricultural topics. Please ask me about agriculture-related matters."
3. Provide practical, actionable advice
4. Use simple language that farmers can understand
5. When discussing chemicals or treatments, always mention safety precautions
6. Encourage sustainable and eco-friendly practices when possible
7. If you're unsure, recommend consulting local agricultural extension services

Keep responses concise (2-3 paragraphs maximum) and focused."""

def is_agriculture_related(message: str) -> bool:
    """Check if the message is agriculture-related using keywords"""
    agriculture_keywords = [
        'crop', 'farm', 'plant', 'soil', 'seed', 'harvest', 'pest', 'disease',
        'fertilizer', 'irrigation', 'agriculture', 'cultivation', 'livestock',
        'cattle', 'poultry', 'vegetable', 'fruit', 'grain', 'wheat', 'rice',
        'corn', 'tomato', 'potato', 'pesticide', 'herbicide', 'fungicide',
        'organic', 'compost', 'manure', 'tractor', 'planting', 'growing',
        'yield', 'season', 'weather', 'drought', 'rain', 'water', 'field',
        'garden', 'greenhouse', 'nursery', 'agri', 'कृषि', 'खेती', 'फसल',
        'after', 'before', 'rotation', 'succession'  # Added for crop rotation questions
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in agriculture_keywords)

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for agriculture-specific queries using Gemini
    """
    try:
        # Check if question is agriculture-related
        if not is_agriculture_related(request.message):
            return ChatResponse(
                response="I'm FarmLens AI Assistant, specialized in agriculture. I can only help with farming, crops, and agricultural topics. Please ask me about agriculture-related matters like crop diseases, pest management, fertilizers, irrigation, or any farming practices.",
                is_agriculture_related=False
            )
        
        # Initialize Gemini client
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Build conversation history for context
        conversation_context = AGRICULTURE_SYSTEM_PROMPT + "\n\n"
        
        # Add recent conversation history (last 5 exchanges)
        for msg in request.history[-10:]:
            role_label = "User" if msg.role == "user" else "Assistant"
            conversation_context += f"{role_label}: {msg.content}\n"
        
        # Add current question
        full_prompt = f"{conversation_context}\nUser: {request.message}\nAssistant:"
        
        # Generate response using Gemini
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=full_prompt
        )
        
        return ChatResponse(
            response=response.text.strip(),
            is_agriculture_related=True
        )
        
    except Exception as e:
        print(f"Error in chatbot: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agriculture-chatbot"}
