# import asyncio
# from google.adk.agents import Agent, AgentMessage, MessageContent

# from .utils import llm, log_agent_event


# class RequirementsAgent(Agent):
#     def __init__(self, name: str):
#         super().__init__(
#             name=name,
#             llm=llm,
#             description="Generates detailed software requirements.",
#             instruction="You are a meticulous software requirements engineer. Convert high-level requests into clear, concise and detailed functional and non-functional requirements. Respond with only the requirements.",
#         )

#     async def handle_message(self, message: AgentMessage):
#         trace_id = message.context.get("trace_id", "UNKNOWN TRACE") # Get trace_id from message context

#         await log_agent_event(
#             event_type="AGENT_START",
#             agent_id=self.name,
#             trace_id=trace_id,
#             message_summary=f"Received request for requirements: {message.content.text}",
#             source_agent_id=message.sender.name,
#             details={"input_request": message.context.text}
#         )
#         print(f"Requirements Agent: Processing request: {message.context.text}")

#         # Simulate processing time
#         await asyncio.sleep(3) # A longer delay to see it in debugger

#         # Use LLM to generate requirements
#         llm_response = await self.llm.generate_text(
#             prompt=f"Generate detailed requirements for: {message.context.text}. Respond ONLY with the requirements, no preamble or extra text."
#         )
#         requirements_text = llm_response.text
#         if not requirements_text.strip():
#             requirements_text = "No specific requirements generated. Need more context." # Fallback

#         # Simulate a potential failure based on keyword
#         status = "SUCCESS"
#         if "force_req_fail" in message.context.text.lower():
#             requirements_text = "ERROR: Could not generate requirements due to forced failure."
#             status = "FAILURE"

#             await log_agent_event(
#                 event_type="ERROR",
#                 agent_id=self.name,
#                 trace_id=trace_id,
#                 message_summary="Forced requirements generation failure.",
#                 status="FAILURE",
#                 details={"input_text": message.context.text}
#             )

#         response_content = MessageContent(text=requirements_text)
#         await self.send_message(
#             recipient=message.sender_id,
#             content=response_content,
#             context={"trace_id": trace_id} # Propagate trace_id back
#         )

#         await log_agent_event(
#             event_type="TASK_COMPLETE",
#             agent_id=self.name,
#             message_summary=f"Generated requirements: {requirements_text[:100]}...",
#             status=status,
#             details={"generated_requirements": requirements_text}
#         )
#         print("Requirements Agent: Finished and sent requirements.")


# agents/requirements_agent.py
import time  # For measuring duration

import asyncio
from google.adk.agents import Agent  # type: ignore

# Note: No AgentMessage or MessageContent classes needed here from ADK
from .utils import llm_model, log_agent_event  # Use llm_model instead of llm


class RequirementsAgent(Agent):
    """
    The RequirementsAgent is responsible for converting high-level requests
    into detailed functional and non-functional software requirements
    using a Large Language Model.
    """

    def __init__(self, name: str):
        """
        Initializes the RequirementsAgent.

        Args:
            name (str): The unique name of the agent.
        """
        super().__init__(
            name=name,
            llm=llm_model,  # Pass the GenerativeModel instance
            description="Generates detailed software requirements.",
            instruction="You are a meticulous software requirements engineer. Convert high-level requests into clear, concise, and detailed functional and non-functional requirements. Respond with only the requirements.",
        )

    async def handle_message(self, content: str, sender_id: str, context: dict):
        """
        Handles incoming messages, processes the request to generate requirements,
        and sends the generated requirements back to the sender.

        Args:
            content (str): The text content of the message, which is the high-level request.
            sender_id (str): The ID of the agent that sent the request.
            context (dict): A dictionary containing contextual information, including the trace_id.
        """
        trace_id = context.get(
            "trace_id", "UNKNOWN_TRACE"
        )  # Get trace_id from message context
        start_time = time.time()

        await log_agent_event(
            event_type="AGENT_START",
            agent_id=self.name,
            trace_id=trace_id,
            message_summary=f"Received request for requirements from {sender_id}: {content[:100]}...",
            source_agent_id=sender_id,
            details={"input_request": content},
        )
        print(f"{self.name}: Processing request from {sender_id}: {content}")

        # Simulate processing time
        await asyncio.sleep(1)  # Shorter delay for LLM calls

        # Use LLM to generate requirements
        llm_prompt = f"{self.instruction}\n\nHigh-level request: {content}"
        llm_call_start = time.time()
        try:
            # For google-generativeai, it's model.generate_content
            llm_response = await self.llm.generate_content(llm_prompt)
            requirements_text = llm_response.text
        except Exception as e:
            requirements_text = f"ERROR: LLM failed to generate requirements: {e}"
            print(f"LLM Error in {self.name}: {e}")
        llm_call_end = time.time()

        if not requirements_text.strip():
            requirements_text = "No specific requirements generated. Need more context or LLM issue."  # Fallback

        # Simulate a potential failure based on keyword
        status = "SUCCESS"
        if "force_req_fail" in content.lower():
            requirements_text = (
                "ERROR: Could not generate requirements due to forced failure."
            )
            status = "FAILURE"
            await log_agent_event(
                event_type="ERROR",
                agent_id=self.name,
                trace_id=trace_id,
                message_summary="Forced requirements generation failure.",
                status="FAILURE",
                details={"input_text": content},
            )

        # Send response back to sender
        await self.send_message(
            recipient_id=sender_id,
            content=requirements_text,  # Content is directly the string
            context={"trace_id": trace_id},  # Propagate trace_id back
        )
        await log_agent_event(
            event_type="LLM_CALL_COMPLETE",  # New event type for LLM interactions
            agent_id=self.name,
            trace_id=trace_id,
            message_summary="LLM call for requirements generation completed.",
            status=status,
            duration_ms=int((llm_call_end - llm_call_start) * 1000),
            details={
                "llm_prompt": llm_prompt,
                "llm_response_snippet": requirements_text[:500],  # Log a snippet
            },
        )

        end_time = time.time()
        await log_agent_event(
            event_type="TASK_COMPLETE",
            agent_id=self.name,
            trace_id=trace_id,
            message_summary=f"Generated requirements and sent to {sender_id}: {requirements_text[:100]}...",
            status=status,
            duration_ms=int((end_time - start_time) * 1000),
            details={"generated_requirements": requirements_text},
        )
        print(f"{self.name}: Finished and sent requirements.")
