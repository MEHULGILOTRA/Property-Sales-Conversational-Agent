import asyncio
import uuid
from app.agent.graph import build_graph

async def run_cli():

    print("🚀 Initializing Silver Land Properties Assistant...")
    app = await build_graph()
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    print("\n--- Assistant Ready. Type 'exit' or 'quit' to stop. ---")
    
    while True:
        user_input = input("\n👤 You: ")
        
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Goodbye! 👋")
            break
        initial_state = {
            "messages": [{"role": "user", "content": user_input}],
            "projects": [],
            "shortlisted_projects": [],
            "summary": ""
        }

        try:
            final_state = await app.ainvoke({"messages": [("user", user_input)]}, config=config)
            # print(f"Final State is : {final_state}")
            assistant_reply = final_state.get("reply", "No response generated.")
            
            print(f"\n🏠 Assistant:\n{assistant_reply}")

        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_cli())
