import streamlit as st

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

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.status("Please type your message and press enter...")
user_input = st.chat_input("Type your message here...", key="chat_input")
if user_input:
    st.session_state.chat_history.append({'message': user_input, 'is_user': True})
    # Here you would typically handle the user input, call the assistant API or process the input locally,
    # and then update the chat history with the assistant's response.
    # For example, let's simulate a response:
    st.session_state.chat_history.append({'message': "This is a simulated response.", 'is_user': False})

for chat in st.session_state.chat_history:
    if chat['is_user']:
        st.chat_message(chat['message'], is_user=True)
    else:
        st.chat_message(chat['message'], is_user=False)

if st.sidebar.button('Configure Assistant'):
    assistant_name = st.sidebar.text_input('Name')
    uploaded_file = st.sidebar.file_uploader(
        'Knowledge',
        type=['pdf', 'csv', 'txt']
    )
st.sidebar.markdown("---")
st.sidebar.markdown("<p align='center'>Made by the AI Team</p>", unsafe_allow_html=True)





