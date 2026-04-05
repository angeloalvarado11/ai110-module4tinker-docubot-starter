# DocuBot

DocuBot is a small documentation assistant that helps answer developer questions about a codebase.  
It can operate in three different modes:

1. **Naive LLM mode**  
   Sends the entire documentation corpus to a Gemini model and asks it to answer the question.

2. **Retrieval only mode**  
   Uses a simple indexing and scoring system to retrieve relevant snippets without calling an LLM.

3. **RAG mode (Retrieval Augmented Generation)**  
   Retrieves relevant snippets, then asks Gemini to answer using only those snippets.

The docs folder contains realistic developer documents (API reference, authentication notes, database notes), but these files are **just text**. They support retrieval experiments and do not require students to set up any backend systems.

---

## Setup

### 1. Install Python dependencies

    pip install -r requirements.txt

### 2. Configure environment variables

Copy the example file:

    cp .env.example .env

Then edit `.env` to include your Gemini API key:

    GEMINI_API_KEY=your_api_key_here

If you do not set a Gemini key, you can still run retrieval only mode.

---

## Running DocuBot

Start the program:

    python main.py

Choose a mode:

- **1**: Naive LLM (Gemini reads the full docs)  
- **2**: Retrieval only (no LLM)  
- **3**: RAG (retrieval + Gemini)

You can use built in sample queries or type your own.

---

## Running Retrieval Evaluation (optional)

    python evaluation.py

This prints simple retrieval hit rates for sample queries.

---

## Modifying the Project

You will primarily work in:

- `docubot.py`  
  Implement or improve the retrieval index, scoring, and snippet selection.

- `llm_client.py`  
  Adjust the prompts and behavior of LLM responses.

- `dataset.py`  
  Add or change sample queries for testing.

---

## Requirements

- Python 3.9+
- A Gemini API key for LLM features (only needed for modes 1 and 3)
- No database, no server setup, no external services besides LLM calls

TF Response:
The core concepts students need to understand from this Tinker is the differences between a Naive LLM mode, Retrieval, and RAG mode. I found this Tinker to be especially helpful in making a connection between all these buzzwords and getting your hands dirty for yourself. I believe students will struggle most with the fine tuning of the guard rail, at least that's where I ran into the most trouble. Asking a question like “What is the weather in Houston?” had my guard rail response, but something slightly similar like “What is the weather like in Houston?” caused my program to answer something related to Postman. As always, another point of trouble will probably be the installation of packages, but a simple py -m prepended to the command fixed my issues. I found AI to be helpful in all phases of the Tinker. A way I would guide the student without giving them the answer is to step back and understand what’s going on with the 3 functions that make up this Tinker. What is it asking of you? How does this affect the grand scheme of things? Can you walk through what it is trying to do? If not, Copilot can be a great help in walking through how the code works.
