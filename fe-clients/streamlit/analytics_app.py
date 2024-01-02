import streamlit as st
import random
import time
import numpy as np
from PIL import Image

st.title("Ask a question")

def chat_response(prompt):
    full_response = ""
    assistant_response = random.choice(
            [
                "Hello there! How can I assist you today?",
                "Hi, human! Is there anything I can help you with?",
                "Do you need help?",
            ]
        )
    # Simulate stream of response with milliseconds delay
    for chunk in assistant_response.split():
        full_response += chunk + " "
        time.sleep(0.3)
    the_thing = np.random.randn(30, 3) if random.randint(1, 10) % 2 else None
    return full_response, the_thing


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            message_placeholder = st.empty()
            full_response,the_thing = chat_response(prompt)
            message_placeholder.markdown(full_response)
            if the_thing is not None:
                st.bar_chart(the_thing)
                img = Image.fromarray(the_thing, 'RGB')
                img.show()
            
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})


st.sidebar.markdown('**Marketing insights and Reporting**')
st.sidebar.markdown("This assistant helps to navigate and answer questions you might have of your analytics data\n\n Simply type your question in the prompt and the assistant will convert it into the necessary sql and interrogate your data to give an answer as well as the steps it took to get to the answer.\nYou can also select whether you want to use openAI api or run using local models by selecting the Run mode ✅")
run_mode_expander = st.sidebar.expander("Run mode")
run_mode = run_mode_expander.radio(
    label="Choose the run mode:",
    options=("AssistantAPI", "Autogen", "CrewAI")
)
with st.container() as border1:
    roles = {
        "AssistantAPI": ["Turbo4", "Informational"],
        "Autogen": ["Admin", "Engineer", "Data Analyst", "Scrum Master", "Insights Reporter"],
        "CrewAI": ["Team"]
    }

    selected_roles = roles.get(run_mode, [])
    for role in selected_roles:
        st.sidebar.markdown(f"<p align='center'>{role}</p>", unsafe_allow_html=True)

if st.sidebar.button('Configure Assistant'):
    assistant_name = st.sidebar.text_input('Name')
    uploaded_file = st.sidebar.file_uploader(
        'Knowledge',
        type=['pdf', 'csv', 'txt']
    )
st.sidebar.markdown("---")
st.sidebar.markdown("<p align='center'>Made by the AI Team</p>", unsafe_allow_html=True)





