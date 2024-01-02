import streamlit as st

st.set_page_config(page_title='AI Data Assistant', layout='wide', initial_sidebar_state='expanded')

st.title('AI assistant')
st.header('Data analysis')
st.subheader('Solution')
st.write('Hallo, I\'m your AI Data assistant here to help you with Marketing queries, how can I help you?')
st.sidebar.write("This assistant helps to navigate and answer questions you might have of your analytics data\n\n Simply type your question in the prompt and the assistant will convert it into the necessary sql and interrogate your data to give an answer as well as the steps it took to get to the answer.")
