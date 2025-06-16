# import time

# import asyncio
# import uuid
# from google.adk.agents import Agent
# from google.generativeai import MessageContent
# from utils import llm_model, log_agent_event


# class ProjectManagerAgent(Agent):
#     """
#     The ProjectManagerAgent orchestrates the entire software development lifecycle (SDLC)
#     by coordinating tasks among other specialized agents. It receives initial requests,
#     dispatches sub-tasks, and tracks the overall progress and status of the workflow.
#     """

#     def __init__(self, name: str, other_agents: dict):
#         """
#         Initializes the ProjectManagerAgent.

#         Args:
#             name (str): The unique name of the agent.
#             other_agents (dict): A dictionary mapping agent names (str) to their
#                                  Agent instances, allowing the PM to send messages.
#         """
#         super().__init__(
#             name=name,
#             llm=llm_model,  # Uses the shared LLM instance
#             description="Orchestrates the software developmenty lifecycle.",
#             instruction="Manage the SDLC from initial request to final delivery by coordinating with other agents.",
#         )
#         self.other_agents = other_agents  # Store references to other agents
#         self.current_trace_id = None  # Holds the ID for the current workflow to run

#     async def handle_message(self, content: str, sender_id: str, context: dict):
#         """
#         Handles incoming messages for the Project Manager, initiating and
#         managing the SDLC workflow.

#         Args:
#             content (str): The text content of the message.
#             sender_id (str): The ID of the agent or entity that sent the message.
#             context (dict): A dictionary containing contextual information for the message,
#                             including the trace_id for session tracking.
#         """

#         # Determines/Propagates the trace_id for the current session.
#         self.current_trace_id = context.get("trace_id", str(uuid.uuid4()))

#         start_time = time.time()
#         await log_agent_event(
#             event_type="AGENT_START",
#             agent_id=self.name,
#             trace_id=self.current_trace_id,
#             message_summary=f"Received initial request: {content}",
#             source_agent_id=sender_id,
#             details={"original_request": content},
#         )
#         print(f"{self.name}: Received initial request from {sender_id}: {content}")

#         initial_request_text = content

#         # 1. Request requirements
#         # ADK send_message takes recipient_id, content, and then context as kwargs
#         await self.send_message(
#             recipient_id="RequirementsAgent",
#             content=f"Generate detailed requirements for: {initial_request_text}",
#             context={"trace_id": self.current_trace_id},
#         )
#         await log_agent_event(
#             event_type="MESSAGE_SEND",
#             agent_id=self.name,
#             trace_id=self.current_trace_id,
#             message_summary=f"Requesting requirements for: {initial_request_text[:50]}...",
#             source_agent_id=self.name,
#             target_agent_id="RequirementsAgent",
#             details={"task_description": initial_request_text},
#         )

#         requirements_response = await self.wait_for_response(
#             sender_id="RequirementsAgent", context={"trace_id": self.current_trace_id}
#         )

#         requirements_text = requirements_response.content.text
#         print(f"PM: Receeived requirements: {requirements_text}")

#         # Simulate a delay for human-like-processing
#         await asyncio.sleep(2)

#         # 2. Request Code based on Requirements
#         await self._send_task(
#             target_agent_name="CodingAgent",
#             task_description={
#                 "Write Python code based on the following requirements: {requirements_text}"
#             },
#         )
#         code_response = await self.wait_for_response(
#             sender_id="CodingAgent", context={"trace_id": self.current_trace_id}
#         )

#         generated_code = code_response.content.text
#         print(f"PM: Received code: \n{generated_code}")

#         # Simulate a delay
#         await asyncio.sleep(1)

#         # --- Simulated Testing (Optional: Will be adding a real TestingAgent later) ---
#         # Assuming success for simplicity -- randonmess can be added later for debugger demo
#         test_status = "SUCCESS"
#         if "simulated_test_failed" in initial_request_text.lower():
#             test_status = "FAILURE"
#             print("PM: Simulating a test failure as requested.")
#         else:
#             print("PM: Simulating successfull testing.")

