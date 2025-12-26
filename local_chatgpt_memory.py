import streamlit as st
import requests
from mem0 import Memory
from litellm import completion
    
# --- Helper Functions ---

def check_ollama_status(url):
    """Checks if the Ollama server is running."""
    try:
        response = requests.get(f"{url}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def init_memory(ollama_url, llm_model):
    """Initializes the Mem0 object with current configuration."""
    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "local-chatgpt-memory",
                "host": "localhost",
                "port": 6333,
                "embedding_model_dims": 768,
            },
        },
        "llm": {
            "provider": "ollama",
            "config": {
                "model": llm_model, 
                "temperature": 0.1, # Slightly higher temperature for better variety
                "max_tokens": 8000,
                "ollama_base_url": ollama_url,
            },
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": "nomic-embed-text:latest", # Keeping the embedder consistent
                "ollama_base_url": ollama_url,
            },
        },
        "version": "v1.1"
    }
    
    try:
        m = Memory.from_config(config)
        return m
    except Exception as e:
        st.error(f"Failed to initialize Memory: {e}")
        return None

# --- Streamlit App ---

st.set_page_config(layout="wide")
st.title("Local LLM Chat with Personalized Memory 🧠")
st.caption("Powered by Streamlit, Mem0, and Ollama/LiteLLM.")

# Initialize session state for chat history and previous user ID
if "messages" not in st.session_state:
    st.session_state.messages = []
if "previous_user_id" not in st.session_state:
    st.session_state.previous_user_id = None
if "memory_instance" not in st.session_state:
    st.session_state.memory_instance = None


# --- Sidebar Configuration and Memory Management ---
with st.sidebar:
    st.title("⚙️ Configuration & User Settings")
    
    # 1. User Authentication
    user_id = st.text_input("Enter your **Username** (for personalized memory)", key="user_id_input", value="User123")
    
    if user_id != st.session_state.previous_user_id:
        st.session_state.messages = []  # Clear chat history on user switch
        st.session_state.previous_user_id = user_id
        st.session_state.memory_instance = None # Force re-initialization
        st.rerun()
        
    if user_id:
        st.success(f"Logged in as: **{user_id}**")
        
    st.markdown("---")
    
    # 2. Ollama & LLM Settings (Now Configurable)
    st.header("Ollama Connection")
    ollama_url = st.text_input("Ollama Base URL", value="http://localhost:11434")
    llm_model = st.selectbox("LLM Model (installed in Ollama)", ("gemma3:1b", "llama3:8b", "phi3:medium"))

    # 3. Initialize Memory
    if st.button("Connect & Initialize Chat"):
        if check_ollama_status(ollama_url):
            st.session_state.memory_instance = init_memory(ollama_url, llm_model)
            if st.session_state.memory_instance:
                st.success(f"Ollama connected. LLM: **{llm_model}** is ready!")
        else:
            st.error(f"Cannot connect to Ollama at {ollama_url}. Please ensure Ollama is running.")

    # Get memory instance from session state
    m = st.session_state.memory_instance

    if m and user_id:
        st.markdown("---")
        st.header("🧠 Memory Operations")
        
        # View Memory Button
        if st.button("View My Memory"):
            memories = m.get_all(user_id=user_id)
            if memories and "results" in memories:
                with st.expander(f"All {len(memories['results'])} Memories for {user_id}"):
                    for i, memory in enumerate(memories["results"]):
                        if "memory" in memory:
                            st.write(f"**{i+1}.** {memory['memory']}")
            else:
                st.info("No memories found yet for this user.")

        # Clear Memory Button (Suggestion implemented)
        if st.button("🗑️ Clear All My Memory", help="This will delete ALL past conversation context for this user."):
            try:
                m.delete(user_id=user_id)
                st.session_state.messages = [] # Also clear chat history on memory clear
                st.success(f"All memories for **{user_id}** have been cleared!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error clearing memory: {e}")

# --- Main Chat Interface ---

if not user_id:
    st.info("👈 Please enter your **Username** in the sidebar to begin.")
elif not st.session_state.memory_instance:
    st.warning("👈 Please enter the settings and click **Connect & Initialize Chat** to start.")
else:
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("What is your message?"):
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Start Memory/Response Logic
        try:
            # 1. Add to memory *before* retrieval (to include the current turn)
            m.add(prompt, user_id=user_id)
            
            # 2. Get CONTEXT from memory using SEMANTIC SEARCH (Suggestion implemented)
            # Retrieve the top 5 most relevant memories based on the current prompt
            memories = m.search(query=prompt, user_id=user_id, limit=5)
            context = ""
            if memories and "results" in memories:
                st.caption(f"Context from **{len(memories['results'])}** relevant memories used for response.")
                for memory in memories["results"]:
                    if "memory" in memory:
                        context += f"- {memory['memory']}\n"
            else:
                st.caption("No relevant context found in memory.")

            # 3. Generate assistant response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Enhanced System Prompt
                system_prompt = (
                    "You are a helpful, friendly, and concise AI assistant. "
                    "You have access to past conversations and user facts. "
                    "Use the 'Context' provided to give personalized responses when relevant, but do not repeat the context verbatim."
                )
                
                # Stream the response
                response = completion(
                    model=f"ollama/{llm_model}", # Use the configurable model
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Context from previous conversations with {user_id}: {context}\nCurrent message: {prompt}"}
                    ],
                    api_base=ollama_url, # Use the configurable URL
                    stream=True,
                    max_tokens=2048 # Adjust max tokens for safety
                )
                
                # Process streaming response
                for chunk in response:
                    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.get('content', '')
                        if content:
                            full_response += content
                            message_placeholder.markdown(full_response + "▌")
                
                # Final update
                message_placeholder.markdown(full_response)

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            if 'Connection refused' in error_message or 'Failed to establish a new connection' in error_message:
                 st.error("🚨 **Connection Error:** Could not connect to Ollama. Please check if the service is running at the configured URL.")
            elif 'Model not found' in error_message:
                st.error(f"🚨 **LLM Model Error:** The model **{llm_model}** was not found in Ollama. Please ensure it is installed (`ollama pull {llm_model}`).")
            else:
                st.error(f"🚨 **Error generating response:** {str(e)}")
            
            full_response = "I apologize, but I encountered a critical error. Please check the sidebar configurations and logs."
            with st.chat_message("assistant"):
                 st.markdown(full_response)
        
        # 4. Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        # 5. Add response to memory (for a more complete conversational history)
        if full_response != "I apologize, but I encountered a critical error. Please check the sidebar configurations and logs.":
            m.add(f"Assistant: {full_response}", user_id=user_id)