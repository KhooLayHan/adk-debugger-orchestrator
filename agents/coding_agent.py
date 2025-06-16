# import asyncio
# from google.adk.agents import Agent, AgentMessage, MessageContent

# from .utils import llm, log_agent_event


# class CodingAgent(Agent):
#     def __init__(self, name: str):
#         super().__init__(
#             name=name,
#             llm=llm,  # Use the shared LLM instance
#             description="Writes production-ready code based on requirements.",
#             instruction="You are a senior software engineer. Write clean, efficient, and well-commented Python code based on the provided requirements. Respond with only the code, no preamble or explanation.",
#         )

#     async def handle_message(self, message: AgentMessage):
#         trace_id = message.context.get("trace_id", "UNKNOWN TRACE")

#         await log_agent_event(
#             event_type="AGENT_START",
#             agent_id=self.name,
#             trace_id=trace_id,
#             message_summary=f"Received requirements for coding: {message.content.text[:100]}...",
#             source_agent_id=message.sender_id,
#             details={"input requirements": message.content.text},
#         )
#         print(f"Coding Agent: Processing requirements: {message.content.text}")

#         # Simulate processing time
#         await asyncio.sleep(5) # Even longer delay

#         # Use LLM to generate code
#         llm_response = await self.llm.generate_text(
#             prompt=f"Write Python code for the following requirements: Respond ONLY with the code:\n{message.content.text}\n\nExample: def fibonacci(n):\n  # Implementation"
#         )
#         generated_code = llm_response.text
#         if not generated_code:
#             generated_code = (
#                 "No code generated. Requirements might be unclear."  # Fallback
#             )

#         # Simulate a potential failure based on keyword
#         status = "SUCCESS"
#         if "force_code_fail" in message.content.text.lower():
#             generated_code = "ERROR: Code generation failed due to forced error."
#             status = "FAILURE"
#             await log_agent_event(
#                 event_type="ERROR",
#                 agent_id=self.name,
#                 trace_id=trace_id,
#                 message_summary="Forced code generation failure.",
#                 status="FAILURE",
#                 details={"input_text": message.content.text},
#             )

#         response_content = MessageContent(text=generated_code)
#         await self.send_message(
#             recipient=message.sender_id,
#             content=response_content,
#             context={"trace_id": trace_id},  # Propagate trace_id back
#         )

#         await log_agent_event(
#             event_type="TASK_COMPLETE",
#             agent_id=self.name,
#             trace_id=trace_id,
#             message_summary=f"Generated code: {generated_code[:100]}...",
#             status=status,
#             details={"generated_code": generated_code},
#         )
#         print("Coding Agent: Finished and sent code.")

# agents/coding_agent.py
import time  # For measuring duration

import asyncio
from google.adk.agents import Agent  # type: ignore

from .utils import llm_model, log_agent_event  # Use llm_model instead of llm


class CodingAgent(Agent):
    """
    The CodingAgent is responsible for writing production-ready code
    based on provided requirements, using a Large Language Model.
    """

    def __init__(self, name: str):
        """
        Initializes the CodingAgent.

        Args:
            name (str): The unique name of the agent.
        """
        super().__init__(
            name=name,
            llm=llm_model,  # Pass the GenerativeModel instance
            description="Writes production-ready code based on requirements.",
            instruction="You are a senior software engineer. Write clean, efficient, and well-commented Python code based on the provided requirements. Respond ONLY with the code, no preamble or explanation.",
        )

    async def handle_message(self, content: str, sender_id: str, context: dict):
        """
        Handles incoming messages, processes the requirements to generate code,
        and sends the generated code back to the sender.

        Args:
            content (str): The text content of the message, which contains the requirements.
            sender_id (str): The ID of the agent that sent the requirements.
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
            message_summary=f"Received requirements for coding from {sender_id}: {content[:100]}...",
            source_agent_id=sender_id,
            details={"input_requirements": content},
        )
        print(f"{self.name}: Processing requirements from {sender_id}: {content}")

        # Simulate processing time
        await asyncio.sleep(1)  # Shorter delay for LLM calls

        # Use LLM to generate code
        llm_prompt = f"{self.instruction}\n\nRequirements:\n{content}\n\nExample: def fibonacci(n):\n    # implementation"
        llm_call_start = time.time()
        try:
            # For google-generativeai, it's model.generate_content
            llm_response = await self.llm.generate_content(llm_prompt)
            generated_code = llm_response.text
        except Exception as e:
            generated_code = f"ERROR: LLM failed to generate code: {e}"
            print(f"LLM Error in {self.name}: {e}")
        llm_call_end = time.time()

        if not generated_code.strip():
            generated_code = "# No code generated. Requirements might be unclear or LLM issue."  # Fallback

        # Simulate a potential failure based on keyword
        status = "SUCCESS"
        if "force_code_fail" in content.lower():
            generated_code = "ERROR: Code generation failed due to forced error."
            status = "FAILURE"
            await log_agent_event(
                event_type="ERROR",
                agent_id=self.name,
                trace_id=trace_id,
                message_summary="Forced code generation failure.",
                status="FAILURE",
                details={"input_text": content},
            )

        # Send response back to sender
        await self.send_message(
            recipient_id=sender_id,
            content=generated_code,  # Content is directly the string
            context={"trace_id": trace_id},  # Propagate trace_id back
        )
        await log_agent_event(
            event_type="LLM_CALL_COMPLETE",  # New event type for LLM interactions
            agent_id=self.name,
            trace_id=trace_id,
            message_summary="LLM call for code generation completed.",
            status=status,
            duration_ms=int((llm_call_end - llm_call_start) * 1000),
            details={
                "llm_prompt": llm_prompt,
                "llm_response_snippet": generated_code[:500],  # Log a snippet
            },
        )

        end_time = time.time()
        await log_agent_event(
            event_type="TASK_COMPLETE",
            agent_id=self.name,
            trace_id=trace_id,
            message_summary=f"Generated code and sent to {sender_id}: {generated_code[:100]}...",
            status=status,
            duration_ms=int((end_time - start_time) * 1000),
            details={"generated_code": generated_code},
        )
        print(f"{self.name}: Finished and sent code.")