#         await log_agent_event(
#             event_type="TASK_COMPLETE",
#             agent_id=self.name,
#             trace_id=self.current_trace_id,
#             message_summary=f"Finished SDLC workflow. Final status: {test_status}",
#             status=test_status,
#             details={
#                 "final_code": generated_code,
#                 "test_status": test_status,
#             },
#         )
#         print(f"PM: SDLC workflow completed with status: {test_status}")

#     async def _send_task(self, target_agent_name: str, task_description: str):
#         """
#         Helper to send a task message to another agent and logs it.
#         """

#         target_agent = self.other_agents.get(target_agent_name)
#         if not target_agent:
#             print(f"Error: {target_agent_name} not found.")
#             await log_agent_event(
#                 event_type="ERROR",
#                 agent_id=self.name,
#                 trace_id=self.current_trace_id,
#                 message_summary=f"Target agent '{target_agent_name}' not found for task: {task_description}",
#                 status="FAILURE",
#                 details={
#                     "target_agent": target_agent_name,
#                     "task": task_description,
#                 },
#             )

#             return

#         await self.send_message(
#             recipient=target_agent_name,
#             content=MessageContent(text=task_description),
#             context={"trace_id": self.current_trace_id},  # Propagate trace_id
#         )

#         await log_agent_event(
#             event_type="MESSAGE_SEND",
#             agent_id=self.name,
#             trace_id=self.current_trace_id,
#             message_summary=f"Sending task to {target_agent_name}: {task_description}",
#             source_agent_id=self.name,
#             target_agent_id=target_agent_name,
#             details={
#                 "task": task_description,
#             },
#         )
#         print(f"PM: Sent task to {target_agent_name}.")

#     async def _wait_for_response(self, sender_id: str, context: dict):
#         """
#         Helper to wait for a response and logs the reception.
#         """

#         await log_agent_event(
#             event_type="WAITING_FOR_RESPONSE",
#             agent_id=self.name,
#             trace_id=self.current_trace_id,
#             message_summary=f"Waiting for response from {sender_id}",
#             source_agent_id=sender_id,  # This is who we expect to send from
#             target_agent_id=self.name,  # This is us
#             details={
#                 "context": context,
#             },
#         )

#         response = await self.receive_message(
#             sender_id=sender_id,
#             context=context,
#         )

#         await log_agent_event(
#             event_type="MESSAGE_RECEIVE",
#             agent_id=self.name,
#             trace_id=self.current_trace_id,
#             message_summary=f"Received response from {sender_id}: {response.content.text[:100]}...",
#             source_agent_id=sender_id,
#             target_agent_id=self.name,
#             details={
#                 "full_response_text": response.content.text,
#             },
#         )

#         return response

# agents/project_manager_agent.py

import time  # For measuring duration

import asyncio
import uuid
from google.adk.agents import Agent  # type: ignore

from .utils import llm_model, log_agent_event  # Use llm_model instead of llm


