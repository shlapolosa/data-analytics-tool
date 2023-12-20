from postgres_da_ai_agent.agents.turbo4 import Turbo4
from postgres_da_ai_agent.types import Chat, TurboTool
from typing import List, Callable
import os
from postgres_da_ai_agent.agents.instruments import PostgresAgentInstruments
from postgres_da_ai_agent.modules import llm
from postgres_da_ai_agent.modules import rand
from postgres_da_ai_agent.modules import embeddings
from postgres_da_ai_agent.agents import agents
from postgres_da_ai_agent.types import ConversationResult
import argparse

DB_URL = os.environ.get("DATABASE_URL")
POSTGRES_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"


custom_function_tool_config = {
    "type": "function",
    "function": {
        "name": "store_fact",
        "description": "A function that stores a fact.",
        "parameters": {
            "type": "object",
            "properties": {"fact": {"type": "string"}},
        },
    },
}

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


def store_fact(fact: str):
    print(f"------store_fact({fact})------")
    return "Fact stored."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", help="The prompt for the AI")
    args = parser.parse_args()

    if not args.prompt:
        print("Please provide a prompt")
        return

    raw_prompt = args.prompt

    prompt = f"Fulfill this database query: {raw_prompt}. "

    assistant_name = "Turbo4"

    assistant = Turbo4()

    session_id = rand.generate_session_id(assistant_name + raw_prompt)

    with PostgresAgentInstruments(DB_URL, session_id) as (agent_instruments, db):
        database_embedder = embeddings.DatabaseEmbedder(db)

        table_definitions = database_embedder.get_similar_table_defs_for_prompt(
            raw_prompt
        )

        # code: move gate_orchestrator logic into its own function called prompt_confidence that returns nlq_confidence

        gate_orchestrator = agents.build_team_orchestrator(
            "scrum_master",
            agent_instruments,
            validate_results=lambda: (True, ""),
        )

        gate_orchestrator: ConversationResult = (
            gate_orchestrator.sequential_conversation(prompt)
        )

        print("gate_orchestrator.last_message_str", gate_orchestrator.last_message_str)

        nlq_confidence = int(gate_orchestrator.last_message_str)

        match nlq_confidence:
            case (1 | 2):
                print(f"❌ Gate Team Rejected - Confidence too low: {nlq_confidence}")
                # create a new function called informational_prompt and move print above to that function. also exit
                return
            case (3 | 4 | 5):
                print(f"✅ Gate Team Approved - Valid confidence: {nlq_confidence}")
                # create new function called data_analysis_prompt and move print above to that function. also move all logic from line 107 to line 165 into this function.
            case _:
                print("❌ Gate Team Rejected - Invalid response")
                return

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
            assistant.get_or_create_assistant(assistant_name)
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

        # ---------- Simple Prompt Solution - Same thing, only 2 api calls instead of 8+ ------------
        # sql_response = llm.prompt(
        #     prompt,
        #     model="gpt-4-1106-preview",
        #     instructions="You're an elite SQL developer. You generate the most concise and performant SQL queries.",
        # )
        # llm.prompt_func(
        #     "Use the run_sql function to run the SQL you've just generated: "
        #     + sql_response,
        #     model="gpt-4-1106-preview",
        #     instructions="You're an elite SQL developer. You generate the most concise and performant SQL queries.",
        #     turbo_tools=tools,
        # )
        # agent_instruments.validate_run_sql()

        # ----------- Example use case of Turbo4 and the Assistants API ------------

        # (
        #     assistant.get_or_create_assistant(assistant_name)
        #     .make_thread()
        #     .equip_tools(tools)
        #     .add_message("Generate 10 random facts about LLM technology.")
        #     .run_thread()
        #     .add_message("Use the store_fact function to 1 fact.")
        #     .run_thread(toolbox=["store_fact"])
        # )


if __name__ == "__main__":
    main()
