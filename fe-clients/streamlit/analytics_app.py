import streamlit as st

st.set_page_config(page_title='AI Data Assistant', layout='wide', initial_sidebar_state='auto')

st.title('AI assistant')
st.header('Data analysis')
st.subheader('Solution')
st.write('Hallo, I\'m your AI Data assistant here to help you with Marketing queries, how can I help you?')
st.sidebar.markdown('**Marketing insights and Reporting**')
st.sidebar.markdown("This assistant helps to navigate and answer questions you might have of your analytics data\n\n Simply type your question in the prompt and the assistant will convert it into the necessary sql and interrogate your data to give an answer as well as the steps it took to get to the answer.\nYou can also select whether you want to use openAI api or run using local models by selecting the Run mode ✅")
run_mode_expander = st.sidebar.expander("Run mode")
run_mode = run_mode_expander.radio(
    label="Choose the run mode:",
    options=("AssistantAPI", "Autogen", "CrewAI")
)
st.sidebar.markdown("---")
st.sidebar.markdown("<p align='center'>Made by the AI Team</p>", unsafe_allow_html=True)
st.button('Let\'s get started')
if st.sidebar.button('Configure Assistant'):
    assistant_name = st.sidebar.text_input('Name')
    uploaded_file = st.sidebar.file_uploader(
        'Knowledge',
        type=['pdf', 'csv', 'txt']
    )

