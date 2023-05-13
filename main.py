import asyncio
import json
from EdgeGPT import Chatbot
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
app = FastAPI()

async def process_message(user_message, context):
    chatbot = await Chatbot.create(cookie_path="cookies.json")
    try:
        async for _, response in chatbot.ask_stream(prompt=user_message, conversation_style="creative", raw=True,
                                                    webpage_context=context, search_result=True):
            yield response
    except Exception as e:
        yield {"type": "error", "error": str(e)}
    finally:
        await chatbot.close()

@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    chatbot = await Chatbot.create(cookie_path="cookies.json")
    try:
        while True:
            try:
                message = await websocket.receive_text()
                print(message)
                request = json.loads(message)
                user_message = request['message']
                context = request['context']
                async for response in process_message(user_message, context):
                    await websocket.send_json(response)
            except WebSocketDisconnect:
                break
    except Exception as e:
        await websocket.send_json({"type": "error", "error": str(e)})
    finally:
        await chatbot.close()

@app.get("/{tail:path}")
async def http_handler(tail: str):
    file_path = "/" + tail if tail else "/index.html"
    return FileResponse('.' + file_path)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="localhost", port=65432)
