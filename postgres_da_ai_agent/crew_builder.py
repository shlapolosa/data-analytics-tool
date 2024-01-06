from crewai import Agent, Task, Crew, Process
from langchain.tools import tool
from postgres_da_ai_agent.agents.instruments import PostgresAgentInstruments
import json

class CrewBuilder:
    def __init__(self):
        self.agents = []
        self.tasks = []
        self.crew = None
        self.process = None
        self.agent_instruments = PostgresAgentInstruments()  # Property of type PostgresAgentInstruments

    def create_agents(self):
        # Define the agents with roles and goals
        self.data_engineer = Agent(
            role='Data Engineer',
            goal='Prepare and transform data for analytical or operational uses',
            backstory="""You are a meticulous Data Engineer responsible for building and maintaining the data architecture of the company. Your expertise in data modeling, ETL processes, and data warehousing is unparalleled.""",
            verbose=True,
            allow_delegation=True
        )

        self.data_analyst = Agent(
            role='Data Analyst',
            goal='Analyze data to help inform business decisions',
            backstory="""As a Data Analyst, you have a sharp eye for detail and a passion for deciphering data puzzles. You excel at turning data into meaningful insights and actionable recommendations.""",
            verbose=True,
            allow_delegation=True
        )

        self.scrum_master = Agent(
            role='Scrum Master',
            goal='Facilitate the team's Agile practices and processes',
            backstory="""You are the Scrum Master, the team's coach, and facilitator. Your primary goal is to ensure that the team adheres to Agile practices and works efficiently towards their goals.""",
            verbose=True,
            allow_delegation=False
        )

        self.data_visualisation_expert = Agent(
            role='Data Visualization Expert',
            goal='Recommend the best way to visualize the data and prepare it for the chosen visualization method.',
            backstory="""As a Data Visualization Expert, you have an eye for design and a knack for presenting data in the most insightful and accessible ways. You're familiar with a variety of visualization tools and techniques.""",
            verbose=True,
            allow_delegation=True
        )

        self.data_innovator = Agent(
            role='Data Innovator',
            goal="You're a data innovator. You analyze SQL databases table structure and generate 3 novel insights for your team to reflect on and query. Format your insights in JSON format.",
            backstory="""As a Data Innovator, you have a unique ability to see beyond the data. You connect the dots between disparate pieces of information to generate new, valuable insights that can transform the way your team operates.""",
            verbose=True,
            allow_delegation=True
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
            description="Is the following block of text a SQL Natural Language Query (NLQ)? Please rank from 1 to 5.",
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
        # Create a crew with the agents and tasks
        self.crew = Crew(
            agents=self.agents,
            tasks=self.tasks
        )
        return self

    def create_process(self):
        # Create the process with the crew
        self.process = Process(crew=self.crew)
        return self

    def execute(self):
        # Execute the crew process
        if self.process:
            self.process.execute()
        return self
    @tool("Executes a given SQL query string against the database.")
    def run_sql(self, sql: str) -> str:
        """
        Run a SQL query against the postgres database
        """
        self.agent_instruments.db.cur.execute(sql)
        columns = [desc[0] for desc in self.agent_instruments.db.cur.description]
        res = self.agent_instruments.db.cur.fetchall()

        list_of_dicts = [dict(zip(columns, row)) for row in res]

        json_result = json.dumps(list_of_dicts, indent=4, default=self.agent_instruments.datetime_handler)

        return json_result
