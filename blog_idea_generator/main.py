
import os
from typing import List, Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import httpx
from pydantic import BaseModel
import json
from prompt_templates import BLOG_IDEA_PROMPT

app = FastAPI(title="Blog Idea Generator")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


WEBUI_ENABLED = True  
WEBUI_BASE_URL = "https://chat.ivislabs.in/api"
API_KEY = "sk-d40e1f1ad71d4d33a31c1ce45447c994"  

DEFAULT_MODEL = "gemma2:2b"  

OLLAMA_ENABLED = True  # Set to False to use only the web UI API
OLLAMA_HOST = "localhost"
OLLAMA_PORT = "11434"
OLLAMA_API_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api"

class GenerationRequest(BaseModel):
    niche: str
    num_ideas: int = 3
    include_outline: bool = True
    tone: Optional[str] = "professional"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_ideas(
    niche: str = Form(...),
    num_ideas: int = Form(3),
    include_outline: bool = Form(True),
    tone: str = Form("professional"),
    model: str = Form(DEFAULT_MODEL)
):
    try:
      
        prompt = BLOG_IDEA_PROMPT.format(
            niche=niche,
            num_ideas=num_ideas,
            include_outline="with detailed outlines" if include_outline else "without outlines",
            tone=tone
        )
        
        
        if WEBUI_ENABLED:
            try:
             
                messages = [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
          
                request_payload = {
                    "model": model,
                    "messages": messages
                }
                print(f"Attempting open-webui API with payload: {json.dumps(request_payload)}")
                
              
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{WEBUI_BASE_URL}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json=request_payload,
                        timeout=60.0
                    )
                  
                    print(f"Open-webui API response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                      
                        generated_text = ""
                        
                        
                        if "choices" in result and len(result["choices"]) > 0:
                            choice = result["choices"][0]
                            if "message" in choice and "content" in choice["message"]:
                                generated_text = choice["message"]["content"]
                            elif "text" in choice:
                                generated_text = choice["text"]
                        elif "response" in result:
                            generated_text = result["response"]
                        
                        if generated_text:
                            return {"generated_ideas": generated_text}
            except Exception as e:
                print(f"Open-webui API attempt failed: {str(e)}")
        if OLLAMA_ENABLED:
            print("Falling back to direct Ollama API")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_API_URL}/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail="Failed to generate content from Ollama API")
                
                result = response.json()
                generated_text = result.get("response", "")
                
                return {"generated_ideas": generated_text}
                

        raise HTTPException(status_code=500, detail="Failed to generate content from any available LLM API")
            
    except Exception as e:
        import traceback
        print(f"Error generating blog ideas: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating blog ideas: {str(e)}")

@app.get("/models")
async def get_models():
    try:

        if WEBUI_ENABLED:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{WEBUI_BASE_URL}/models",
                        headers={
                            "Authorization": f"Bearer {API_KEY}"
                        }
                    )
                    
                    if response.status_code == 200:
                        models_data = response.json()
                        
  
                        if "data" in models_data and isinstance(models_data["data"], list):
                            model_names = []
                            for model in models_data["data"]:
                                if "id" in model:
                                    model_names.append(model["id"])
                            
                            if model_names:
                                return {"models": model_names}
            except Exception as e:
                print(f"Error fetching models from open-webui API: {str(e)}")
        
        if OLLAMA_ENABLED:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{OLLAMA_API_URL}/tags")
                    if response.status_code == 200:
                        models = response.json().get("models", [])
                        model_names = [model.get("name") for model in models]
                        return {"models": model_names}
            except Exception as e:
                print(f"Error fetching models from Ollama: {str(e)}")
      
        fallback_models = [DEFAULT_MODEL, "gemma2:2b", "qwen2.5:0.5b", "deepseek-r1:1.5b", "deepseek-coder:latest"]
        return {"models": fallback_models}
    except Exception as e:
        print(f"Unexpected error in get_models: {str(e)}")
        return {"models": [DEFAULT_MODEL]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)