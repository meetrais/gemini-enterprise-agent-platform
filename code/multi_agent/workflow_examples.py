"""Deterministic workflow-agent examples for section 09.

These objects are examples to inspect or import. They are not meant to replace
the router in agent.py because workflow agents are best for fixed pipelines.
"""

import os

from google.adk.agents import Agent, ParallelAgent, SequentialAgent


classifier_agent = Agent(
 name="ticket_classifier",
 model=os.environ.get("GOOGLE_GENAI_ROUTER_MODEL", "gemini-2.5-flash"),
 instruction=(
  "Classify the ticket as billing, technical, account, or other. Return only "
  "the category and one short reason."
 ),
)

responder_agent = Agent(
 name="ticket_responder",
 model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
 instruction="Draft a concise first response for the classified ticket.",
)

logger_agent = Agent(
 name="ticket_logger",
 model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
 instruction="Create a short internal support log entry for the ticket.",
)

ticket_pipeline = SequentialAgent(
 name="ticket_pipeline",
 sub_agents=[classifier_agent, responder_agent, logger_agent],
)

kb_search_agent = Agent(
 name="kb_search_agent",
 model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
 instruction="Search the internal knowledge you have and summarize relevant ACME guidance.",
)

web_search_agent = Agent(
 name="web_search_agent",
 model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
 instruction="Summarize relevant public context if the user asks for public facts.",
)

parallel_search = ParallelAgent(
 name="parallel_search",
 sub_agents=[kb_search_agent, web_search_agent],
)

