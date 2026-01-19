import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env vars from the parent directory or current directory
load_dotenv()

# Import integration logic
# We will use dynamic imports or just simple logic here to keep it consolidated
from gen_ai_hub.proxy.native.openai import chat as openai_chat
from gen_ai_hub.proxy.native.google_vertexai.clients import GenerativeModel
from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
from gen_ai_hub.proxy.langchain.init_models import init_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from gen_ai_hub.proxy.native.amazon.clients import Session as BedrockSession
import json

app = FastAPI()

# CORS Configuration
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    provider: str
    prompt: str

@app.get("/")
def read_root():
    return {"message": "Native Integrations Backend Running"}

@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    print(f"Received request: {request.provider} - {request.prompt}")
    
    try:
        if request.provider == "openai":
            # OpenAI Logic
            messages = [{"role": "user", "content": request.prompt}]
            # Ensure model name matches your deployment
            response = openai_chat.completions.create(model_name='gpt-4o', messages=messages)
            return {"result": response.choices[0].message.content}
            
        elif request.provider == "vertex":
            # Vertex AI Logic
            proxy_client = get_proxy_client('gen-ai-hub')
            model = GenerativeModel(proxy_client=proxy_client, model_name='gemini-1.5-flash')
            content = [{"role": "user", "parts": [{"text": request.prompt}]}]
            response = model.generate_content(content)
            return {"result": response.text}
            
        elif request.provider == "langchain":
            # LangChain Logic
            llm = init_llm('gpt-4o')
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant."),
                ("user", "{text}")
            ])
            chain = prompt_template | llm | StrOutputParser()
            response = chain.invoke({'text': request.prompt})
            return {"result": response}

        elif request.provider == "bedrock":
            # Amazon Bedrock Logic
            # Using Titan or Claude based on previous script attempts
            # Note: User had issues with model names, using a safe default or what worked
            # Trying Claude as per user's last edit attempt
            model_name = "anthropic--claude-3-sonnet" 
            bedrock = BedrockSession().client(model_name=model_name)
            
            # Claude 3 payload structure
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ]
            })
            
            response = bedrock.invoke_model(body=body)
            response_body = json.loads(response.get("body").read())
            # Basic parsing for Claude response
            return {"result": response_body['content'][0]['text']}
            
        else:
            raise HTTPException(status_code=400, detail="Unknown provider")

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        # Raise generic helper message + actual error
        raise HTTPException(status_code=500, detail=f"Integration Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8090, reload=True)
