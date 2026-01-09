# 🤖 Self-Service Knowledge Assistant

An AI-powered HR onboarding assistant that allows users to upload internal HR documents (PDF, DOCX, TXT) and ask natural-language questions. The system uses **Retrieval-Augmented Generation (RAG)** to provide accurate, document-grounded answers with citations.

## 🚀 Features

* Upload and process HR documents via UI
* Intelligent document chunking with semantic boundaries
* Vector-based semantic search using FAISS
* Accurate answers generated using Groq LLM
* Source citations for transparency
* Category tagging (Leave, Benefits, Legal, etc.)
* Fully local execution (except LLM inference)

---

## 🛠️ Setup Instructions (Run Locally)

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/mishra-yogendra/Self-Service-Knowledge-Assistant
cd Self-Service-Knowledge-Assistant
```

---

### 2️⃣ Create and Activate Virtual Environment

```bash
python -m venv venv
```

**Windows**

```bash
venv\Scripts\activate
```

**Mac / Linux**

```bash
source venv/bin/activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies include Streamlit, FAISS, Sentence Transformers, Groq SDK, and document parsers .

---

### 4️⃣ Run the Application

```bash
streamlit run app.py
```
---

### 5️⃣ Usage Flow

1. Enter your **Groq API key** in the sidebar
2. Upload HR documents (PDF, DOCX, TXT)
3. Click **Process Documents**
4. Ask questions in the chat interface
5. View answers with citations and categories

The main application logic is implemented in `app.py` .

---

## 🧠 Chunking Strategy (Document Processing)

Document ingestion and chunking are handled by the `DocumentProcessor` class .

### Strategy Used

The chunking approach is **semantic-first**, not naive fixed-size splitting:

1. **Text Extraction**

   * PDF: Page-wise extraction
   * DOCX: Paragraph-level extraction
   * TXT: Full text read

2. **Semantic Splitting**

   * Split on:

     * Section headers (e.g., `1.`, `LEAVE POLICY`, `Section 2:`)
     * Paragraph boundaries (`\n\n`)
   * Preserves logical meaning (policies, rules, clauses)

3. **Chunk Size Control**

   * Target size: **~1000 characters**
   * Overlap: **~200 characters** to preserve context continuity

4. **Metadata Preservation**

   * Each chunk stores:

     * Source document name
     * Chunk type (section / paragraph group)

### Why This Works Well

* Prevents breaking policies mid-sentence
* Improves retrieval relevance
* Reduces hallucination risk during generation

---

## 📦 Vector Database Choice

### Vector DB Used: **FAISS (Flat L2 Index)**

Implemented inside `RAGEngine` .

#### Why FAISS?

* Fast in-memory similarity search
* Ideal for small-to-medium document collections
* No external service dependency
* Easy to deploy locally or on servers

#### Embeddings

* Model: `all-MiniLM-L6-v2`
* Dimension: **384**
* Optimized for semantic similarity
* Low latency and lightweight

#### Retrieval Flow

1. Convert chunks → embeddings
2. Store embeddings in FAISS index
3. Embed user query
4. Retrieve top-K closest chunks
5. Send retrieved context to LLM

---

## 🤖 LLM & RAG Design

* **LLM Provider:** Groq
* **Model:** `llama-3.3-70b-versatile`
* **Temperature:** 0.3 (factual, low hallucination)
* **Strict grounding rules:**

  * Answer only from retrieved context
  * Explicitly say when information is missing
  * Cite document sources

This ensures compliance-safe HR responses.

## 📁 Project Structure

```
├── app.py                  # Streamlit UI and app orchestration
├── document_processor.py   # Text extraction & intelligent chunking
├── rag_engine.py           # Embeddings, FAISS, retrieval & LLM
├── requirements.txt        # Dependencies
└── README.md               # Documentation
```



## ⚠️ Known Limitations

* **In-memory vector store only**
  The FAISS index is created and maintained entirely in memory. As a result, all document embeddings are lost when the application restarts, requiring documents to be reprocessed on each launch.

* **Keyword-based query categorization**
  Query classification (e.g., Leave, Benefits, Legal) relies on simple keyword matching. This approach may misclassify complex, implicit, or multi-intent queries.

* **No document-level access control**
  All uploaded documents are globally accessible within the application. There is no role-based or permission-based restriction on document visibility.

* **Limited scalability**
  The system is optimized for small to medium-sized document collections. Very large datasets may lead to increased memory consumption and slower retrieval performance.

* **No OCR support for scanned PDFs**
  Documents that contain scanned images without extractable text are not supported, as OCR processing is not currently integrated.

* **Single-session usage**
  The application is designed for a single active session and does not support concurrent multi-user access or collaboration.

---

## 🔮 Future Improvements

* **Persistent vector storage**
  Store embeddings on disk or use a managed vector database (e.g., FAISS persistence, Chroma, Pinecone) to avoid reprocessing documents after application restarts.

* **ML-based query classification**
  Replace rule-based categorization with an embedding-based or fine-tuned machine learning classifier to improve intent detection accuracy.

* **Advanced retrieval techniques**
  Implement hybrid retrieval (keyword + vector search), reranking models, or Max Marginal Relevance (MMR) to improve the relevance and diversity of retrieved context.

* **OCR integration**
  Add OCR capabilities (e.g., Tesseract or cloud-based OCR services) to support scanned PDFs and image-based documents.

* **User authentication and access control**
  Introduce authentication mechanisms and role-based access control to restrict document visibility based on user roles.

* **Conversation memory and follow-ups**
  Enhance multi-turn conversational capabilities by maintaining dialogue context across user interactions.

* **Deployment and scalability enhancements**
  Containerize the application using Docker and deploy it on cloud platforms with autoscaling and load balancing support.

* **Feedback loop for answer quality**
  Enable user feedback on responses and leverage this data to continuously improve retrieval accuracy and answer quality.

---

## ✅ Summary

This project demonstrates a **RAG system** with:

* Thoughtful chunking
* Efficient vector search
* Grounded LLM generation
* Clear UX and citations

It is well-suited for **internal knowledge bases**, **HR onboarding**, and **policy assistants**.

---
