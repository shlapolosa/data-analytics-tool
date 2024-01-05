from typing import List
from postgres_da_ai_agent.types import TurboTool
from postgres_da_ai_agent.agents.turbo4 import Turbo4
from postgres_da_ai_agent.modules import llm
from postgres_da_ai_agent.modules import embeddings
from postgres_da_ai_agent.modules.db import PostgresManager
from postgres_da_ai_agent.agents import agents
from postgres_da_ai_agent.types import ConversationResult
import os

POSTGRES_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"


run_sql_tool_config = {
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": "Run a SQL query against the postgres database",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL query to run",
                }
            },
            "required": ["sql"],
        },
    },
}


def informational_prompt(nlq_confidence: int, prompt: str):
    print(f"❌ Gate Team Rejected - Confidence too low: {nlq_confidence}")
    exit()

def data_analysis_prompt(nlq_confidence: int, prompt: str, db: PostgresManager ,agent_instruments, assistant_name: str):
    print(f"✅ Gate Team Approved - Valid confidence: {nlq_confidence}")

    database_embedder = embeddings.DatabaseEmbedder(db)
    table_definitions = database_embedder.get_similar_table_defs_for_prompt(prompt)

    prompt = llm.add_cap_ref(
        prompt,
        f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query.",
        POSTGRES_TABLE_DEFINITIONS_CAP_REF,
        table_definitions,
    )

    tools = [
        TurboTool("run_sql", run_sql_tool_config, agent_instruments.run_sql),
    ]

    (
        Turbo4().get_or_create_assistant(assistant_name)
        .set_instructions(
            "You're an elite SQL developer. You generate the most concise and performant SQL queries."
        )
        .equip_tools(tools)
        .make_thread()
        .add_message(prompt)
        .run_thread()
        .add_message(
            "Use the run_sql function to run the SQL you've just generated.",
        )
        .run_thread(toolbox=[tools[0].name])
        .run_validation(agent_instruments.validate_run_sql)
        .spy_on_assistant(agent_instruments.make_agent_chat_file(assistant_name))
        .get_costs_and_tokens(
            agent_instruments.make_agent_cost_file(assistant_name)
        )
    )

    print(f"✅ Turbo4 Assistant finished.")

def invalid_prompt():
    print("❌ Gate Team Rejected - Invalid response")
    exit()


def prompt_confidence(prompt: str, agent_instruments) -> int:
    gate_orchestrator = agents.build_team_orchestrator(
        "scrum_master",
        agent_instruments,
        validate_results=lambda: (True, ""),
    )

    gate_orchestrator: ConversationResult = (
        gate_orchestrator.sequential_conversation(prompt)
    )

    print("gate_orchestrator.last_message_str", gate_orchestrator.last_message_str)

    return int(gate_orchestrator.last_message_str)


def data_analyst_prompt_autogen(prompt: str, agent_instruments):
    # ---------- Simple Prompt Solution - Same thing, only 2 api calls instead of 8+ ------------
    tools = [
        TurboTool("run_sql", run_sql_tool_config, agent_instruments.run_sql),
    ]
    sql_response = llm.prompt(
        prompt,
        model="gpt-4-1106-preview",
        instructions="You're an elite SQL developer. You generate the most concise and performant SQL queries.",
    )
    llm.prompt_func(
        "Use the run_sql function to run the SQL you've just generated: "
        + sql_response,
        model="gpt-4-1106-preview",
        instructions="You're an elite SQL developer. You generate the most concise and performant SQL queries.",
        turbo_tools=tools,
    )
    agent_instruments.validate_run_sql()

