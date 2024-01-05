import streamlit as st
import streamlit.components.v1 as components
import json
import io
import random
import time
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'postgres_da_ai_agent'))
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'postgres_da_ai_agent'))
import numpy as np
from PIL import Image
from postgres_da_ai_agent.modules import rand
from postgres_da_ai_agent.agents.instruments import PostgresAgentInstruments
from postgres_da_ai_agent.prompt_handler import PromptHandler
from postgres_da_ai_agent.types import Innovation
import pandas as pd 

DB_URL = os.environ.get("DATABASE_URL")

st.title("Ask a question")

# Path to your Snowplow HTML file
snowplow_html_file = os.path.join(os.path.dirname(__file__), 'snowplow.html')

# Read the HTML file
with open(snowplow_html_file, 'r') as file:
    snowplow_html = file.read()
    # Replace the placeholder with the actual page name
    snowplow_html = snowplow_html.replace('{{pageName}}', 'Analytics App')

# Embed the Snowplow HTML in your Streamlit app
components.html(snowplow_html, height=0, width=0)

if 'download_triggered' not in st.session_state:
    st.session_state.download_triggered = False

def track_sidebar_interaction(interaction_type):
    components.html(f"<script>window.trackSidebarInteraction('{interaction_type}');</script>", height=0, width=0)

def track_tab_click():
    selected_tab = st.session_state.tab_key
    tab_name = ["Response", "SQL", "Innovation", "Artifact"][selected_tab]
    components.html(f"<script>window.trackTabClick('{tab_name}');</script>", height=0, width=0)

def prompt_response(raw_prompt):
    print(f"running prompt_response")
    # Logic to generate a response string and object based on the prompt
    response_string = ""
    response_object = None
            
    # prompt = f"Fulfill this database query: {raw_prompt}. "

    assistant_name = "Turbo4"

    session_id = rand.generate_session_id(assistant_name + raw_prompt)

    response = None
    with PostgresAgentInstruments(DB_URL, session_id) as (agent_instruments, db):
        with PromptHandler(raw_prompt, agent_instruments, db) as executor:
            response = executor.execute()
            response_string = response
            response_object = np.random.randn(30, 3) if random.randint(1, 10) % 2 else None
    return response_string, response_object

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

