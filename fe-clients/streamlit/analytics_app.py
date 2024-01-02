import streamlit as st
import io
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

    # Generate assistant response and potentially a numpy array
    full_response, the_thing = chat_response(prompt)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            # Create tabs for Response and Artifact
            tab1, tab2 = st.tabs(["Response", "Artifact"])
            # Set the value of full_response to the Response tab
            with tab1:
                full_response, the_thing = chat_response(prompt)
                st.markdown(full_response)
            # Set the value of the_thing to the Artifact tab
            with tab2:
                if the_thing is not None:
                    st.bar_chart(the_thing)
                    img = Image.fromarray(the_thing, 'RGB')
                    # Convert the numpy array to a file and create a download button
                    the_thing_bytes = io.BytesIO()
                    np.save(the_thing_bytes, the_thing, allow_pickle=False)
                    the_thing_bytes.seek(0)
                    # Use Streamlit's session state to prevent rerun from affecting the chat history
                    if 'download_triggered' not in st.session_state:
                        st.session_state.download_triggered = False
            with tab2:
                if the_thing is not None:
                    st.bar_chart(the_thing)
                    download_button = st.download_button(
                        label="Download the_thing",
                        data=the_thing_bytes,
                        file_name="the_thing.npy",
                        mime="application/octet-stream",
                        on_click=lambda: setattr(st.session_state, 'download_triggered', True),
                        key="download_the_thing_tab2"
                    )
                    if st.session_state.download_triggered:
                        # Reset the flag to prevent the download action from affecting the chat history
                        st.session_state.download_triggered = False
                        st.bar_chart(the_thing)
                if st.session_state.download_triggered:
                    st.session_state.download_triggered = False
                    st.bar_chart(the_thing)
            if the_thing is not None:
                st.bar_chart(the_thing)
                img = Image.fromarray(the_thing, 'RGB')
                # img.show()
                # Convert the numpy array to a file and create a download button
                the_thing_bytes = io.BytesIO()
                np.save(the_thing_bytes, the_thing, allow_pickle=False)
                the_thing_bytes.seek(0)
                # Use Streamlit's session state to prevent rerun from affecting the chat history
                if 'download_triggered' not in st.session_state:
                    st.session_state.download_triggered = False
                download_button = st.download_button(
                    label="Download the_thing",
                    data=the_thing_bytes,
                    file_name="the_thing.npy",
                    mime="application/octet-stream",
                    on_click=lambda: setattr(st.session_state, 'download_triggered', True),
                    key="download_the_thing_outside"
                )
                if st.session_state.download_triggered:
                    # Reset the flag to prevent the download action from affecting the chat history
                    st.session_state.download_triggered = False
                    st.bar_chart(the_thing)
            
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





