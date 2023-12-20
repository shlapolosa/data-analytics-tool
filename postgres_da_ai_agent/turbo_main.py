from postgres_da_ai_agent.agents.instruments import PostgresAgentInstruments
from postgres_da_ai_agent.modules import rand
from postgres_da_ai_agent.modules import embeddings
from postgres_da_ai_agent.prompt_handler import informational_prompt, data_analysis_prompt, invalid_response
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

        def prompt_confidence(prompt: str) -> int:
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

        nlq_confidence = prompt_confidence(prompt)

        match nlq_confidence:
            case (1 | 2):
                informational_prompt(nlq_confidence)
            case (3 | 4 | 5):
                data_analysis_prompt(nlq_confidence, prompt, table_definitions, agent_instruments, assistant_name)
            case _:
                invalid_response()

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
