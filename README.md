# CGP

# TrustCare AI Backend System

AI based check-in, messaging and reporting system for TrustCare Care Recipient Application

---

# Tech Stack

- Python 3.14
- FastAPI
- MSSQL (SQLAlchemy Core)
- Windows + VS Code
- Uvicorn
- Azure OpenAI
- Azure AI Search
- Pydantic
- Transformers
- Sentence Transformers
- HTTPX
- Pandas
- NumPy


---
#Download the SQL Server ODBC Driver 17  (https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver17)


Windows:   https://go.microsoft.com/fwlink/?linkid=2266337

##  Clone the Repository
After cloning, navigate to that folder to run the following terminal commands inside the project.
## Open the Windows Terminal
Type: 

python -m venv venv

.\venv\Scripts\activate

You should see: 

(venv)

Install Dependencies:

pip install --upgrade pip

pip install -r requirements.txt


## To Run the App
.\venv\Scripts\activate

 uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

## Open with SWAGGER
http://127.0.0.1:8001/docs
