# Gemini Enterprise Agent Platform - Implementation Guide

This is a hands-on, step-by-step implementation guide for the current **Google Cloud Agent Platform** experience. It follows the Agent Platform console areas shown under **Build**, **Scale**, **Govern**, and **Optimise**, while still using the underlying SDK/API names where Google Cloud exposes them, such as Agent Engine and `aiplatform`.

You will build one realistic system end-to-end: an **Enterprise Support Assistant** that uses ADK, Agent Platform MCP servers, RAG Engine, Vector Search, Sessions, Memory Bank, Deployments, governance controls, and Evaluation.

## How to use this guide

Follow the sections in order. Each file is self-contained and ends with a "What you should have now" checklist - finish it before moving to the next.

The guide maps to the Agent Platform console like this:

| Agent Platform area | Console items covered |
|---|---|
| **Build** | Agent Garden, ADK, MCP servers, RAG Engine, Vector Search, Search, Models |
| **Scale** | Deployments, Memory Bank, Sessions |
| **Govern** | Agent Registry, Policies, Gateways, Security |
| **Optimise** | Topology, Evaluation |

| # | File | Pillar | What you build |
|---|------|--------|----------------|
| 01 | [`01_prerequisites.md`](01_prerequisites.md) | Foundation | Accounts, IAM roles, software you need installed |
| 02 | [`02_project_setup.md`](02_project_setup.md) | Foundation | GCP project, APIs, staging bucket, SDKs |
| 03 | [`03_model_garden.md`](03_model_garden.md) | Build | Models, Model Garden, tuning, model evaluation |
| 04 | [`04_agent_studio.md`](04_agent_studio.md) | Build / Govern | Register an Agent Engine agent in Gemini Enterprise |
| 05 | [`05_adk_basics.md`](05_adk_basics.md) | Build | ADK and Agent Garden orientation |
| 06 | [`06_mcp_servers.md`](06_mcp_servers.md) | Build | Agent Platform MCP servers and ADK registry access |
| 07 | [`07_rag_grounding.md`](07_rag_grounding.md) | Build | RAG Engine, Vector Search, and Search |
| 08 | [`08_memory_bank.md`](08_memory_bank.md) | Scale | Sessions and Memory Bank |
| 09 | [`09_multi_agent.md`](09_multi_agent.md) | Build | Multi-agent orchestration and A2A concepts |
| 10 | [`10_deployment.md`](10_deployment.md) | Scale | Deployments and runtime scaling |
| 11 | [`11_governance.md`](11_governance.md) | Govern | Agent Registry, Policies, Gateways, Security |
| 12 | [`12_optimization.md`](12_optimization.md) | Optimise | Topology, Evaluation, simulation, observability |
| 13 | [`13_distribution.md`](13_distribution.md) | Distribute | Surface in the Gemini Enterprise web app |
| 14 | [`14_checklist_and_cleanup.md`](14_checklist_and_cleanup.md) | - | Final E2E checklist and resource cleanup |

## Primary references

- Gemini Enterprise: https://docs.cloud.google.com/gemini/enterprise/docs
- Gemini Enterprise agents: https://docs.cloud.google.com/gemini/enterprise/docs/agents-overview
- Agent Runtime (Agent Engine): https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
- Agent Engine Sessions: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview
- Memory Bank: https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/overview
- Agent Registry for ADK: https://adk.dev/integrations/agent-registry/
- ADK docs: https://google.github.io/adk-docs/
- Model Armor: https://docs.cloud.google.com/model-armor
- Gen AI Evaluation: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview

Ready? Open <a href="./01_prerequisites.md">01_prerequisites.md</a> to start.
