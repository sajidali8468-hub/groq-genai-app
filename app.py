import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from groq import Groq
from pydantic import BaseModel

from core.prompts import SYSTEM_GUARDRAIL
from core.utils import log_performance

load_dotenv()

app = FastAPI(title="CST4625 GenAI Artifact")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app.mount("/static", StaticFiles(directory="static"), name="static")


class QueryRequest(BaseModel):
    user_input: str


@app.get("/")
async def serve_homepage():
    return FileResponse("static/index.html")


@app.post("/generate")
async def generate_response(request: QueryRequest):
    start_time = time.time()

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_GUARDRAIL},
                {"role": "user", "content": request.user_input},
            ],
            temperature=0.5,
            max_tokens=1024,
        )

        response_text = completion.choices[0].message.content
        duration = time.time() - start_time

        log_performance(duration, len(response_text))

        return {"output": response_text, "latency": f"{duration:.2f}s"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
