import os
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse


load_dotenv()

app = FastAPI(title="ToDo App v1.0")


@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Todo App</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            .todo-item {
                padding: 10px;
                margin: 5px 0;
                background-color: #f5f5f5;
                border-left: 3px solid #4CAF50;
            }
        </style>
    </head>
    <body>
        <h1>My Todo List</h1>
        <div class="todo-item">Sample todo item 1</div>
        <div class="todo-item">Sample todo item 2</div>
        <div class="todo-item">Sample todo item 3</div>
    </body>
    </html>
    """
    return html_content


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    print(f"Server started in port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
