import streamlit as st
import os
from pathlib import Path
from document_processor import DocumentProcessor
from rag_engine import RAGEngine
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="HR Onboarding Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    .citation-box {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        padding: 0.8rem;
        margin-top: 0.5rem;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'rag_engine' not in st.session_state:
    st.session_state.rag_engine = None
if 'doc_processor' not in st.session_state:
    st.session_state.doc_processor = DocumentProcessor()

# Sidebar for admin features
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/employee-card.png", width=80)
    st.title("Admin Panel")

    tab1, tab2 = st.tabs(["📤 Upload Documents", "📚 Knowledge Base"])

    with tab1:
        st.subheader("Upload HR Documents")
        api_key = st.text_input("Groq API Key", type="password", help="Enter your Groq API key")

        uploaded_files = st.file_uploader(
            "Choose documents",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True
        )

        if st.button("Process Documents", type="primary"):
            if not api_key:
                st.error("Please provide a Groq API key")
            elif not uploaded_files:
                st.error("Please upload at least one document")
            else:
                with st.spinner("Processing documents..."):
                    try:
                        # Save uploaded files temporarily
                        temp_dir = Path("temp_uploads")
                        temp_dir.mkdir(exist_ok=True)

                        file_paths = []
                        for uploaded_file in uploaded_files:
                            file_path = temp_dir / uploaded_file.name
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            file_paths.append(str(file_path))

                        # Process documents
                        chunks = st.session_state.doc_processor.process_documents(file_paths)

                        # Initialize RAG engine
                        st.session_state.rag_engine = RAGEngine(api_key)
                        st.session_state.rag_engine.build_index(chunks)

                        st.success(f"Successfully processed {len(uploaded_files)} documents with {len(chunks)} chunks!")

                        # Clean up temp files
                        for fp in file_paths:
                            os.remove(fp)

                    except Exception as e:
                        st.error(f"Error processing documents: {str(e)}")

    with tab2:
        st.subheader("Current Knowledge Base")
        if st.session_state.rag_engine and st.session_state.rag_engine.chunks:
            st.metric("Total Chunks", len(st.session_state.rag_engine.chunks))

            # Show document sources
            sources = set([chunk['metadata']['source'] for chunk in st.session_state.rag_engine.chunks])
            st.write("**Documents:**")
            for source in sources:
                st.write(f"- {Path(source).name}")

            if st.button("Clear Knowledge Base", type="secondary"):
                st.session_state.rag_engine = None
                st.session_state.messages = []
                st.success("Knowledge base cleared!")
                st.rerun()
        else:
            st.info("No documents uploaded yet")

# Main chat interface
st.markdown('<p class="main-header">🤖 HR Onboarding Assistant</p>', unsafe_allow_html=True)
st.markdown("Ask me anything about company policies, benefits, leave, and more!")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant" and "metadata" in message:
            # Display category
            category = message["metadata"].get("category", "General")
            category_colors = {
                "Benefits": "#4CAF50",
                "Legal": "#f44336",
                "Internal Culture": "#9C27B0",
                "Leave": "#2196F3",
                "Remote Work": "#FF9800",
                "General": "#607D8B"
            }
            color = category_colors.get(category, "#607D8B")
            st.markdown(
                f'<span class="category-badge" style="background-color: {color}; color: white;">{category}</span>',
                unsafe_allow_html=True
            )

            # Display citations
            if "citations" in message["metadata"]:
                st.markdown("**📎 Citations:**")
                for i, citation in enumerate(message["metadata"]["citations"], 1):
                    st.markdown(
                        f'<div class="citation-box">'
                        f'<strong>Source {i}:</strong> {citation["source"]}<br>'
                        f'<em>"{citation["text"][:200]}..."</em>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

# Chat input
if prompt := st.chat_input("Ask a question about HR policies..."):
    if not st.session_state.rag_engine:
        st.error("⚠️ Please upload and process documents first using the Admin Panel!")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.rag_engine.query(prompt)

                    # Display answer
                    st.markdown(response["answer"])

                    # Display category
                    category = response["category"]
                    category_colors = {
                        "Benefits": "#4CAF50",
                        "Legal": "#f44336",
                        "Internal Culture": "#9C27B0",
                        "Leave": "#2196F3",
                        "Remote Work": "#FF9800",
                        "General": "#607D8B"
                    }
                    color = category_colors.get(category, "#607D8B")
                    st.markdown(
                        f'<span class="category-badge" style="background-color: {color}; color: white;">{category}</span>',
                        unsafe_allow_html=True
                    )

                    # Display citations
                    if response["citations"]:
                        st.markdown("**📎 Citations:**")
                        for i, citation in enumerate(response["citations"], 1):
                            st.markdown(
                                f'<div class="citation-box">'
                                f'<strong>Source {i}:</strong> {citation["source"]}<br>'
                                f'<em>"{citation["text"][:200]}..."</em>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

                    # Save to message history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["answer"],
                        "metadata": {
                            "category": category,
                            "citations": response["citations"]
                        }
                    })

                except Exception as e:
                    error_msg = f"I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.9rem;'>"
    "💡 Tip: Be specific in your questions for more accurate answers"
    "</div>",
    unsafe_allow_html=True
)