

# CardGuard API



A Python REST API that evaluates fictional credit card transactions using rule-based risk checks and stores transaction history in SQLite.



## Features



\- Submit and evaluate transactions

\- Flag high-value transactions ($2,000 or more)

\- Detect three or more transactions on the same card within ten minutes

\- Flag changes in transaction country within thirty minutes

\- Store transaction history in SQLite

\- Retrieve all transactions, filter by card ID, or retrieve a transaction by ID

\- Validate incoming requests and return appropriate HTTP status codes

\- Automated tests using pytest



## Tech Stack



Python, FastAPI, SQLite, Pydantic, pytest, HTTPX



## Getting Started



Create and activate a Python virtual environment, then install dependencies:



```bash

pip install -r requirements.txt

```



Start the API:



```bash

python -m uvicorn main:app --reload

```



Open the interactive documentation:



http://127.0.0.1:8000/docs



## Example Request



POST /transactions



```json


{
  "card_id": "DEMO-1001",
  "amount": 2450,
  "merchant": "Demo Electronics",
  "country": "US"
}

```



The API flags this transaction for review because its amount exceeds the configured threshold.



## Testing



Run:



```bash

python -m pytest -v

```



The test suite covers normal transactions, high amounts, rapid country changes, transaction velocity, history retrieval, invalid input, and missing records.



## Disclaimer



CardGuard is an educational portfolio project using fictional transaction data. Its risk rules are illustrative and are not intended for real-world fraud detection or payment authorization.

