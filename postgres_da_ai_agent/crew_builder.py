from crewai import Agent, Task, Crew, Process
from langchain.tools import tool
from postgres_da_ai_agent.agents.instruments import PostgresAgentInstruments
from postgres_da_ai_agent.modules.embeddings import DatabaseEmbedder
from textwrap import dedent
import json

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

    def create_generate_sql_task(self):
        # Task for the Data Engineer to generate initial SQL
        self.generate_sql_task = Task(
            description="Generate the initial SQL based on the requirements provided. Only generate the SQL if you have sufficient TABLE_DEFINITIONS to work with. When generating the SQL beware that the tables are in the 'atomic' schema.",
            agent=self.data_engineer
        )
        self.tasks.append(self.generate_sql_task)
        return self

    def create_execute_sql_task(self):
        # Task for the Data Analyst to execute the SQL
        self.execute_sql_task = Task(
            description="Execute the SQL provided by the Data Engineer.",
            agent=self.data_analyst
        )
        self.tasks.append(self.execute_sql_task)
        return self

    def create_recommend_visualization_task(self):
        # Task for the Data Visualization Expert to recommend visualization method
        self.recommend_visualization_task = Task(
            description="Recommend the best way to visualize the data and prepare it for the chosen visualization method.",
            agent=self.data_visualisation_expert
        )
        self.tasks.append(self.recommend_visualization_task)
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
            description=dedent(f"""Retrieve the table definitions relevant to the current prompt. given the following prompt: {prompt}"""),
            agent=self.data_analyst
        )
        self.tasks.append(self.get_table_definitions_task)
        return self

    def execute(self):
        self.crew.kickoff() if self.crew else None
        return self
    
    
    @tool("Executes a given SQL query string against the database.")
    def run_sql(self, sql: str) -> str:
        """
        Executes a given SQL query string against the database and returns the results in JSON format.

        Args:
            sql (str): The SQL query string to be executed.

        Returns:
            str: A JSON string representing the query results.
        """
        self.agent_instruments.db.cur.execute(sql)
        columns = [desc[0] for desc in self.agent_instruments.db.cur.description]
        res = self.agent_instruments.db.cur.fetchall()

        list_of_dicts = [dict(zip(columns, row)) for row in res]

        json_result = json.dumps(list_of_dicts, indent=4, default=self.agent_instruments.datetime_handler)

        return json_result

    @tool("Retrieves similar table definitions for a given prompt.")
    def get_table_definitions(self) -> str:
        """
        Retrieves table definitions that are similar to the current prompt.

        This method uses the DatabaseEmbedder to find table definitions that are likely
        to be relevant to the prompt provided to the CrewBuilder.

        Returns:
            str: A string containing the similar table definitions.
        """
        from dotenv import load_dotenv
        load_dotenv()
        import os

        db_manager = PostgresManager()
        db_manager.connect_with_url(os.environ['DATABASE_URL'])
        database_embedder = DatabaseEmbedder(db_manager)
        table_definitions = database_embedder.get_similar_table_defs_for_prompt(self.prompt)
        return table_definitions

    @tool("Recommends the best way to visualize the data and prepares it for the chosen visualization method.")
    def recommend_visualization(self, execution_results):
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