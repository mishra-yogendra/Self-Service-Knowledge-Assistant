import numpy as np
import faiss
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from groq import Groq
import re


class RAGEngine:
    """Retrieval-Augmented Generation engine using FAISS and Groq"""

    def __init__(self, groq_api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        """
        Initialize RAG engine

        Args:
            groq_api_key: API key for Groq
            model_name: Groq model to use for generation
        """
        self.groq_client = Groq(api_key=groq_api_key)
        self.model_name = model_name

        # Initialize embedding model (lightweight and fast)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dimension = 384  # Dimension for all-MiniLM-L6-v2

        # FAISS index
        self.index = None
        self.chunks = []

    def build_index(self, chunks: List[Dict]):
        """
        Build FAISS index from document chunks

        Args:
            chunks: List of chunk dictionaries with 'text' and 'metadata'
        """
        self.chunks = chunks

        # Generate embeddings for all chunks
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=True)

        # Create FAISS index (L2 distance)
        self.index = faiss.IndexFlatL2(self.embedding_dimension)

        # Add embeddings to index
        embeddings_np = np.array(embeddings).astype('float32')
        self.index.add(embeddings_np)

    def retrieve_relevant_chunks(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieve most relevant chunks for a query

        Args:
            query: User query
            top_k: Number of top chunks to retrieve

        Returns:
            List of relevant chunks with similarity scores
        """
        if self.index is None or len(self.chunks) == 0:
            return []

        # Generate query embedding
        query_embedding = self.embedder.encode([query])
        query_embedding_np = np.array(query_embedding).astype('float32')

        # Search in FAISS index
        distances, indices = self.index.search(query_embedding_np, min(top_k, len(self.chunks)))

        # Prepare results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):  # Ensure valid index
                chunk = self.chunks[idx].copy()
                chunk['similarity_score'] = float(1 / (1 + distance))  # Convert distance to similarity
                results.append(chunk)

        return results

    def categorize_query(self, query: str) -> str:
        """
        Categorize the query based on keywords

        Categories: Benefits, Legal, Internal Culture, Leave, Remote Work, General
        """
        query_lower = query.lower()

        # Define category keywords
        categories = {
            'Leave': ['leave', 'vacation', 'pto', 'time off', 'holiday', 'sick', 'parental', 'maternity', 'paternity'],
            'Benefits': ['benefit', 'insurance', 'health', 'dental', 'vision', '401k', 'retirement', 'pension',
                         'compensation', 'salary'],
            'Legal': ['legal', 'policy', 'compliance', 'regulation', 'contract', 'agreement', 'confidentiality', 'nda'],
            'Remote Work': ['remote', 'work from home', 'wfh', 'hybrid', 'office', 'coffee shop', 'coworking'],
            'Internal Culture': ['culture', 'values', 'mission', 'team', 'events', 'diversity', 'inclusion']
        }

        # Check each category
        for category, keywords in categories.items():
            if any(keyword in query_lower for keyword in keywords):
                return category

        return 'General'

    def generate_answer(self, query: str, context_chunks: List[Dict]) -> str:
        """
        Generate answer using Groq LLM with retrieved context

        Args:
            query: User query
            context_chunks: Retrieved relevant chunks

        Returns:
            Generated answer
        """
        if not context_chunks:
            return ("I don't have enough information in the knowledge base to answer this question. "
                    "Please make sure the relevant HR documents have been uploaded, or try rephrasing your question.")

        # Prepare context from chunks
        context = "\n\n---\n\n".join([
            f"[Source: {chunk['metadata']['source']}]\n{chunk['text']}"
            for chunk in context_chunks
        ])

        # Create prompt for Groq
        prompt = f"""You are an HR Onboarding Assistant. Your role is to answer employee questions based ONLY on the provided company documents.

IMPORTANT RULES:
1. Answer ONLY based on the context provided below
2. If the answer is not in the context, say "I don't have this information in the uploaded documents"
3. Be specific and cite which document the information comes from
4. If there are step-by-step processes, list them clearly
5. Be helpful but concise

CONTEXT FROM HR DOCUMENTS:
{context}

EMPLOYEE QUESTION:
{query}

ANSWER (based only on the context above):"""

        try:
            # Call Groq API
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful HR assistant that answers questions based only on provided company documents. Never make up information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model_name,
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=1000
            )

            answer = chat_completion.choices[0].message.content
            return answer

        except Exception as e:
            return f"Error generating response: {str(e)}"

    def query(self, query: str, top_k: int = 3) -> Dict:
        """
        Main query method that retrieves context and generates answer

        Args:
            query: User query
            top_k: Number of chunks to retrieve

        Returns:
            Dictionary with answer, category, and citations
        """
        # Retrieve relevant chunks
        relevant_chunks = self.retrieve_relevant_chunks(query, top_k)

        # Generate answer
        answer = self.generate_answer(query, relevant_chunks)

        # Categorize query
        category = self.categorize_query(query)

        # Prepare citations
        citations = [
            {
                'source': chunk['metadata']['source'],
                'text': chunk['text'],
                'similarity': chunk['similarity_score']
            }
            for chunk in relevant_chunks
        ]

        return {
            'answer': answer,
            'category': category,
            'citations': citations
        }