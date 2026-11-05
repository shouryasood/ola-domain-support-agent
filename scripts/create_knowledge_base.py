from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB_DIR = ROOT / "knowledge_base"

DOCUMENTS = {
    # ------------------------------------------------------------------
    # 1. ORIGINAL 12 REQUIRED TOPICS (unchanged)
    # ------------------------------------------------------------------
    "ticket_priority.md": """\
    # Ticket priority classification
    
    Assign priority based on urgency, customer impact, and the number of people affected. A safety concern or widespread service failure receives the highest priority, while a single-account question with a working workaround receives a lower priority. Record the reason for the selected priority in the ticket.
    """,
    "sla_policy.md": """\
    # SLA by severity
    
    Measure the response target from ticket creation to the first meaningful support response. Critical issues should receive an initial response within one hour, high-priority issues within four hours, and standard issues within one business day. Resolution time depends on investigation needs, and the agent should update the customer if the target cannot be met.
    """,
    "escalation_matrix.md": """\
    # Escalation matrix
    
    Escalate a ticket when it affects safety, blocks an essential service, or remains unresolved beyond its target. Send operational incidents to the on-call support lead and policy disputes to the designated policy owner. Record the reason, time, and receiving team in the ticket.
    """,
    "refund_compensation.md": """\
    # Refund and compensation
    
    A refund review requires a ticket reference and a description of the service problem. Support checks the trip or transaction record and the applicable policy before recommending an adjustment. Agents must not promise a refund before an authorized reviewer confirms eligibility.
    """,
    "communication_channels.md": """\
    # Customer communication channels
    
    Use the customer's authenticated in-app support thread as the primary channel for account-specific updates. Email may be used for a receipt or follow-up when the customer has verified that address. Never ask customers to send passwords, one-time codes, or full payment credentials in a support message.
    """,
    "business_hours.md": """\
    # Business hours and holiday support
    
    Handle standard policy questions during published support business hours. Safety-related reports and major service incidents follow the on-call escalation process outside those hours. Holiday staffing may extend ordinary response targets, and the customer should be told when a delay is expected.
    """,
    "repeat_complaints.md": """\
    # Repeat complaint handling
    
    When a customer reports the same unresolved issue again, link the new contact to the earlier ticket and review previous actions. Do not close a repeat complaint solely because a prior ticket exists. Escalate when the earlier remedy failed or repeated reports suggest a broader service problem.
    """,
    "service_credits.md": """\
    # Service credit policy
    
    Consider a service credit only after the incident and customer impact have been verified. The credit amount must follow approved adjustment limits and be recorded with its reason. A credit is not a substitute for addressing an unresolved safety or access issue.
    """,
    "feedback_collection.md": """\
    # Feedback collection
    
    After a support case is resolved, invite the customer to provide optional feedback through the approved survey channel. Store feedback with the case reference and use it to identify recurring service problems. Do not make service eligibility depend on completing a survey.
    """,
    "vip_handling.md": """\
    # VIP customer handling
    
    A VIP designation changes routing and response attention but does not bypass identity checks or safety procedures. Route VIP cases to the designated queue and record the handling reason. Apply the same refund and privacy rules used for other customers.
    """,
    "outage_communication.md": """\
    # Outage communication
    
    During a confirmed outage, share only verified information about the affected service, current impact, and next update time. Use the approved status channel for broad updates and the authenticated support thread for individual cases. Correct earlier messages promptly when incident facts change.
    """,
    "data_retention.md": """\
    # Ticket data retention
    
    Retain support tickets only for the documented operational and legal retention period. Restrict access to staff who need a record for support, audit, or approved incident review. When the retention period ends, delete or de-identify the ticket according to the retention procedure.
    """,
    # ------------------------------------------------------------------
    # 2. TICKET LIFECYCLE
    # ------------------------------------------------------------------
    "ticket_status_definitions.md": """\
    # Ticket status definitions
    
    A ticket is Open when it has been created but no agent has started work on it. It becomes In Progress once an agent is investigating or waiting on a verified reply from the customer. Escalated means the ticket has been handed to a specialist team or a support lead. Resolved means an answer or fix has been delivered, and Closed means the customer confirmed the outcome or the reopen window ended without a reply.
    """,
    "ticket_reopening.md": """\
    # Reopening a resolved ticket
    
    A customer may reopen a Resolved ticket by replying within the published reopen window. A reopened ticket returns to In Progress and keeps its original reference, history, and priority review. If the window has already ended, create a new ticket and link it to the closed one.
    """,
    "ticket_closure.md": """\
    # Ticket closure criteria
    
    Close a ticket only after the customer has confirmed the outcome or the reopen window has passed with no reply. Before closing, check that the resolution notes explain what was done and why. Never close a ticket that still has an open safety concern or a pending refund review.
    """,
    "duplicate_ticket_merging.md": """\
    # Merging duplicate tickets
    
    Merge tickets only when they describe the same issue for the same verified customer. Keep the oldest ticket as the primary record and copy relevant notes from the duplicate into it. Tell the customer which ticket reference remains active so that they do not lose track of the case.
    """,
    "internal_notes_handoff.md": """\
    # Internal notes and shift handoff
    
    Write internal notes so that another agent can continue the case without asking the customer to repeat details. Include actions already taken, information still needed, and the next planned step. Keep notes factual and free of personal opinions about the customer.
    """,
    # ------------------------------------------------------------------
    # 3. BILLING
    # ------------------------------------------------------------------
    "fare_dispute.md": """\
    # Fare dispute review
    
    When a customer questions a fare, compare the final charge with the estimated fare, the route taken, and any approved extra charges. Explain the fare components in plain language before offering any adjustment. If the charge looks incorrect, send the case to the billing review team with the trip reference.
    """,
    "duplicate_charge.md": """\
    # Duplicate charge handling
    
    Confirm that two charges belong to separate completed trips before treating them as a duplicate. If the same trip was charged twice, raise a billing correction request and tell the customer the reversal will follow the payment method's processing time. Do not promise an exact settlement date until the payment provider confirms it.
    """,
    "payment_failure.md": """\
    # Payment failure handling
    
    A failed payment can come from an expired method, insufficient balance, or a temporary provider error. Ask the customer to try another saved method or retry later, and never request full card details in the support thread. If money was deducted but the trip shows unpaid, open a billing investigation with the transaction reference.
    """,
    "refund_timelines.md": """\
    # Refund processing timelines
    
    An approved refund returns to the original payment method unless the policy allows another option. The time it takes depends on the payment method and the provider, so agents should share the published range instead of a guaranteed date. If the refund has not appeared after the published range, open a follow-up investigation.
    """,
    "cancellation_fees.md": """\
    # Cancellation fees
    
    A cancellation fee may apply when a rider cancels after a driver has been assigned and has started travelling to the pickup point. The fee is waived when the driver cancels, when the driver is far from the pickup point, or when the app showed a clear error. Agents should check the trip log before confirming or removing the fee.
    """,
    "wait_time_extra_charges.md": """\
    # Waiting time and extra charges
    
    Waiting time, tolls, parking, and airport fees are added to the fare only when they are shown as approved charges for the trip. Review the trip record to confirm the charge applies before explaining it to the customer. If an extra charge was added by mistake, send a correction request to billing.
    """,
    "promo_codes_wallet.md": """\
    # Promo codes and wallet balance
    
    A promo code applies only when the trip meets its published conditions and the code has not expired. If a valid code failed to apply, record the code and the trip reference and send the case for review. Wallet balance questions should be answered from the verified account record and never from the customer's memory alone.
    """,
    "surge_pricing_explanation.md": """\
    # Dynamic pricing explanation
    
    Dynamic pricing raises fares when demand in an area is higher than the number of available drivers. The app shows the price before the customer confirms the booking, so the agreed price should match the final fare unless the route or trip conditions changed. Agents should explain this clearly and avoid promising a discount.
    """,
    "invoice_receipts.md": """\
    # Invoices and trip receipts
    
    A trip receipt is generated after each completed trip and sent to the verified email on the account. Customers who need a tax invoice should receive it only for trips on their own verified account. Agents must not email invoices to an unverified address.
    """,
    "chargeback_handling.md": """\
    # Chargeback handling
    
    When a customer disputes a charge with their bank, send the case to the payments team and avoid issuing a second refund for the same charge. Gather the trip record and communication history to support the review. Tell the customer that the bank decision is outside support control and that updates will follow once the payments team responds.
    """,
    "driver_payout_issues.md": """\
    # Driver payout issues
    
    Check the payout status, the trip earnings record, and any deductions before answering a driver's payout question. Explain each deduction using the published earnings rules. If a completed trip is missing from earnings, open a payout correction request with the trip reference.
    """,
    # ------------------------------------------------------------------
    # 4. ACCOUNT ACCESS
    # ------------------------------------------------------------------
    "password_reset_recovery.md": """\
    # Password reset and account recovery
    
    Direct customers to the in-app reset flow, which sends a one-time code to the registered phone number or email. Agents never see, request, or set a customer's password. If the customer no longer has access to the registered contact, start the identity verification process.
    """,
    "otp_delivery_issues.md": """\
    # One-time code delivery problems
    
    If a code does not arrive, ask the customer to check network coverage, wait for the retry timer, and request a new code. Remind them that only the latest code works and that a code must never be shared with anyone. Repeated delivery failures should be reported to the technical team with the time of each attempt.
    """,
    "account_suspension.md": """\
    # Account suspension review
    
    A suspended account stays restricted until a review confirms the reason for the suspension. Tell the customer the general reason in neutral language and describe how to submit a review request. Agents must not reveal internal fraud signals or detection rules.
    """,
    "identity_verification.md": """\
    # Identity verification
    
    Verify identity before sharing account details or changing sensitive account information. Use only the approved verification steps in the support tool and never ask for documents through unsecured channels. If verification fails, explain the next available option without revealing which check failed.
    """,
    "phone_number_change.md": """\
    # Phone number change
    
    A phone number change must be requested from within the verified account or confirmed with a code sent to the existing number. If the old number is unavailable, the request goes through identity verification before any change is made. Confirm the update by messaging the new number and noting the change in the ticket.
    """,
    "account_deletion_request.md": """\
    # Account deletion requests
    
    Treat an account deletion request as a privacy request that needs identity verification. Explain what will be removed, what must be kept for legal or financial reasons, and how long the process takes. Close any pending refund or dispute before the deletion is finalized.
    """,
    # ------------------------------------------------------------------
    # 5. TECHNICAL ISSUES
    # ------------------------------------------------------------------
    "app_crash_troubleshooting.md": """\
    # App crash troubleshooting
    
    Ask the customer to update the app, restart the phone, and check available storage and network connection. If the crash continues, collect the app version, device model, and approximate time of the crash. Send repeated reports with the same details to the technical team as a possible app defect.
    """,
    "gps_location_issues.md": """\
    # Location and GPS problems
    
    Wrong pickup pins are often caused by disabled location permission, weak signal, or a very high accuracy setting turned off. Guide the customer to enable precise location and confirm the pin before booking. If the trip already started with a wrong pin, record the trip reference and review the route data.
    """,
    "booking_failure_no_driver.md": """\
    # Booking failures and driver unavailability
    
    If a booking fails or no driver is found, check whether the service is available in that area and time. Ask the customer to retry after a short wait or choose a different ride type. When many customers report the same failure, treat it as a possible service incident and notify the on-call lead.
    """,
    "route_deviation_complaint.md": """\
    # Route deviation complaints
    
    Compare the trip route with the expected route and any road closures noted at the time. Ask the customer what concerned them, and check the driver's explanation if one exists. A deviation that raises a safety concern follows the safety incident process instead of a fare review.
    """,
    "bug_report_intake.md": """\
    # Bug report intake
    
    When a customer describes an app problem, record the steps taken, what happened, what was expected, and the app version. Check whether the issue matches a known problem before creating a new engineering report. Give the customer the ticket reference and avoid promising a fix date.
    """,
    # ------------------------------------------------------------------
    # 6. PRODUCT DEFECT AND SAFETY
    # ------------------------------------------------------------------
    "vehicle_defect_report.md": """\
    # Vehicle defect reports
    
    A report about a vehicle fault, such as brakes, lights, or cleanliness, should include the vehicle details and the trip reference. Treat any defect that could affect safety as high priority and route it to the safety team immediately. Record the report so that repeated issues with the same vehicle can be identified.
    """,
    "safety_incident_handling.md": """\
    # Safety incident handling
    
    Treat any report of danger, harassment, or injury as a safety incident and escalate it immediately. Check first that the customer is safe and direct them to local emergency services when there is immediate danger. Document the facts neutrally and never ask the customer to prove the incident before action begins.
    """,
    "accident_reporting.md": """\
    # Accident reporting
    
    If a customer reports an accident during a trip, confirm that everyone is safe and advise contacting emergency services if needed. Open a safety ticket, attach the trip details, and send it to the incident response team. Avoid discussing fault or compensation until the review team has assessed the case.
    """,
    "driver_conduct_complaints.md": """\
    # Driver conduct complaints
    
    Record what happened, when, and the trip reference without questioning the customer's account. Forward the complaint to the conduct review team and tell the customer that the matter will be reviewed. Do not share the outcome of any disciplinary action with the customer.
    """,
    "rider_conduct_reports.md": """\
    # Rider conduct reports
    
    A driver may report unsafe or abusive behaviour by a rider with the trip reference and a short description. Review the report under the same standards used for driver complaints. Tell the driver that the report was received and that the outcome is handled by the conduct review team.
    """,
    "lost_and_found.md": """\
    # Lost and found items
    
    Help the customer submit the item description and the trip reference so the driver can be contacted. Do not give either side the other party's phone number directly and use the approved masked contact option instead. If the item cannot be recovered quickly, tell the customer the next available option.
    """,
    # ------------------------------------------------------------------
    # 7. GENERAL INQUIRY AND SERVICE QUALITY
    # ------------------------------------------------------------------
    "general_inquiry_handling.md": """\
    # General inquiry handling
    
    Answer general questions using the published help content and current policy documents only. If the answer is not in an approved source, say that it is unavailable instead of guessing. Offer to open a ticket when the question needs a specific account review.
    """,
    "rating_disputes.md": """\
    # Rating disputes
    
    Ratings reflect customer experience and are not changed on request. Review a rating dispute only when there is evidence of abuse, a technical error, or a policy breach connected to the rating. Tell the customer that the review focuses on the trip record and not on the rating alone.
    """,
    "accessibility_support.md": """\
    # Accessibility support
    
    Offer help for customers who need accessible vehicles, assistance with boarding, or alternate contact methods. Record the accessibility need on the ticket so the customer does not have to repeat it. If an accessible option is not available, explain the alternatives clearly and escalate when a need was not met on a past trip.
    """,
    "language_support.md": """\
    # Language support
    
    Reply in the language the customer uses when an approved translation resource is available. If the language is not supported, use simple and clear wording and offer a transfer to a team member who can help. Never use an unapproved tool that would expose customer data.
    """,
    # ------------------------------------------------------------------
    # 8. TRUST, PRIVACY AND AGENT CONDUCT
    # ------------------------------------------------------------------
    "fraud_scam_reporting.md": """\
    # Fraud and scam reporting
    
    Treat reports of unauthorized transactions, fake callers, or phishing messages as high priority. Advise the customer to secure the account, avoid sharing codes, and report suspicious calls to the proper authority. Send the case to the trust and safety team with the evidence supplied.
    """,
    "pii_handling_tickets.md": """\
    # Personal data handling in tickets
    
    Mask phone numbers and other personal identifiers when they are copied into notes or logs. Never store full payment card numbers or passwords in a ticket. Share personal data only with staff who need it to resolve the case.
    """,
    "agent_tone_conduct.md": """\
    # Agent tone and conduct
    
    Respond politely, clearly, and calmly, even when the customer is upset. Acknowledge the problem, explain the next step, and avoid blaming language. Never argue with a customer or make promises that policy does not allow.
    """,
    "abusive_customer_handling.md": """\
    # Abusive customer handling
    
    Stay professional and give one clear warning if the customer uses abusive or threatening language. Continue to help with the issue when the customer returns to respectful communication. Escalate threats of harm immediately and note the behaviour in the ticket.
    """,
    "legal_regulatory_requests.md": """\
    # Legal and regulatory requests
    
    Do not respond directly to legal notices, police requests, or regulator letters received through support. Forward them to the legal team with the ticket reference and note the time they arrived. Tell the sender that the request has been passed to the appropriate team.
    """,
    # ------------------------------------------------------------------
    # 9. SERVICE LEVEL FOLLOW-THROUGH
    # ------------------------------------------------------------------
    "sla_breach_handling.md": """\
    # SLA breach handling
    
    When a ticket is likely to miss its response or resolution target, notify the customer before the target passes. Record the reason for the delay and move the ticket to a team that can act sooner when necessary. Review every breached ticket to find process problems and prevent repeat delays.
    """,
}


def main() -> None:
    KB_DIR.mkdir(parents=True, exist_ok=True)

    for filename, text in DOCUMENTS.items():
        (KB_DIR / filename).write_text(text.strip() + "\n", encoding="utf-8")

    print(f"Wrote {len(DOCUMENTS)} policy documents to {KB_DIR}")


if __name__ == "__main__":
    main()
