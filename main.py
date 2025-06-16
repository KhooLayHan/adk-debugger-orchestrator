# import asyncio
# # import google.adk.agents as Agent

# from agents.coding_agent import CodingAgent
# from agents.project_manager_agent import ProjectManagerAgent
# from agents.requirements_agent import RequirementsAgent
# from agents.utils import log_agent_event  # Import for initial logging


# async def main():
#     """
#     Main function to initialize and run the multi-agent SDLC workflow.
#     It sets up the agents, provides an initial user request, and orchestrates
#     the flow of tasks and messages between them.
#     """

#     print("Initializing agents...")

#     # Instantiate the agents
#     requirements_agent = RequirementsAgent(name="RequirementsAgent")
#     coding_agent = CodingAgent(name="CodingAgent")

#     # The ProjectManagerAgent needs references to the other agents to send messages.
#     # This is a simple way to connect them for local execution.
#     project_manager_agent = ProjectManagerAgent(
#         name="ProjectManagerAgent",
#         other_agents={
#             "RequirementsAgent": requirements_agent,
#             "CodingAgent": coding_agent,
#         },
#     )

#     # Register agents with the ADK runtime (crucial for message routing).
#     # Although not explicitly shown in ADK samples for direct object passing when runnning locally, ADK's internal routing relies on names.
#     # We will "run" agents as co-routines directly in the main loop to simulate.

#     # Start all agents as concurrent tasks
#     # This ensures they are listening for messages

#     # In ADK, agents need to be "registered" or "started" for the internal
#     # message routing to work. `Agent.start()` usually makes them listen.
#     # We create tasks for all agents to run concurrently.
#     agent_tasks = [
#         asyncio.create_task(project_manager_agent.start()),
#         asyncio.create_task(requirements_agent.start()),
#         asyncio.create_task(coding_agent.start()),
#     ]
#     print("All agents started and listening...")

#     # Give them a moment to initialize
#     await asyncio.sleep(1)

#     # Simulate an initial user request to the ProjectManagerAgent
#     user_request = "Develop a Python script to calculate the nth Fibonacci number, including basic tests."
#     # user_request = "Develop a Python script for a simple calculator with add and subtract, force_req_fail." # Test failure
#     # user_request = "Develop a Python script for generating prime numbers up to N, force_code_fail." # Test failure

#     initial_message = AgentMessage(
#         sender_id="User",  # The "User" is the source of this initial request
#         content=MessageContent(text=user_request),
#     )

#     print(f"\nUser: Sending initial request: '{user_request}'")
#     # ProjectManagetAgent is designed to handle this message directly
#     await project_manager_agent.handle_message(initial_message)

#     # Allow time for all agents to complete their tasks and log
#     # Please adjust this sleep duration based on LLM response times.
#     print("\nWaiting for agents to complete their workflow...")
#     await asyncio.sleep(30)  # Sufficient time for messages to be processed and logged

#     # Log a final event indicating the workflow completion
#     # This is not specific to any single agent's task but the overall run
#     await log_agent_event(
#         event_type="WORKFLOW_FINALIZED",
#         agent_id="MainRunner",
#         trace_id=project_manager_agent.current_trace_id,  # Use the trace ID from the project manager
#         message_summary="Multi-agent workflow initiated by MainRunner has concluded.",
#         status="COMPLETE",
#     )
#     print(
#         "MainRunner: Workflow initiated by user has concluded. Check BigQuery for traces."
#     )

#     # Stop agents gracefully (ADK might have a specific way to stop, or just let tasks finish)
#     for task in agent_tasks:
#         task.cancel()  # Or use agent.stop() if ADK provides it directly
#     await asyncio.gather(*agent_tasks, return_exceptions=True)  # Await cancellation


# if __name__ == "__main__":
#     asyncio.run(main())

# main.py
import asyncio
import uuid

from agents.coding_agent import CodingAgent
from agents.project_manager_agent import ProjectManagerAgent
from agents.requirements_agent import RequirementsAgent
from agents.utils import log_agent_event  # Import for initial logging


async def main():
    """
    Main function to initialize and run the multi-agent SDLC workflow.
    It sets up the agents, provides an initial user request, and orchestrates
    the flow of tasks and messages between them.
    """
    print("Initializing agents...")
    # Instantiate agents
    requirements_agent = RequirementsAgent(name="RequirementsAgent")
    coding_agent = CodingAgent(name="CodingAgent")

    # The ProjectManagerAgent needs references to other agents to send messages
    # This is a simple way to connect them for local execution.
    project_manager_agent = ProjectManagerAgent(
        name="ProjectManagerAgent",
        other_agents={
            "RequirementsAgent": requirements_agent,
            "CodingAgent": coding_agent,
        },
    )

    # In ADK, agents need to be "registered" or "started" for the internal
    # message routing to work. `Agent.start()` usually makes them listen.
    # We create tasks for all agents to run concurrently.
    agent_tasks = [
        asyncio.create_task(project_manager_agent.start()),
        asyncio.create_task(requirements_agent.start()),
        asyncio.create_task(coding_agent.start()),
    ]
    print("All agents started and listening...")

    # Give them a moment to initialize fully
    await asyncio.sleep(1)

    # Simulate an initial user request to the ProjectManagerAgent
    user_request = "Develop a Python script to calculate the nth Fibonacci number, including basic tests."
    # Test cases for simulated failures (uncomment one to try):
    # user_request = "Develop a Python script for a simple calculator with add and subtract. force_req_fail."
    # user_request = "Develop a Python script for generating prime numbers up to N. force_code_fail."

    # For the initial message from a "User" to the PM agent, we directly call handle_message.
    # ADK's internal routing takes over for messages between agents.
    initial_trace_id = str(uuid.uuid4())  # Generate a new trace_id for this session
    initial_context = {"trace_id": initial_trace_id}

    print(
        f"\nUser: Sending initial request (Trace ID: {initial_trace_id}): '{user_request}'"
    )
    # ProjectManagerAgent is designed to handle this message directly
    await project_manager_agent.handle_message(
        content=user_request, sender_id="User", context=initial_context
    )

    # Allow time for all agents to complete their tasks and log
    # This sleep is crucial for async operations to complete before the script exits.
    print("\nWaiting for agents to complete their workflow...")
    await asyncio.sleep(30)  # Adjust based on how long LLM calls take

    # Log a final event indicating the overall workflow conclusion
    await log_agent_event(
        event_type="WORKFLOW_FINALIZED",
        agent_id="MainRunner",
        trace_id=initial_trace_id,  # Use the initial trace_id for the overall workflow
        message_summary="Multi-agent SDLC workflow initiated by MainRunner has concluded.",
        status="COMPLETE",
    )
    print(
        "MainRunner: Workflow initiated by user has concluded. Check BigQuery for traces."
    )

    # Gracefully cancel agent tasks
    for task in agent_tasks:
        task.cancel()
    # Await tasks to ensure they are properly handled, even if cancelled
    await asyncio.gather(*agent_tasks, return_exceptions=True)
    print("All agent tasks cancelled.")


if __name__ == "__main__":
    asyncio.run(main())