class ProjectManagerAgent(Agent):
    """
    The ProjectManagerAgent orchestrates the entire software development lifecycle (SDLC)
    by coordinating tasks among other specialized agents. It receives initial requests,
    dispatches sub-tasks, and tracks the overall progress and status of the workflow.
    """

    def __init__(self, name: str, other_agents: dict):
        """
        Initializes the ProjectManagerAgent.

        Args:
            name (str): The unique name of the agent.
            other_agents (dict): A dictionary mapping agent names (str) to their
                                 Agent instances, allowing the PM to send messages.
        """
        super().__init__(
            name=name,
            llm=llm_model,  # Pass the GenerativeModel instance
            description="Orchestrates the software development lifecycle.",
            instruction="Manage the SDLC from initial request to final delivery by coordinating other agents.",
        )
        self.other_agents = other_agents  # Store references to other agents
        self.current_trace_id = None  # To hold the ID for the current workflow run

    async def handle_message(self, content: str, sender_id: str, context: dict):
        """
        Handles incoming messages for the Project Manager, initiating and
        managing the SDLC workflow.

        Args:
            content (str): The text content of the message.
            sender_id (str): The ID of the agent or entity that sent the message.
            context (dict): A dictionary containing contextual information for the message,
                            including the trace_id for session tracking.
        """
        # Determine/Propagate trace_id for the session
        self.current_trace_id = context.get("trace_id", str(uuid.uuid4()))

        start_time = time.time()
        await log_agent_event(
            event_type="AGENT_START",
            agent_id=self.name,
            trace_id=self.current_trace_id,
            message_summary=f"Received initial request: {content}",
            source_agent_id=sender_id,
            details={"original_request": content},
        )
        print(f"{self.name}: Received initial request from {sender_id}: {content}")

        initial_request_text = content

        # 1. Request Requirements
        # The ADK send_message takes recipient_id, content, and then context as kwargs
        req_start_time = time.time()
        await self.send_message(
            recipient_id="RequirementsAgent",
            content=f"Generate detailed requirements for: {initial_request_text}",
            context={"trace_id": self.current_trace_id},  # Propagate trace_id
        )
        await log_agent_event(
            event_type="MESSAGE_SEND",
            agent_id=self.name,
            trace_id=self.current_trace_id,
            message_summary=f"Requesting requirements for: {initial_request_text[:50]}...",
            source_agent_id=self.name,
            target_agent_id="RequirementsAgent",
            details={"task_description": initial_request_text},
        )
        print(f"{self.name}: Sent task to RequirementsAgent.")

        # The ADK receive_message takes sender_id and optional context
        requirements_text = await self.receive_message(
            sender_id="RequirementsAgent",
            context={"trace_id": self.current_trace_id},  # Use context for filtering
        )
        req_end_time = time.time()
        await log_agent_event(
            event_type="MESSAGE_RECEIVE",
            agent_id=self.name,
            trace_id=self.current_trace_id,
            message_summary=f"Received requirements: {requirements_text[:100]}...",
            source_agent_id="RequirementsAgent",
            target_agent_id=self.name,
            duration_ms=int(
                (req_end_time - req_start_time) * 1000
            ),  # Duration of request-response cycle
            details={"full_response_text": requirements_text},
        )
        print(f"{self.name}: Received Requirements: {requirements_text[:50]}...")

        # Simulate a delay for human-like processing
        await asyncio.sleep(1)

        # 2. Request Code based on Requirements
        code_start_time = time.time()
        await self.send_message(
            recipient_id="CodingAgent",
            content=f"Write Python code based on these requirements: {requirements_text}",
            context={"trace_id": self.current_trace_id},
        )
        await log_agent_event(
            event_type="MESSAGE_SEND",
            agent_id=self.name,
            trace_id=self.current_trace_id,
            message_summary=f"Requesting code based on requirements: {requirements_text[:50]}...",
            source_agent_id=self.name,
            target_agent_id="CodingAgent",
            details={"requirements_provided": requirements_text},
        )
        print(f"{self.name}: Sent task to CodingAgent.")

        generated_code = await self.receive_message(
            sender_id="CodingAgent", context={"trace_id": self.current_trace_id}
        )
        code_end_time = time.time()
        await log_agent_event(
            event_type="MESSAGE_RECEIVE",
            agent_id=self.name,
            trace_id=self.current_trace_id,
            message_summary=f"Received code: {generated_code[:100]}...",
            source_agent_id="CodingAgent",
            target_agent_id=self.name,
            duration_ms=int((code_end_time - code_start_time) * 1000),
            details={"full_generated_code": generated_code},
        )
        print(f"{self.name}: Received Code: \n{generated_code[:100]}...")

        # Simulate Testing Phase
        test_status = "SUCCESS"
        if "simulated_test_fail" in initial_request_text.lower():
            test_status = "FAILURE"
            print(f"{self.name}: Simulating a test failure as requested.")
        else:
            print(f"{self.name}: Simulating successful testing.")

        end_time = time.time()
        await log_agent_event(
            event_type="TASK_COMPLETE",
            agent_id=self.name,
            trace_id=self.current_trace_id,
            message_summary=f"Finished SDLC workflow. Final status: {test_status}",
            status=test_status,
            duration_ms=int((end_time - start_time) * 1000),  # Total duration
            details={
                "final_code_snippet": generated_code[:500],
                "test_status": test_status,
            },
        )
        print(f"{self.name}: SDLC workflow completed with status: {test_status}")
