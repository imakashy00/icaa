import asyncio

from langchain_core.runnables import RunnableConfig
import json

from app.workflows.graph import app
from app.workflows.state import ClaimState

async def main() -> None:
    initial_state = ClaimState()
    # 1. Define a config dictionary (LangGraph needs this to track the thread/run)
    # config: RunnableConfig = {"configurable": {"thread_id": "1"}}
    # 2. Invoke the graph with the config
    final_output = await app.ainvoke(initial_state) # needs to provide initial state to the graph
    print("--- Final Output ---")
    print(final_output)

    # 3. Fetch and print the final state using the same config
    # state = await app.aget_state(config)

    # print("\n--- Current Graph State ---")
    # # state.values contains your actual graph state variables
    # print(json.dumps(state.values, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())