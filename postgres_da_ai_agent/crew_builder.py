from crewai import Agent, Task, Crew, Process
from langchain.tools import tool
from postgres_da_ai_agent.agents.instruments import PostgresAgentInstruments
from postgres_da_ai_agent.modules.embeddings import DatabaseEmbedder
from textwrap import dedent
import json

POSTGRES_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"

class CrewBuilder:
    def __init__(self, agent_instruments: PostgresAgentInstruments, prompt: str):
        self.agents = []
        self.tasks = []
        self.crew = None
        self.process = None
        self.agent_instruments = agent_instruments  # Property of type PostgresAgentInstruments
        self.prompt = prompt  # The prompt for the CrewBuilder

    def create_agents(self):
        # Define the agents with roles and goals
        self.data_engineer = Agent(
            role='Data Engineer',
            goal='Prepare and transform data for analytical or operational uses',
            backstory="""You are a meticulous Data Engineer responsible for building and maintaining the data architecture of the company. Your expertise in data modeling, ETL processes, and data warehousing is unparalleled.""",
            verbose=True,
            allow_delegation=False
        )

        self.data_analyst = Agent(
            role='Data Analyst',
            goal='Analyze data to help inform business decisions',
            backstory="""As a Data Analyst, you have a sharp eye for detail and a passion for deciphering data puzzles. You excel at turning data into meaningful insights and actionable recommendations.""",
            tools=[
                self.run_sql,
                self.get_table_definitions
            ],
            verbose=True,
            allow_delegation=False
        )

        self.scrum_master = Agent(
            role='Scrum Master',
            goal="Facilitate the team's Agile practices and processes",
            backstory="""You are the Scrum Master, the team's coach, and facilitator. Your primary goal is to ensure that the team adheres to Agile practices and works efficiently towards their goals.""",
            verbose=True,
            allow_delegation=False
        )

        self.data_visualisation_expert = Agent(
            role='Data Visualization Expert',
            goal='Recommend the best way to visualize the data and prepare it for the chosen visualization method.',
            backstory="""As a Data Visualization Expert, you have an eye for design and a knack for presenting data in the most insightful and accessible ways. You're familiar with a variety of visualization tools and techniques.""",
            tools=[
                self.recommend_visualization
            ],
            verbose=True,
            allow_delegation=False
        )


        self.data_innovator = Agent(
            role='Data Innovator',
            goal="You're a data innovator. You analyze SQL databases table structure and generate 3 novel insights for your team to reflect on and query. Format your insights in JSON format.",
            backstory="""As a Data Innovator, you have a unique ability to see beyond the data. You connect the dots between disparate pieces of information to generate new, valuable insights that can transform the way your team operates.""",
            verbose=True,
            allow_delegation=False
        )

        # Add the agents to the list
        self.agents.extend([
            self.data_engineer,
            self.data_analyst,
            self.scrum_master,
            self.data_visualisation_expert,
            self.data_innovator
        ])

        return self


    def create_assess_nlq_task(self):
        # Task for the Scrum Master to assess if the prompt is a Natural Language Query (NLQ)
        self.assess_nlq_task = Task(
            description="""
            Is the following block of text a SQL Natural Language Query (NLQ)? Please rank from 1 to 5.
            """,
            agent=self.scrum_master
        )
        self.tasks.append(self.assess_nlq_task)
        return self

    def create_generate_sql_task(self, prompt):
        # Task for the Data Engineer to generate initial SQL
        self.generate_sql_task = Task(
            description=dedent(f"""
                               Generate a SQL query to answer the following question: {prompt}.
                               This query will run on a database whose schema is represented by the {POSTGRES_TABLE_DEFINITIONS_CAP_REF}.
                               When generating the SQL beware that the tables are in the 'atomic' schema.
                               Make sure that the SQL you generate is correct for the {POSTGRES_TABLE_DEFINITIONS_CAP_REF} provided.
                               Respond with only exactly this format, DO NOT alter the format:
                               ```
                               sql_input:\n\n raw generated sql\n\n
                               {POSTGRES_TABLE_DEFINITIONS_CAP_REF}:\n\n as per the input {POSTGRES_TABLE_DEFINITIONS_CAP_REF} exactly\n\n
                               ```
                               """),
            agent=self.data_engineer
        )
        self.tasks.append(self.generate_sql_task)
        return self

    def create_execute_sql_task(self):
        # Task for the Data Analyst to execute the SQL
        self.execute_sql_task = Task(
            description=dedent(f"""
                               Senior Data Analyst: Execute the SQL query using the run_sql function, which returns the raw_response. Respond in the following strict format only:
                                ```
                                sql_input:
                                [Insert your SQL query here, replacing {{sql_input}}]

                                raw_response:
                                [Insert the raw response from the SQL query here as a json object, replacing raw_response]

                                Database Schema:
                                [Insert the PostgreSQL table definitions here, replacing {POSTGRES_TABLE_DEFINITIONS_CAP_REF}]
                                ```

                                Example Response:
                                ```
                                sql_input:
                                SELECT event, COUNT(*) AS frequency FROM atomic.events GROUP BY event ORDER BY frequency DESC;

                                raw_response:
                                [
                                    {
                                        "event": "page_view",
                                        "frequency": 160
                                    },
                                    {
                                        "event": "page_ping",
                                        "frequency": 39
                                    },
                                    {
                                        "event": "unstruct",
                                        "frequency": 9
                                    },
                                    {
                                        "event": "struct",
                                        "frequency": 1
                                    }
                                ]

                                Database Schema:

                                    CREATE TABLE atomic.events (
                                    app_id character varying(255),
                                    platform character varying(255),
                                    true_tstamp timestamp without time zone,
                                    ...
                                    );
                                ```           
                               """),
            agent=self.data_analyst
        )
        self.tasks.append(self.execute_sql_task)
        return self

    def create_recommend_visualization_task(self):
        # Task for the Data Visualization Expert to recommend visualization method
        self.recommend_visualization_task = Task(
            description=dedent(f"""
                               Recommend the best way to visualize the raw_response. Prepare the data for the chosen visualization method as the prepared_data. Provide only one option. Respond in this strict format only:
                               ```
                                format:
                                [Insert the best visualization method here, replacing visualization_method]

                                result:
                                [Insert the prepared data formatted for the chosen visualization method here, replacing prepared_data]

                                sql_input:
                                [Insert the SQL input query here, replacing sql_input]
                                ```

                                Example Response:
                                ```
                                format:
                                Bar Chart

                                result:
                                Prepared data in format suitable for a bar chart (e.g., categories and values)

                                sql_input:
                                SELECT category, COUNT(*) FROM sales_data GROUP BY category
                               ```
                               """),
            agent=self.data_visualisation_expert
        )
        self.tasks.append(self.recommend_visualization_task)
        return self

    def create_response(self):
        # Task for the Data Visualization Expert to recommend visualization method
        self.response = Task(
            description=dedent("""
                               Summarize all outputs after your team's review. Return the summary in the following JSON format:

                                ```
                                {
                                    "result": {
                                        "prepared_data": "Place the summarized result here",
                                        "display_format": "Specify the format used for summary"
                                    },
                                    "sql": "Insert the SQL input query here"
                                }
                                ```
                               """),
            agent=self.scrum_master,
        )
        self.tasks.append(self.response)
        return self
    
    def create_innovation_task(self, prompt):
        # Task for the Data Engineer to analyze SQL database table structure and generate insights
        self.innovation_task = Task(
            description=dedent("""
                                Analyze SQL database table structures and generate 3 novel insights based on the original prompt: '{prompt}'. 
                                Each insight should be accompanied by its actionable business value and a new SQL query. Respond with the following JSON structure:

                                ```
                                [
                                    {
                                        "insight": "First insight description here",
                                        "actionable_business_value": "Description of the first insight's actionable business value",
                                        "sql": "SQL query related to the first insight"
                                    },
                                    {
                                        "insight": "Second insight description here",
                                        "actionable_business_value": "Description of the second insight's actionable business value",
                                        "sql": "SQL query related to the second insight"
                                    },
                                    {
                                        "insight": "Third insight description here",
                                        "actionable_business_value": "Description of the third insight's actionable business value",
                                        "sql": "SQL query related to the third insight"
                                    }
                                ]
                                ```
                               """).format(prompt),
            agent=self.data_engineer
        )
        self.tasks.append(self.innovation_task)
        return self

    def create_crew(self):
        # Instantiate your crew with a sequential process
        self.crew = Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=2,  # Crew verbose mode
            process=Process.sequential  # Sequential process
        )
        return self

    def create_get_table_definitions_task(self, prompt):
        # Task for the Data Analyst to get the table definitions
        self.get_table_definitions_task = Task(
            description=dedent(f"""
                               Retrieve the table definitions relevant to the current prompt. given the following prompt: {prompt}. 
                               return in exactly the following format: 
                                ```
                               {POSTGRES_TABLE_DEFINITIONS_CAP_REF}:\n\n as per the tabel definition response from the tools exactly \n\n
                               ```
                               """),
            agent=self.data_analyst
        )
        self.tasks.append(self.get_table_definitions_task)
        return self

    def execute(self):
        response = self.crew.kickoff() if self.crew else None
        self.tasks = []
        return response
  
    
    
    @tool("Executes a given SQL query string against the database.")
    def run_sql(sql: str) -> str:
        """
        Executes a given SQL query string against the database and returns the results in JSON format.

        Args:
            sql (str): The SQL query string to be executed.

        Returns:
            str: A JSON string representing the query results.
        """
        print(f"SQL query to be ran: {sql}")
        from postgres_da_ai_agent.modules.db import PostgresManager
        from dotenv import load_dotenv
        load_dotenv()
        import os

        def datetime_handler(obj):
            """
            Handle datetime objects when serializing to JSON.
            """
            from datetime import datetime

            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)  # or just return the object unchanged, or another default value
        
        db_manager = PostgresManager()
        db_manager.connect_with_url(os.environ['DATABASE_URL'])
        db_manager.cur.execute(sql)
        columns = [desc[0] for desc in db_manager.cur.description]
        res = db_manager.cur.fetchall()

        list_of_dicts = [dict(zip(columns, row)) for row in res]

        json_result = json.dumps(list_of_dicts, indent=4, default=datetime_handler)

        return json_result

    @tool("Retrieves similar table definitions for a given prompt.")
    def get_table_definitions(prompt) -> str:
        """
        Retrieves table definitions that are similar to the current prompt.

        This method uses the DatabaseEmbedder to find table definitions that are likely
        to be relevant to the prompt provided to the CrewBuilder.

        Returns:
            str: A string containing the similar table definitions.
        """
        from postgres_da_ai_agent.modules.db import PostgresManager
        from dotenv import load_dotenv
        load_dotenv()
        import os

        db_manager = PostgresManager()
        db_manager.connect_with_url(os.environ['DATABASE_URL'])
        database_embedder = DatabaseEmbedder(db_manager)
        print(f" the prompt in get_table_definitions is: {prompt}")

        table_definitions = database_embedder.get_similar_table_defs_for_prompt(prompt)
        return table_definitions

    @tool("Recommends the best way to visualize the data and prepares it for the chosen visualization method.")
    def recommend_visualization(execution_results):
        """
        Recommends the best way to visualize the data and prepares it for the chosen visualization method.

        This method analyzes the execution results and determines the best visualization method,
        as well as prepares the data for visualization.

        Args:
            execution_results: The results of the SQL query execution.

        Returns:
            tuple: A tuple containing the recommended visualization method and the prepared data.
        """
        import pandas as pd

        # This method should contain the logic to analyze the execution_results
        # and determine the best visualization method, as well as prepare the data.
        # The following is a placeholder for the actual implementation.

        # Placeholder logic for visualization recommendation
        if isinstance(execution_results, list) and all(isinstance(row, dict) for row in execution_results):
            # Assuming execution_results is a list of dictionaries representing rows of data
            df = pd.DataFrame(execution_results)
            columns = df.columns
            if "time" in columns or "date" in columns:
                visualization_method = "line_chart"
                prepared_data = df.set_index("time" if "time" in columns else "date")
            elif "category" in columns and "value" in columns:
                visualization_method = "bar_chart"
                prepared_data = df.pivot(index='category', values='value', columns=df.columns.difference(['category', 'value']))
            elif len(columns) >= 2:
                visualization_method = "scatter_chart"
                prepared_data = df
            else:
                visualization_method = "table"
                prepared_data = df
        else:
            visualization_method = "text"
            prepared_data = str(execution_results)

        return visualization_method, prepared_data.to_dict('list') if isinstance(prepared_data, pd.DataFrame) else prepared_data    
    
    def get_db_manager():
        """
        Creates an instance of PostgresManager and connects to the database using the DATABASE_URL from the environment.

        Returns:
            PostgresManager: An instance of the PostgresManager connected to the database.
        """
        from postgres_da_ai_agent.modules.db import PostgresManager
        from dotenv import load_dotenv
        load_dotenv()
        import os

        db_manager = PostgresManager()
        db_manager.connect_with_url(os.environ['DATABASE_URL'])
        return db_manager
