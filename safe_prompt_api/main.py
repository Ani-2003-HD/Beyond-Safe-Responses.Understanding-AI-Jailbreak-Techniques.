import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Load environment variables
load_dotenv()

# Get API key from environment, with fallback
API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

app = FastAPI(title="Prompt Safety API")

class PromptRequest(BaseModel):
    prompt: str

class SafetyResponse(BaseModel):
    safe: bool
    prompt: str

class PromptSafetyMiddleware:
    """Middleware to check prompts for harmful content using Google's Gemini model."""
    
    def __init__(self):
        genai.configure(api_key=API_KEY)
    
    async def verify_prompt(self, prompt: str) -> bool:
        """
        Perform final safety verification using Google's Gemini model.
        
        Args:
            prompt: The user prompt to verify
            
        Returns:
            Boolean indicating if the prompt is safe
        """
        try:
            model = genai.GenerativeModel(model_name="gemini-1.5-pro")
            response = model.generate_content(f"{prompt}\n tell me the above prompts are safe or not answer in true of false only")
            print(response.text)
            return "true" in response.text.strip().lower() 
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
    
    async def process_prompt(self, prompt: str) -> dict:
        """
        Process a prompt through the safety middleware.
        
        Args:
            prompt: The user prompt to process
            
        Returns:
            Dictionary with safety assessment
        """
        is_safe = await self.verify_prompt(prompt)
        return {
            "prompt": prompt,
            "safety_assessment": {
                "safe": is_safe,
                "verification_method": "Google Gemini Pro"
            }
        }

# Initialize middleware
middleware = PromptSafetyMiddleware()

@app.post("/check-safety", response_model=SafetyResponse)
async def check_safety(request: PromptRequest):
    """
    Check if a prompt is safe.
    
    Args:
        request: PromptRequest containing the text to check
        
    Returns:
        SafetyResponse with safety assessment
    """
    try:
        is_safe = await middleware.verify_prompt(request.prompt)
        return SafetyResponse(
            safe=is_safe,
            prompt=request.prompt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)