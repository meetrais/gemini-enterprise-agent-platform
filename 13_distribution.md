# 13 - Distribute via the Gemini Enterprise app

The **Gemini Enterprise web app** is the employee-facing front door. Admins can register supported custom agents, including ADK agents hosted on Vertex AI Agent Engine, and share them with the right users. The app also includes:

- **Agent Designer** - a no-code builder for non-developers.
- **Agent Gallery** - a place to browse available Google, organization, and personal agents.
- **Inbox** - a central location to monitor long-running agent tasks.

This section publishes your support assistant to the right audience and shows how to extend it via Agent Designer and Agent Gallery.

```powershell
PS> cd $HOME\agent-platform-demo
PS> . .\set-env.ps1
```

```bash
$ cd "$HOME/agent-platform-demo"
$ source ./set-env.sh
```

## 13.1 Make sure you have a Gemini Enterprise license

Before this section will fully work:

1. Console -> **Gemini Enterprise**.
2. If you don't have an app or license, follow the setup flow or contact your Google Cloud administrator.
3. Wait a few minutes for the license to provision.
4. Refresh - the **Admin** sidebar entry should appear.

## 13.2 Register the Agent Engine agent

1. Console -> **Gemini Enterprise**.
2. Open the app that should contain the agent.
3. Click **Agents -> Add agents**.
4. Choose **Custom agent via Agent Engine**.
5. Enter the Agent Engine resource path from section 10.

A configuration panel opens.

## 13.3 Configure the agent for users

Fill in the configuration panel:

- **Display name in app:** `ACME Support`
- **Short description:** `Get answers fast on billing, technical, and account questions.`
- **Long description:** A paragraph explaining what the agent can do, with sample prompts.
- **Icon:** upload a 256x256 PNG, or pick from the icon library.
- **Color theme:** match brand colors.
- **Starter prompts** (3 - 5 - these appear as buttons in the chat UI):
 - "Why was I charged twice?"
 - "My API is throwing 503s"
 - "How do I change my email?"
 - "What's the difference between Pro and Enterprise?"
- **Audience:** select which Google Group, OU, or list of emails can see this agent. For internal-only, pick `support-team@acme.com`. For company-wide, pick `all-employees@acme.com`.
- **Inbox enabled:** ON. This lets users monitor long-running runs from the Inbox panel.
- **Sharing:** allow users to share conversations with colleagues, OR restrict for sensitive PII flows.
- **Citations:** ON. The app will show source documents from RAG retrievals next to each response.

Click **Publish**.

## 13.4 Verify the agent shows up

1. Copy the Gemini Enterprise web app URL from the app dashboard in the Google Cloud console.
2. Sign in with your work account.
3. Open **Agents** or **Agent Gallery**.
4. You should see **ACME Support** in the list.
5. Click it. Try a starter prompt.

If the agent doesn't appear:

- The audience setting may not include your account.
- Cache - sign out and back in.
- License - make sure your account has a Gemini Enterprise seat assigned.

## 13.5 Inbox for long-running tasks

For tasks that take minutes (deep research, multi-step automation), the agent can run asynchronously. Users see them in the **Inbox**.

In your agent code, mark a sub-agent or workflow as long-running:

```python
from google.adk.agents import Agent

deep_research_agent = Agent(
 name="deep_research_agent",
 model="gemini-2.5-pro",
 instruction="...",
 tools=[google_search, search_kb, code_execution],
 long_running=True, # surfaced in Inbox
 estimated_duration_seconds=600,
)
```

When triggered, the agent emits status updates to the user's Inbox; users can navigate away and come back to see the result.

## 13.6 Agent Designer - no-code agents for end users

The Gemini Enterprise app includes **Agent Designer**, a natural-language no-code builder. Admins can control whether end users are allowed to create their own agents.

Walk an end user through it:

1. In the Gemini Enterprise app, open the agent creation flow.
2. **Agent Designer** opens with a chat-style prompt: *"Describe what your agent should do."*
3. Example: "Every Monday at 9am, summarize last week's support tickets from ServiceNow grouped by category, and email me the result."
4. Designer generates a draft agent that includes:
 - The required MCP tools (ServiceNow, Gmail).
 - A schedule trigger.
 - The summarization prompt.
5. The user reviews the draft, adjusts, and clicks **Save**.
6. The agent is saved in the app and governed by the app's sharing and admin controls.

This is how the platform scales to hundreds of agents per company without IT becoming the bottleneck.

## 13.7 Agent Gallery and marketplace agents

Agent Gallery is where users discover agents made by Google, agents shared by your organization, and their own Agent Designer agents. Marketplace A2A agents can also be added by admins where available.

1. In the Gemini Enterprise app, open **Agents** or **Agent Gallery**.
2. Review the available Google-made, organization, and personal agents.
3. For marketplace A2A agents, follow the current admin flow in the Google Cloud console.
4. Set the audience carefully before sharing.

Do not assume every agent shares the same runtime controls. Review the specific docs and OAuth scopes for each partner or marketplace agent.

## 13.8 Mix agents into Workspace

If your org uses Google Workspace:

1. Console -> **Workspace Admin -> Apps -> Google Workspace -> Gemini Enterprise**.
2. Enable Gemini Enterprise for selected OUs / groups.
3. Configure data-access policies (which agents can read which Drive folders, Gmail labels, etc.).
4. Users can now invoke ACME Support from the side panel of Gmail, Docs, Sheets, Meet.

## 13.9 Branding and custom domains

Standard / Plus customers can:

- Upload a custom logo and color palette (Console -> **Gemini Enterprise -> Admin -> Branding**).
- Set a custom welcome message.
- Configure the app to be available at a vanity URL (e.g., `gemini.acme.example.com`).

## 13.10 Train your users

Distribution isn't just publishing; it's adoption. Two artifacts to produce:

1. **A short video or doc** showing 3 example queries the agent handles well.
2. **An "escape hatch"** - make sure users know how to get to a human, and that the agent's "I'll escalate" response actually creates a ticket somewhere.

## 13.11 Iterate based on real traffic

Hook the same dashboard from section 12 to a "user satisfaction" metric:

- Add a thumbs-up / thumbs-down on each response (the app supports this natively).
- Periodically pull dissatisfied conversations from the audit log into your eval set.
- Retune the relevant agent's instruction or KB.
- Re-run section 12.B's Auto SxS to confirm improvement.
- Ship.

This is the real long-term operating loop.

---

## What you should have now

- ✅ A Gemini Enterprise license active on your project.
- ✅ `support-assistant-prod` registered with the Gemini Enterprise app.
- ✅ Display name, icon, starter prompts, audience all configured.
- ✅ You've used the agent yourself from the Gemini Enterprise web app URL.
- ✅ (Optional) An Inbox-enabled long-running sub-agent.
- ✅ (Optional) A no-code agent built in Agent Designer to demonstrate the user path.
- ✅ (Optional) A marketplace or A2A agent reviewed and shared with the right audience.
- ✅ (Optional) Workspace integration enabled for your audience.

Move on to **`14_checklist_and_cleanup.md`** for final verification and cleanup.