class PromptExecutor:
    def __init__(self, prompt: str, agent_instruments):
        self.prompt = prompt
        self.agent_instruments = agent_instruments
        self.conversation_result = ConversationResult(success=True,messages=[],cost=0.0,tokens=0,last_message_str="",error_message="",suggestions=[])

    def __enter__(self):
        return self.assess_prompt(self.db)

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def execute(self) -> ConversationResult:
        raise NotImplementedError("Subclasses should implement this!")
    
    def innovation_suggestions(self)-> ConversationResult:
        # ----------- Data Insights Team: Based on sql table definitions and a prompt generate novel insights -------------
        innovation_prompt = f"Given this database query: '{self.prompt}'. Generate novel insights and new database queries to give business insights."
        
        map_table_name_to_table_def = self.db.get_table_definition_map_for_embeddings()

        database_embedder = embeddings.DatabaseEmbedder(self.db)

        for name, table_def in map_table_name_to_table_def.items():
            database_embedder.add_table(name, table_def)

        similar_tables = database_embedder.get_similar_tables(self.prompt, n=5)

        related_table_names = self.db.get_related_tables(similar_tables, n=3)

        core_and_related_table_definitions = (
            database_embedder.get_table_definitions_from_names(
                related_table_names + similar_tables
            )
        )


        insights_prompt = llm.add_cap_ref(
            innovation_prompt,
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query.",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            core_and_related_table_definitions,
        )

        data_insights_orchestrator = agents.build_team_orchestrator(
            "data_insights",
            self.agent_instruments,
            validate_results=self.agent_instruments.validate_innovation_files,
        )

        data_insights_conversation_result: ConversationResult = (
            data_insights_orchestrator.round_robin_conversation(
                insights_prompt, loops=1
            )
        )

        match data_insights_conversation_result:
            case ConversationResult(
                success=True, cost=data_insights_cost, tokens=data_insights_tokens
            ):
                print(
                    f"✅ Orchestrator was successful. Team: {data_insights_orchestrator.name}"
                )
                print(
                    f"💰📊🤖 {data_insights_orchestrator.name} Cost: {data_insights_cost}, tokens: {data_insights_tokens}"
                )
            case _:
                print(
                    f"❌ Orchestrator failed. Team: {data_insights_orchestrator.name} Failed"
                )
        return data_insights_conversation_result
        # insights_prompt = llm.add_cap_ref(
        #     innovation_prompt,
        #     f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query.",
        #     POSTGRES_TABLE_DEFINITIONS_CAP_REF,
        #     core_and_related_table_definitions,
        # )

        # data_insights_orchestrator = agents.build_team_orchestrator(
        #     "data_insights",
        #     self.agent_instruments,
        #     validate_results=self.agent_instruments.validate_innovation_files,
        # )

        # data_insights_conversation_result: ConversationResult = (
        #     data_insights_orchestrator.round_robin_conversation(
        #         insights_prompt, loops=1
        #     )
        # )

        # match data_insights_conversation_result:
        #     case ConversationResult(
        #         success=True, cost=data_insights_cost, tokens=data_insights_tokens
        #     ):
        #         print(
        #             f"✅ Orchestrator was successful. Team: {data_insights_orchestrator.name}"
        #         )
        #         print(
        #             f"💰📊🤖 {data_insights_orchestrator.name} Cost: {data_insights_cost}, tokens: {data_insights_tokens}"
        #         )
        #     case _:
        #         print(
        #             f"❌ Orchestrator failed. Team: {data_insights_orchestrator.name} Failed"
        #         )


class InformationalPromptExecutor(PromptExecutor):
    def __init__(self, prompt: str, agent_instruments, assistant_name: str):
        super().__init__(prompt, agent_instruments)
        self.assistant_name = assistant_name

    def execute(self)-> ConversationResult:
        # Implement the logic specific to InformationalPromptExecutor here.
        pass

class AutogenDataAnalystPromptExecutor(PromptExecutor):
    def __init__(self, prompt: str,  db: PostgresManager, agent_instruments):
        super().__init__(prompt, agent_instruments)
        self.db = db

    def execute(self)-> ConversationResult:
        print(f"✅ Gate Team Approved AUTOGEN")
        # ---------- Simple Prompt Solution - Same thing, only 2 api calls instead of 8+ ------------
        map_table_name_to_table_def = self.db.get_table_definition_map_for_embeddings()

        database_embedder = embeddings.DatabaseEmbedder(self.db)

        for name, table_def in map_table_name_to_table_def.items():
            database_embedder.add_table(name, table_def)

        similar_tables = database_embedder.get_similar_tables(self.prompt, n=5)

        table_definitions = database_embedder.get_table_definitions_from_names(
            similar_tables
        )

        prompt = llm.add_cap_ref(
            self.prompt,
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query.",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            table_definitions,
        )

        prompt_sql_coder = f"""
            ## Task
            Generate a SQL query to answer the following question:
            `{self.prompt}`

            ### Database Schema
            This query will run on a database whose schema is represented in this string:
            {table_definitions}

            ### SQL
            Given the database schema, here is the SQL query that answers `{self.prompt}`:
            ```sql


            """

        # ----------- Data Eng Team: Based on a sql table definitions and a prompt create an sql statement and execute it -------------

        data_eng_orchestrator = agents.build_team_orchestrator(
            "data_eng",
            self.agent_instruments,
            validate_results=self.agent_instruments.validate_run_sql,
        )

        data_eng_conversation_result: ConversationResult = (
            data_eng_orchestrator.sequential_conversation(prompt)
        )

        match data_eng_conversation_result:
            case ConversationResult(
                success=True, cost=data_eng_cost, tokens=data_eng_tokens
            ):
                print(
                    f"✅ Orchestrator was successful. Team: {data_eng_orchestrator.name}"
                )
                print(
                    f"💰📊🤖 {data_eng_orchestrator.name} Cost: {data_eng_cost}, tokens: {data_eng_tokens}"
                )
                
                self.conversation_result = data_eng_conversation_result
                print(
                    f"Initial conversation results: {self.conversation_result}"
                )
                conv_res = self.innovation_suggestions()
                print(
                    f"Innovation results: {conv_res}"
                )
                self.conversation_result.suggestions = conv_res.messages
                print(
                    f"Total results: {conv_res}"
                )
            case _:
                print(
                    f"❌ Orchestrator failed. Team: {data_eng_orchestrator.name} Failed"
                )
        return self.conversation_result

