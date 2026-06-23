# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ----------------------------------------------------------------------
# Database setup
# ----------------------------------------------------------------------
DATABASE_URL = "sqlite:///./data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)


# ----------------------------------------------------------------------
# FastAPI app
# ----------------------------------------------------------------------
app = FastAPI()


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/", response_class=HTMLResponse)
def read_root():
    # Retrieve all items and compute total
    db = SessionLocal()
    items = db.query(Item).all()
    total = sum(item.amount for item in items)
    db.close()

    # Build HTML page
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Simple Tracker</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4; }}
            .container {{ max-width: 800px; margin: auto; padding: 20px; background: #fff; }}
            h1 {{ text-align: center; }}
            form {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }}
            input[type=text], input[type=number] {{ flex: 1 1 200px; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }}
            button {{ padding: 10px 20px; background: #28a745; color: #fff; border: none; border-radius: 4px; cursor: pointer; }}
            button:hover {{ background: #218838; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }}
            th {{ background: #f8f8f8; }}
            @media (max-width: 600px) {{
                form {{ flex-direction: column; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Simple Tracker</h1>
            <form action="/add" method="post">
                <input type="text" name="description" placeholder="Description" required>
                <input type="number" step="0.01" name="amount" placeholder="Amount" required>
                <button type="submit">Add</button>
            </form>
            <h2>Entries</h2>
            <table>
                <thead>
                    <tr><th>Description</th><th>Amount</th></tr>
                </thead>
                <tbody>
                    {"".join(f"<tr><td>{item.description}</td><td>{item.amount:.2f}</td></tr>" for item in items)}
                </tbody>
            </table>
            <h3>Total: ${total:.2f}</h3>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/add")
def add_item(description: str = Form(...), amount: float = Form(...)):
    db = SessionLocal()
    new_item = Item(description=description, amount=amount)
    db.add(new_item)
    db.commit()
    db.close()
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    import os, uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))