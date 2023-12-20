from postgres_da_ai_agent.agents.instruments import PostgresAgentInstruments
from postgres_da_ai_agent.modules import rand
from postgres_da_ai_agent.modules import embeddings
from postgres_da_ai_agent.types import ConversationResult
from postgres_da_ai_agent.agents import agents
from postgres_da_ai_agent.modules import llm
from postgres_da_ai_agent.prompt_handler import informational_prompt, data_analysis_prompt, invalid_prompt, prompt_confidence
import argparse
import os

DB_URL = os.environ.get("DATABASE_URL")


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

    

    session_id = rand.generate_session_id(assistant_name + raw_prompt)

    with PostgresAgentInstruments(DB_URL, session_id) as (agent_instruments, db):
        nlq_confidence = prompt_confidence(prompt,agent_instruments=agent_instruments)

        match nlq_confidence:
            case (1 | 2):
                informational_prompt(nlq_confidence,prompt)
            case (3 | 4 | 5):
                data_analysis_prompt(nlq_confidence, prompt, db, agent_instruments, assistant_name)
            case _:
                invalid_prompt()

        # ---------- Simple Prompt Solution - Same thing, only 2 api calls instead of 8+ ------------
        assistant = Turbo4()
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

        # ----------- Example use case of Turbo4 and the Assistants API ------------

        (
            assistant.get_or_create_assistant(assistant_name)
            .make_thread()
            .equip_tools(tools)
            .add_message("Generate 10 random facts about LLM technology.")
            .run_thread()
            .add_message("Use the store_fact function to 1 fact.")
            .run_thread(toolbox=["store_fact"])
        )


if __name__ == "__main__":
    main()
