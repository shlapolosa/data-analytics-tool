import streamlit as st

import streamlit.components.v1 as components
import os

st.set_page_config(page_title='AI Data Assistant', layout='wide', initial_sidebar_state='auto')

st.title('AI assistant')
st.header('Data analysis')
st.subheader('Solution')
st.write('Hallo, I\'m your AI Data assistant here to help you with Marketing queries, how can I help you?')

# Path to your Snowplow HTML file
snowplow_html_file = os.path.join(os.path.dirname(__file__), '..', 'snowplow.html')

# Read the HTML file
with open(snowplow_html_file, 'r') as file:
    snowplow_html = file.read()

# Embed the Snowplow HTML in your Streamlit app
components.html(snowplow_html, height=0, width=0)

components.html("""
<script type="text/javascript">
    window.snowplow('trackPageView', 'Marketing Insights');
</script>
""", height=0, width=0)
