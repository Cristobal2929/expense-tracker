# -*- coding: utf-8 -*-
import os
from datetime import datetime

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI()

# ---------- Database setup ----------
SQLALCHEMY_DATABASE_URL = "sqlite:///./expenses.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    concept = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)


@app.on_event("startup")
def startup():
    """Create tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


# ---------- Helper functions ----------
def get_expenses():
    with SessionLocal() as db:
        expenses = db.query(Expense).order_by(Expense.date.desc()).all()
        total = sum(e.amount for e in expenses)
    return expenses, total


def add_expense_to_db(concept: str, amount: float, date_str: str):
    expense_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    with SessionLocal() as db:
        db.add(Expense(concept=concept, amount=amount, date=expense_date))
        db.commit()


# ---------- Routes ----------
@app.get("/", response_class=HTMLResponse)
def read_root():
    expenses, total = get_expenses()
    rows_html = "\n".join(
        f"<tr><td>{e.concept}</td><td>{e.amount:.2f}</td><td>{e.date}</td></tr>"
        for e in expenses
    )
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Expense Tracker</title>
        <style>
            body{{font-family:Arial,sans-serif;margin:20px;background:#f5f5f5;}}
            .container{{max-width:800px;margin:auto;background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);}}
            h1{{text-align:center;}}
            form{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px;}}
            input,button{{padding:8px;font-size:1rem;}}
            input[type=text],input[type=date],input[type=number]{{flex:1 1 200px;}}
            button{{background:#28a745;color:#fff;border:none;border-radius:4px;cursor:pointer;}}
            button:hover{{background:#218838;}}
            table{{width:100%;border-collapse:collapse;margin-top:10px;}}
            th,td{{border:1px solid #ddd;padding:8px;text-align:left;}}
            th{{background:#f2f2f2;}}
            @media(max-width:600px){{form{{flex-direction:column;}}}}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Expense Tracker</h1>
            <form method="post" action="/add">
                <input type="text" name="concept" placeholder="Concept" required>
                <input type="number" step="0.01" name="amount" placeholder="Amount" required>
                <input type="date" name="date" required>
                <button type="submit">Add Expense</button>
            </form>
            <table>
                <thead>
                    <tr><th>Concept</th><th>Amount</th><th>Date</th></tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
                <tfoot>
                    <tr><td><strong>Total</strong></td><td colspan="2"><strong>{total:.2f}</strong></td></tr>
                </tfoot>
            </table>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/add")
def add_expense(
    concept: str = Form(...),
    amount: float = Form(...),
    date: str = Form(...)
):
    add_expense_to_db(concept, amount, date)
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))