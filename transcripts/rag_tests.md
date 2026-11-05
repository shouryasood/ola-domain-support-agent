# Part 1 RAG demonstrations

## Query: How are support tickets prioritized?

Answer: # Ticket priority classification
    
    Assign priority based on urgency, customer impact, and the number of people affected. Record the reason for the selected priority in the ticket. # Ticket data retention
    
    Retain support tickets only for the documented operational and legal retention period. # SLA by severity
    
    Measure the response target from ticket creation to the first meaningful support response.

Sources: ['ticket_priority', 'data_retention', 'sla_policy']

Top similarity: 0.630744

Fallback: False

## Query: What are the response targets by severity?

Answer: # SLA by severity
    
    Measure the response target from ticket creation to the first meaningful support response. Escalate when the earlier remedy failed or repeated reports suggest a broader service problem. Holiday staffing may extend ordinary response targets, and the customer should be told when a delay is expected. Critical issues should receive an initial response within one hour, high-priority issues within four hours, and standard issues within one business day.

Sources: ['sla_policy', 'repeat_complaints', 'business_hours']

Top similarity: 0.600182

Fallback: False

## Query: When should support escalate a ticket?

Answer: Escalate threats of harm immediately and note the behaviour in the ticket. # Escalation matrix
    
    Escalate a ticket when it affects safety, blocks an essential service, or remains unresolved beyond its target. Escalated means the ticket has been handed to a specialist team or a support lead. # SLA breach handling
    
    When a ticket is likely to miss its response or resolution target, notify the customer before the target passes.

Sources: ['abusive_customer_handling', 'escalation_matrix', 'ticket_status_definitions', 'sla_breach_handling']

Top similarity: 0.708150

Fallback: False

## Query: How does a customer request refund review?

Answer: # Refund and compensation
    
    A refund review requires a ticket reference and a description of the service problem. Agents must not promise a refund before an authorized reviewer confirms eligibility. # Refund processing timelines
    
    An approved refund returns to the original payment method unless the policy allows another option. Apply the same refund and privacy rules used for other customers.

Sources: ['refund_compensation', 'refund_timelines', 'vip_handling']

Top similarity: 0.589640

Fallback: False

## Query: Which channel should be used for account-specific updates?

Answer: # Customer communication channels
    
    Use the customer's authenticated in-app support thread as the primary channel for account-specific updates. Tell the customer that the bank decision is outside support control and that updates will follow once the payments team responds. Use the approved status channel for broad updates and the authenticated support thread for individual cases. A safety concern or widespread service failure receives the highest priority, while a single-account question with a working workaround receives a lower priority.

Sources: ['communication_channels', 'chargeback_handling', 'outage_communication', 'ticket_priority']

Top similarity: 0.591528

Fallback: False

## Query: What is the capital of France?

Answer: I don't know based on the available support policies.

Sources: []

Top similarity: 0.156447

Fallback: True