def display_assistant_response(full_response, the_thing):
    # Parse the full_response if it's a string (JSON)
    if isinstance(full_response, str):
        full_response = json.loads(full_response)

    # Create tabs for Response, SQL, Innovation, and Artifact
    tab1, tab2, tab3, tab4 = st.tabs(["Response", "SQL", "Innovation", "Artifact"])
    # Set the value of full_response to the Response tab
    with tab1:             
        # Check if full_response.result is a string and parse it as JSON                                             
        if isinstance(full_response.result, str):                                                                    
            result = json.loads(full_response.result)                                                           
        else:                                                                                                        
            result = full_response.result  
                                                                                         
        # Check if full_response.result is a valid data structure for st.dataframe
        if isinstance(result, (pd.DataFrame, pd.Series, pd.Index, np.ndarray, dict, list, set)):
            result_data = pd.DataFrame(result)  # Convert to DataFrame if not already one
            # Display as json
            with st.container():
                st.json(result, expanded=True)            
            # Display as DataFrame with new Streamlit 1.29.0 parameters
            with st.container():
                st.dataframe(result_data, use_container_width=True)
    # Set the value of SQL to the SQL tab
    with tab2:
        st.code(full_response.sql, language="sql", line_numbers=True)
    # Set the value of Innovation to the Innovation tab
    with tab3:
        for innovation in full_response.follow_up:
            st.code(innovation.insight,language=None)
            st.write(innovation.actionable_business_value)
            st.code(innovation.sql, language="sql")
            st.markdown("---")  # Divider between each innovation
    # Set the value of the_thing to the Artifact tab
    with tab4:
        # Create a pandas dataframe from full_response.result
        result_data = full_response.result
        df = pd.DataFrame(result_data)

        # Display various charts using the dataframe if the data format is suitable
        if isinstance(result_data, (pd.DataFrame, pd.Series, pd.Index, np.ndarray, dict, list)):
            st.area_chart(df)
            st.bar_chart(df)
            st.line_chart(df)
            st.scatter_chart(df)

            # For other chart types, we need to check if the data format is suitable
            # and potentially preprocess the data to fit the requirements of each chart type

            # st.pyplot(df)
            # Assuming result_data can be used to generate a matplotlib figure
            # fig, ax = plt.subplots()
            # ax.plot(...) # Replace with actual plotting code
            # st.pyplot(fig)

            # st.altair_chart(df)
            # Assuming result_data can be converted to an Altair chart
            # chart = alt.Chart(df).mark_line().encode(...)
            # st.altair_chart(chart, use_container_width=True)

            # st.vega_lite_chart(df)
            # Assuming result_data can be used with Vega-Lite specifications
            # vega_spec = {...} # Replace with actual Vega-Lite spec
            # st.vega_lite_chart(vega_spec, use_container_width=True)

            # st.plotly_chart(df)
            # Assuming result_data can be used to generate a Plotly figure
            # fig = px.line(df, ...) # Replace with actual Plotly code
            # st.plotly_chart(fig, use_container_width=True)

            # st.bokeh_chart(df)
            # Assuming result_data can be used to generate a Bokeh plot
            # plot = figure(...)
            # plot.line(...) # Replace with actual Bokeh plotting code
            # st.bokeh_chart(plot, use_container_width=True)

            # st.pydeck_chart(df)
            # Assuming result_data contains geospatial data for PyDeck
            # layer = pdk.Layer(...)
            # deck = pdk.Deck(layers=[layer], ...)
            # st.pydeck_chart(deck)

            # st.graphviz_chart(df)
            # Assuming result_data can be represented as a Graphviz graph
            # graph = graphviz.Graph(...)
            # st.graphviz_chart(graph)

            # st.map(df)
            # Assuming result_data contains latitude and longitude for mapping
            # st.map(df)

        # Note: For the above chart types, additional context or data processing might be required
        # to generate meaningful visualizations. The code assumes that result_data is in a format
        # that can be directly used or easily transformed for each chart type.
        # Display various charts using the dataframe

        # For st.pyplot, st.altair_chart, st.vega_lite_chart, st.plotly_chart, st.bokeh_chart, st.pydeck_chart, st.graphviz_chart, and st.map
        # we would need specific data structures or additional code to generate meaningful visualizations.
        # These functions are not directly compatible with a generic dataframe without additional context or data processing.
        # Therefore, we will not include them here as it would require a deeper understanding of the data and the desired visualizations.
        # If you have specific requirements for these charts, please provide further details or examples of the data and the expected output.


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            display_assistant_response(message["content"], message.get("artifact"))
        else:
            st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Track the user prompt submission using Snowplow
    # components.html(f"<script>window.trackUserPromptSubmission({json.dumps(prompt)});</script>", height=0, width=0)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            # Generate assistant response and potentially a numpy array
            full_response, the_thing = prompt_response(prompt)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response, "artifact": the_thing})

            # Display assistant response in chat message container
            display_assistant_response(full_response, the_thing)



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
    # components.html(f"<script>window.trackSidebarInteraction('Configure Assistant');</script>", height=0, width=0)

st.sidebar.markdown("---")
st.sidebar.markdown("<p align='center'>Made by the AI Team</p>", unsafe_allow_html=True)


# track_sidebar_interaction('sidebar_loaded')
# Track tab clicks using JavaScript
tab_click_script = """
<script>
const tabNames = ["Response", "SQL", "Innovation", "Artifact"];
const tabs = document.getElementsByClassName('st-Tab');
for (let i = 0; i < tabs.length; i++) {
    tabs[i].addEventListener('click', function() {
        window.trackTabClick(tabNames[i]);
    });
}
</script>
"""
# components.html(tab_click_script, height=0, width=0)
