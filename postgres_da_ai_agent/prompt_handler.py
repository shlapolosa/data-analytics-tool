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

    def __enter__(self):
        return self.assess_prompt(self.db)

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def execute(self):
        raise NotImplementedError("Subclasses should implement this!")

class InformationalPromptExecutor(PromptExecutor):
    def __init__(self, prompt: str, agent_instruments, assistant_name: str):
        super().__init__(prompt, agent_instruments)
        self.assistant_name = assistant_name

    def execute(self):
        # Implement the logic specific to InformationalPromptExecutor here.
        pass

class AutogenDataAnalystPromptExecutor(PromptExecutor):
    def __init__(self, prompt: str, agent_instruments):
        super().__init__(prompt, agent_instruments)

    def execute(self):
        print(f"✅ Gate Team Approved AUTOGEN")
        # ---------- Simple Prompt Solution - Same thing, only 2 api calls instead of 8+ ------------
        tools = [
            TurboTool("run_sql", run_sql_tool_config, self.agent_instruments.run_sql),
        ]
        sql_response = llm.prompt(
            self.prompt,
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
        self.agent_instruments.validate_run_sql()

class AssistantApiPromptExecutor(AutogenDataAnalystPromptExecutor):
    def __init__(self, prompt: str, agent_instruments, assistant_name: str, db: PostgresManager, nlq_confidence: int):
        super().__init__(prompt, agent_instruments)
        self.assistant_name = assistant_name
        self.db = db
        self.nlq_confidence = nlq_confidence

    def execute(self):
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
        
                if os.getenv("USE_OPENAI_API") == 'True':                                                                                                                        
                    return AutogenDataAnalystPromptExecutor(self.prompt, self.agent_instruments)                                                                                            
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