class AssistantApiPromptExecutor(AutogenDataAnalystPromptExecutor):
    def __init__(self, prompt: str, agent_instruments, assistant_name: str, db: PostgresManager, nlq_confidence: int):
        super().__init__(prompt, db, agent_instruments)
        self.assistant_name = assistant_name
        self.db = db
        self.nlq_confidence = nlq_confidence

    def execute(self) -> ConversationResult:
        print(f"✅ Gate Team Approved OPEN API: {self.nlq_confidence}")

        database_embedder = embeddings.DatabaseEmbedder(self.db)
        table_definitions = database_embedder.get_similar_table_defs_for_prompt(self.prompt)

        self.prompt = llm.add_cap_ref(
            self.prompt,
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query.",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            table_definitions,
        )

        tools = [
            TurboTool("run_sql", run_sql_tool_config, self.agent_instruments.run_sql),
        ]

        (
            Turbo4().get_or_create_assistant(self.assistant_name)
            .set_instructions(
                "You're an elite SQL developer. You generate the most concise and performant SQL queries."
            )
            .equip_tools(tools)
            .make_thread()
            .add_message(self.prompt)
            .run_thread()
            .add_message(
                "Use the run_sql function to run the SQL you've just generated.",
            )
            .run_thread(toolbox=[tools[0].name])
            .run_validation(self.agent_instruments.validate_run_sql)
            .spy_on_assistant(self.agent_instruments.make_agent_chat_file(self.assistant_name))
            .get_costs_and_tokens(
                self.agent_instruments.make_agent_cost_file(self.assistant_name)
            )
        )

        print(f"✅ Turbo4 Assistant finished.")
        self.innovation_suggestions()
        result, sql, follow_up = self.agent_instruments.populate_conversation_result()
        self.conversation_result = ConversationResult(success=True, messages=[], cost=0.0, tokens=0, last_message_str="", error_message="", sql=sql, result=result, follow_up=follow_up)
        return self.conversation_result

class PromptHandler:
    def __init__(self, prompt: str, agent_instruments, db: PostgresManager):
        self.prompt = prompt
        self.agent_instruments = agent_instruments
        self.db = db

    def __enter__(self) -> PromptExecutor:
        return self.assess_prompt(self.db)

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def assess_prompt(self, db: PostgresManager) -> PromptExecutor:
        nlq_confidence = self._prompt_confidence()
        match nlq_confidence:
            case 1 | 2:
                return InformationalPromptExecutor(self.prompt, self.agent_instruments, "SQL_Analyst")
            case 3 | 4 | 5:
                from dotenv import load_dotenv

                # Assuming the .env file is at the root of the project
                dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
                load_dotenv(dotenv_path, verbose=True)
                print("OPENAI_API_KEY "+os.getenv("OPENAI_API_KEY"))
                if False :                                                                                                                        
                    return AutogenDataAnalystPromptExecutor(self.prompt, db, self.agent_instruments)                                                                                            
                else:                                                                                                                                                                       
                    return AssistantApiPromptExecutor(self.prompt, self.agent_instruments, "Turbo4", db, nlq_confidence)


    def _prompt_confidence(self) -> int:
        gate_orchestrator = agents.build_team_orchestrator(
            "scrum_master",
            self.agent_instruments,
            validate_results=lambda: (True, ""),
        )

        gate_orchestrator: ConversationResult = (
            gate_orchestrator.sequential_conversation(self.prompt)
        )

        print("gate_orchestrator.last_message_str", gate_orchestrator.last_message_str)

        return int(gate_orchestrator.last_message_str)
        # return 5
class CrewAIDataAnalystPromptExecutor(PromptExecutor):
    def __init__(self, prompt: str, db: PostgresManager, agent_instruments):
        super().__init__(prompt, agent_instruments)
        self.db = db

    def execute(self) -> ConversationResult:
        from crewai import Agent, Task, Crew, Process

        # Define the agents with roles and goals
        data_engineer = Agent(
            role='Data Engineer',
            goal='Prepare and transform data for analytical or operational uses',
            backstory="""You are a meticulous Data Engineer responsible for building and maintaining the data architecture of the company. Your expertise in data modeling, ETL processes, and data warehousing is unparalleled.""",
            verbose=True,
            allow_delegation=True
        )

        data_analyst = Agent(
            role='Data Analyst',
            goal='Analyze data to help inform business decisions',
            backstory="""As a Data Analyst, you have a sharp eye for detail and a passion for deciphering data puzzles. You excel at turning data into meaningful insights and actionable recommendations.""",
            verbose=True,
            allow_delegation=True
        )

        scrum_master = Agent(
            role='Scrum Master',
            goal='Facilitate the team's Agile practices and processes',
            backstory="""You are the Scrum Master, the team's coach, and facilitator. Your primary goal is to ensure that the team adheres to Agile practices and works efficiently towards their goals.""",
            verbose=True,
            allow_delegation=False
        )

        # Logic to utilize the agents will be implemented here.
        # This is a placeholder to show where the agents would be used in the workflow.
        # Actual tasks, crew creation, and execution logic will depend on the specific requirements.

        return ConversationResult(success=True, messages=[], cost=0.0, tokens=0, last_message_str="", error_message="")
