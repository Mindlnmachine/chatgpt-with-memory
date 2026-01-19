# 🧠 Local Chatbot with Personalized Memory (Gemma 3:1b)

# 🧠 Local Chatbot with Personalized Memory (Configurable: Gemma, LLaMA, Phi-3)

Repository: https://github.com/Mindlnmachine/chatgpt-with-memory

This Streamlit application provides a fully local chatbot experience, leveraging local LLMs via Ollama (e.g., Gemma 3:1b, LLaMA 3, Phi-3) and personalized memory management for each user. All core components, including the large language model (LLM), embedding model, and vector store, operate entirely on your local machine, eliminating the need for external API keys.

## ✨ Features

*   **Fully Local Operation:** No external API dependencies or cloud services required.
*   **Powered by Ollama:** Integrates with the local Ollama server for LLM inference.
*   **Personalized Memory:** Each user benefits from a dedicated memory space for storing conversation history.
*   **Local Embeddings:** Generates embeddings using Ollama's `nomic-embed-text:latest` model.
*   **Vector Storage:** Utilizes Qdrant as the local vector database for efficient memory retrieval.

## 🚀 How to Get Started

Follow these steps to set up and run the application on your local machine.

### Prerequisites

Before you begin, ensure you have the following installed and running:

1.  **Git:** For cloning the repository.
2.  **Python 3.8+:** For running the Streamlit application.
3.  **Docker Desktop:** Essential for running the Qdrant vector database. [Download Docker Desktop](https://docs.docker.com/desktop/install/windows-install/).
4.  **Ollama:** For serving the local LLM and embedding models. [Download Ollama](https://ollama.com/download).

### Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Mindlnmachine/chatgpt-with-memory.git
    cd chatgpt-with-memory
    ```

2.  **Create and Activate a Python Virtual Environment (Recommended):**
    ```bash
    python -m venv .venv
    .\.venv\Scripts\Activate # On Windows PowerShell
    # source .venv/bin/activate # On Linux/macOS Bash/Zsh
    ```

3.  **Install Required Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install and Start Qdrant Vector Database:**
    Ensure Docker Desktop is running before executing these commands.
    ```bash
    docker pull qdrant/qdrant
    docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
    ```
    *To verify Qdrant is running:*
    ```bash
    docker ps -a
    curl http://localhost:6333/api/v1/collections
    ```

5.  **Pull Ollama Models:**
    Download the required LLM and embedding models using Ollama.
    ```bash
    ollama pull gemma3:1b
    # or
    ollama pull llama3:8b
    ollama pull phi3:medium
    
    ollama pull nomic-embed-text:latest
    ```
    *To verify Ollama models are available:*
    ```bash
    curl http://localhost:11434/api/tags
    ```

6.  **Run the Streamlit Application:**
    ```bash
    streamlit run local_chatgpt_memory.py
    ```
    Your browser should automatically open the Streamlit application.

## ⚠️ Troubleshooting Common Issues

*   **`ConnectionRefusedError` or `WinError 10061`:** This usually means either Ollama (port 11434) or Qdrant (port 6333) is not running or is blocked by a firewall.
    *   **For Qdrant:** Ensure Docker Desktop is running, and the `qdrant` container is active (`docker ps -a`).
    *   **For Ollama:** Ensure the Ollama Desktop application is running in your system tray.
    *   **Firewall:** Temporarily disable your firewall or add exceptions for ports 11434 and 6333.
*   **`model requires more system memory`:** The selected LLM might be too large for your system's available RAM.
    *   Try a smaller model (e.g., `phi3:medium`) by choosing it in the sidebar or updating the `model` in `config["llm"]["config"]` within `local_chatgpt_memory.py`, then run `ollama pull <model_name>`.
    *   Consider increasing your system's available RAM or using a remote LLM provider.

*   **`AttributeError: 'QdrantClient' object has no attribute 'search'`:** This indicates a version incompatibility between `mem0ai` and `qdrant-client`. Run `pip install -r requirements.txt --upgrade --no-cache-dir` to ensure the latest compatible versions are installed.....
