# CGP

# TrustCare AI System

AI-powered elderly care assistant backend for the TrustCare platform.
This system provides intelligent conversational support, personalized RAG (Retrieval-Augmented Generation), AI-generated daily and weekly caregiver reports, emotional analysis, check-in management, and vector-based memory retrieval for elderly users.


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
- all-MiniLM-L6-v2
- pytz
- AsyncIO

---

# Features

## AI Conversational Assistant

* Elderly-friendly conversational AI
* Context-aware responses
* Emotional tone adaptation
* Mood detection from user messages
* Persistent memory-based conversations
* Retrieval-Augmented Generation (RAG)
* TTS and STT are added with the mobile application.

---

## Agentic RAG Retrieval System

The system uses an intelligent retrieval planner instead of simple keyword routing.

### Retrieval Sources

The AI dynamically retrieves relevant information from:

* Basic user information
* Elder profile
* Medical profile
* Appointments
* Meals
* Caregiver notes
* Past conversation memory
* AI-generated care reports

### Agentic Retrieval Flow

1. User asks a question
2. Retrieval planner analyzes the request
3. System decides:

   * which data sources are needed
   * which APIs to call
   * whether vector memory retrieval is required
4. Relevant structured data is collected
5. Azure AI Search retrieves vector memories
6. LLM generates the final response

---

# AI Check-In System

The platform supports AI-powered daily elderly wellness check-ins.

## Morning Check-In

Available during:

* 08:00 → 11:59 (user local timezone)

## Night Check-In

Available during:

* 16:00 → 23:59 (user local timezone)

## Features

* Timezone-aware scheduling
* Personalized AI-generated greetings
* Mood detection
* Conversation continuation
* Vector memory indexing
* Emotional monitoring
* Caregiver-supportive interaction style

---

# Daily Report Generation

AI automatically generates professional caregiver daily reports.

## Daily Report Includes

* Mood observations
* Emotional state analysis
* Medication adherence insights
* Meal adherence insights
* Check-in engagement analysis
* Behavioral observations
* Risk flags
* Caregiver recommendations

## Data Sources

Daily reports are generated using:

* Check-in conversations
* Medication adherence APIs
* Meal adherence APIs
* Elder forms
* Mood detection data

## Features

* Structured JSON report output
* AI summarization
* Vector indexing for future retrieval
* Source tracking
* Duplicate prevention

---

# Weekly Report Generation

Weekly caregiver reports are generated from:

* Daily reports
* Check-in summaries
* Medication patterns
* Meal patterns
* Vitals
* SOS alerts

## Weekly Report Includes

* Mood trends
* Engagement patterns
* Nutrition patterns
* Medication adherence overview
* Safety concerns
* Weekly summaries
* Caregiver recommendations

## Features

* AI-generated structured JSON
* Source traceability
* Professional caregiver summaries
* Historical retrieval support

---

# Azure AI Search Integration

The system uses Azure AI Search for intelligent memory retrieval.

## Features Used

### Vector Search

Used for:

* semantic memory retrieval
* similarity search
* conversational memory matching


### Embedding-Based Retrieval

User messages and AI responses are:

* embedded into vectors
* indexed into Azure AI Search
* retrieved later using similarity search

---

# AI Architecture

## Core Components

### Conversational AI

* LLM-based response generation
* Mood-aware prompting
* Elderly-supportive interaction design

### Agentic Retrieval Planner

Determines:

* user intent
* required data sources
* memory retrieval strategy

### Vector Memory System

Stores:

* chat conversations
* AI responses
* caregiver reports
* emotional context

### Report Generation Engine

Creates:

* daily reports
* weekly reports
* summarized caregiver insights

---


# Safety and AI Behavior Rules

The assistant:

* avoids hallucinations
* avoids unsupported medical advice
* uses structured data as priority
* responds calmly and respectfully
* does not expose technical systems
* encourages caregiver/doctor contact for serious concerns

---

# Memory and Indexing

The system indexes:

* user messages
* AI responses
* generated reports

Indexed data includes:

* embeddings
* moods
* timestamps
* thread IDs
* report metadata

This enables:

* semantic retrieval
* long-term memory
* contextual conversations

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

## env
```
DATABASE_URL=mssql+pyodbc://CGP_project_login:xxxxxx@xxxxxxx:1433/CGP_DB?driver=ODBC+Driver+17+for+SQL+Server
## AZURE AI SEARCH
SEARCH_ENDPOINT=https://xxxx.search.windows.net
SEARCH_KEY=
SEARCH_INDEX=
REPORT_SEARCH_INDEX=

LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=openai-gpt-oss-120b

## EXTERNAL CRUD BACKEND

CRUD_API=http://xxx:8000
APP_TIMEZONE=Asia/Colombo
DEBUG=True
```