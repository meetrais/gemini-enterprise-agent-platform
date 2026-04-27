\# Troubleshooting Persistent 503 Errors



If a customer reports persistent 503 errors:



1\. Check status.acme.example.com for active incidents.

2\. Verify the customer's API key is on the correct plan tier (Free keys are

&#x20;throttled at 100 events/day).

3\. Have them retry with exponential backoff. Our gateway will accept retries

&#x20;from 1s to 60s.

4\. If still failing, escalate to L2 with the customer's account ID and a

&#x20;sample of the failed request IDs.

