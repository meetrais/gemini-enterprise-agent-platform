# 04 - Build a low-code agent in Agent Designer

Gemini Enterprise includes **Agent Designer**, a no-code and low-code builder for creating single-step and multi-step agents inside a Gemini Enterprise app. Use this section as a low-code prototype path. The code-first path starts in section 5 with ADK.

In this section you'll build the **Triage Agent**: a small classifier that reads an incoming support message and assigns it to `billing`, `technical`, `account`, or `general`.

```powershell
cd $HOME\agent-platform-demo
. .\set-env.ps1
```

```bash
cd "$HOME/agent-platform-demo"
source ./set-env.sh
```

## 4.1 Open Agent Designer

1. In the Google Cloud console, go to **Gemini Enterprise**.
2. Open the Gemini Enterprise app you want to use.
3. Go to **Agents** and choose **Create agent** or **Agent Designer**.
4. If prompted, select the app region and complete the setup flow.

Agent Designer is a Preview feature in the public docs, so labels can shift. If your UI differs, look for the flow that creates a custom agent from a prompt or from the visual flow builder.

## 4.2 Create the triage agent

Create a new single-step agent with these details:

- **Name:** `Support Triage Agent`
- **Description:** `Classifies inbound support messages into billing, technical, account, or general.`
- **Starter prompt:** `Classify a support ticket`

Use this instruction:

```text
You are the Triage Agent for ACME Customer Support. Read the user's
message and classify it into exactly one category:
- billing: charges, refunds, invoices, payment methods
- technical: errors, outages, integration problems, bugs
- account: login, email change, MFA, profile
- general: greetings, sales questions, anything else

Return strict JSON only:
{
 "category": "<billing|technical|account|general>",
 "confidence": <number from 0.0 to 1.0>,
 "reason": "<one short sentence>"
}

Do not include markdown fences. Do not include any other text.
```

If the builder asks for a model, choose `gemini-2.5-flash` or the newest Flash model available in your project.

## 4.3 Add structured output

If Agent Designer offers structured output or JSON schema validation, use this schema:

```json
{
 "type": "object",
 "required": ["category", "confidence", "reason"],
 "properties": {
 "category": {
 "type": "string",
 "enum": ["billing", "technical", "account", "general"]
 },
 "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
 "reason": { "type": "string" }
 }
}
```

If your UI doesn't expose schema validation yet, keep the instruction strict and use the tests below to catch malformed output.

## 4.4 Test the agent

Use the preview or test panel and try:

```text
Why did you charge me $40 instead of $20 in March?
```

Expected category: `billing`

Try a few more:

- `My API keeps returning 503 errors since this morning.` -> `technical`
- `Hi! Just wanted to say thanks for the great product.` -> `general`
- `Can you change my login email to a new address?` -> `account`

If a classification is wrong, tighten the instruction with another example rather than adding a long policy document here. The full policy grounding happens in section 7.

## 4.5 Save and share

Save the agent in your Gemini Enterprise app. In the Agent Gallery, it should appear under your custom or organization agents, depending on your permissions and sharing settings.

If your organization allows sharing custom agents, grant access only to the group that needs this prototype. The production ADK agent is registered and shared later in section 13.

## 4.6 Optional: turn the prototype into ADK requirements

Agent Designer is useful for stakeholder iteration, but keep the production path in source control. Capture these items for section 5:

- Final name and description
- Final instruction
- Example inputs and expected categories
- Any structured output schema
- Any tool or data source the prototype needs

Those become the initial ADK agent instruction, tests, and eval rows.

---

## What you should have now

- ✅ A working triage prototype in Agent Designer.
- ✅ At least 5 test prompts with expected categories.
- ✅ The final instruction saved for the ADK implementation.
- ✅ A decision on whether this stays a no-code helper or moves into the production ADK path.

Move on to **[`05_adk_basics.md`](05_adk_basics.md)**.
