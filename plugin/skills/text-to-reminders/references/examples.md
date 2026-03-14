# Text-to-Reminders: Worked Examples

## Example 1: Dense Project Email

**Source text:**
> Hi Sam, following up on our call. A few things: can you send the updated spec to the team by Thursday? Also we need the vendor contract signed before we can kick off — legal is waiting on your redlines. And don't forget the demo is Friday at 2pm, you're presenting the new onboarding flow. Let me know if you need anything. - Priya

**Raw extraction:**
1. Send updated spec to team — by Thursday
2. Redline vendor contract — legal is waiting, no hard date
3. Demo presentation Friday 2pm — present new onboarding flow

**Consolidation reasoning:** All three are distinct tasks with different deadlines and different types of work. Keep separate.

**Proposed reminders:**

| Title | Due | Notes |
|-------|-----|-------|
| Send updated spec to team | Thursday | Per Priya. Send to full team. |
| Redline vendor contract | (this week) | Legal (Priya's team) is blocked waiting. No hard date given but urgent. |
| Present new onboarding flow at demo | Friday 2pm | Priya's project demo. Presenting onboarding flow specifically. |

---

## Example 2: Slack Thread with Scattered Tasks

**Source text:**
> [Alice] hey can you review the PR before EOD?
> [Alice] also the staging deploy is broken, someone needs to look at it
> [Bob] I can take the deploy
> [Alice] @sam also reminder that the retro doc needs to be filled out by Friday, it's in Notion
> [Alice] and we still need to schedule the 1:1 catchup we missed last week

**Filtering:** Bob claimed the staging deploy — not Sam's task. Alice's retro doc and 1:1 are Sam's.

**Raw extraction:**
1. Review Alice's PR — by EOD today
2. Fill out retro doc in Notion — by Friday
3. Schedule missed 1:1 with Alice — no hard date

**Consolidation:** Items 2 and 3 both involve Alice but are unrelated tasks — keep separate.

**Proposed reminders:**

| Title | Due | Notes |
|-------|-----|-------|
| Review Alice's PR | Today | EOD deadline. Check Slack for PR link. |
| Fill out retro doc | Friday | In Notion. Alice's reminder in Slack thread. |
| Schedule 1:1 with Alice | (none) | Missed last week's. Reach out to reschedule. |

---

## Example 3: Over-extracted (Bad) vs Consolidated (Good)

**Source text:**
> Please review the Q1 budget report, add your comments, check the headcount numbers, verify the travel expenses, confirm the software subscriptions are correct, and send back to finance by March 31.

**Bad (over-extracted):**
1. Review Q1 budget report
2. Add comments to Q1 budget report
3. Check headcount numbers in Q1 budget report
4. Verify travel expenses in Q1 budget report
5. Confirm software subscriptions in Q1 budget report
6. Send Q1 budget report to finance

Six reminders for one deliverable — this is noise.

**Good (consolidated):**

| Title | Due | Notes |
|-------|-----|-------|
| Review and return Q1 budget report to finance | March 31 | Check: comments, headcount numbers, travel expenses, software subscriptions. Send back to finance when done. |

---

## Example 4: Ambiguous Date Handling

**Source text:**
> We need this wrapped up soon. End of quarter at the latest, but ideally next week.

**Interpretation:**
- "End of quarter" → March 31 (current quarter)
- "Ideally next week" → soft target, not a hard deadline

**In proposal, show interpretation explicitly:**
> Due: March 31 (end of quarter — interpreted from "end of quarter at the latest"; soft target is next week Mar 17)

This lets the user correct the interpretation before creating.

---

## Example 5: Meeting Notes

**Source text:**
> Action items from design sync Mar 14:
> - Sam: update Figma mockups with new brand colors by next Monday
> - Sam: share mockup link with stakeholders after update
> - Jake: write copy for onboarding screens (Sam to review when ready)
> - Sam: book room for next design sync

**Filtering:** Jake's copy item is not Sam's task directly — but Sam needs to review it when ready. Capture as a follow-up, not a primary task.

**Consolidation:** Figma update + share link are sequential sub-tasks of the same deliverable.

**Proposed reminders:**

| Title | Due | Notes |
|-------|-----|-------|
| Update Figma mockups with new brand colors | Monday Mar 17 | Then share link with stakeholders. Both steps from design sync Mar 14. |
| Review Jake's onboarding copy | (none) | Waiting on Jake. Follow up when he says it's ready. |
| Book room for next design sync | (none) | Recurring — check calendar for next sync date first. |
