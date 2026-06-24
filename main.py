# import asyncio

# from app.workflows.graph import app
# from app.workflows.state import ClaimState

# from app.workflows.initial_data import INITIAL_STATE

# async def main() -> None:

#     # 1. Define a config dictionary (LangGraph needs this to track the thread/run)
#     # config: RunnableConfig = {"configurable": {"thread_id": "1"}}
#     # 2. Invoke the graph with the config
#     final_output = await app.ainvoke(
#         ClaimState.model_validate(INITIAL_STATE)
#     )  # needs to provide initial state to the graph
#     print("--- Final Output ---")
#     print(final_output)

#     # 3. Fetch and print the final state using the same config
#     # state = await app.aget_state(config)

#     # print("\n--- Current Graph State ---")
#     # # state.values contains your actual graph state variables
#     # print(json.dumps(state.values, indent=2, default=str))


# if __name__ == "__main__":
#     asyncio.run(main())
import uvicorn
from fastapi import FastAPI
from app.api.routes.claim import router

app = FastAPI() 
app.include_router(router)
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)