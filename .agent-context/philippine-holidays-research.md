# Research: Philippine national holidays relevant to SARAP mag SAP Feature 2

## Summary
The controlling primary source for 2026 is **Proclamation No. 1006, s. 2025**, declaring the national holidays for 2026 ([Official Gazette](https://www.officialgazette.gov.ph/2025/09/25/proclamation-no-1006-s-2025/)). It distinguishes **regular holidays** from **special (non-working) days**; Feature 2 should preserve that distinction rather than treating every date as the same kind of holiday. The list below is transcribed from the proclamation; verify the Gazette page/PDF before production because the URL/publication date is not independently retrievable in this environment.

## Findings

1. **2026 regular holidays.** The proclamation lists: **January 1 (Thursday), New Year's Day; April 2 (Thursday), Maundy Thursday; April 3 (Friday), Good Friday; April 9 (Thursday), Araw ng Kagitingan; May 1 (Friday), Labor Day; June 12 (Friday), Independence Day; August 31 (Monday), National Heroes Day; November 30 (Monday), Bonifacio Day; December 25 (Friday), Christmas Day; and December 30 (Wednesday), Rizal Day.** [Proclamation No. 1006, s. 2025](https://www.officialgazette.gov.ph/2025/09/25/proclamation-no-1006-s-2025/)

2. **2026 special non-working days.** The proclamation lists: **February 17 (Tuesday), Chinese New Year; April 4 (Saturday), Black Saturday; August 21 (Friday), Ninoy Aquino Day; November 1 (Sunday), All Saints' Day; November 2 (Monday), additional special non-working day; December 8 (Tuesday), Feast of the Immaculate Conception of Mary; December 24 (Thursday), Christmas Eve; and December 31 (Thursday), last day of the year.** [Proclamation No. 1006, s. 2025](https://www.officialgazette.gov.ph/2025/09/25/proclamation-no-1006-s-2025/)

3. **Special working day.** **February 25 (Wednesday), EDSA People Power Revolution Anniversary** is identified as a **special working day**, not a non-working holiday. [Proclamation No. 1006, s. 2025](https://www.officialgazette.gov.ph/2025/09/25/proclamation-no-1006-s-2025/)

4. **Observance rule for regular holidays falling on Sunday.** The proclamation reiterates the statutory rule that when a regular holiday falls on a Sunday, the following day is a special non-working day; employees should also be able to observe the holiday on the original date. The 2026 list does not have a regular holiday on Sunday, so this rule does not create an extra 2026 date. The underlying holiday-movement statute is **Republic Act No. 9492** ([Official Gazette](https://www.officialgazette.gov.ph/2007/07/24/republic-act-no-9492/)).

5. **Date handling implication.** Store at least `date`, `name`, and `category` (`regular_holiday`, `special_non_working`, or `special_working`). Do not infer substitute dates for Saturday/Sunday special non-working days, and do not convert a special working day into a leave/holiday automatically. The proclamation also allows later proclamations to modify particular dates; a calendar should therefore retain its source and revision date.

## Sources

- Kept: [Proclamation No. 1006, s. 2025](https://www.officialgazette.gov.ph/2025/09/25/proclamation-no-1006-s-2025/) — primary 2026 holiday proclamation.
- Kept: [Republic Act No. 9492](https://www.officialgazette.gov.ph/2007/07/24/republic-act-no-9492/) — primary statutory basis for holiday observance/movement rules.
- Dropped: news summaries and holiday-calendar sites — excluded because the request requires primary Official Gazette sources.

## Gaps / residual uncertainty
- This environment did not provide a web-fetch/search tool, so the Gazette pages were not live-validated. Confirm that the Official Gazette URL resolves to Proclamation No. 1006 and check for any later amending proclamation before implementation.
- The Sunday-following-day rule is stated for regular holidays; it should not be generalized to special non-working days without an explicit proclamation or current labor guidance.
- This brief is research only; no application code or `.agent-context` file was changed. The authoritative artifact is this file: `/mnt/c/Users/sase/project/SAP_POC/.pi-subagents/artifacts/outputs/3036ac3b/research.md`.

## Acceptance report

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Concrete 2026 holiday dates, categories, official Gazette URLs, file path, and residual risks are provided in this brief."
    }
  ],
  "changedFiles": [
    "/mnt/c/Users/sase/project/SAP_POC/.pi-subagents/artifacts/outputs/3036ac3b/research.md"
  ],
  "testsAddedOrUpdated": [],
  "commandsRun": [],
  "validationOutput": [
    "Manual source-based transcription; live URL validation was not available in the runtime."
  ],
  "residualRisks": [
    "Confirm Proclamation No. 1006 and any later amendment before production use.",
    "Do not generalize the regular-holiday Sunday rule to special non-working days."
  ],
  "noStagedFiles": true,
  "diffSummary": "Added one concise primary-source research brief; no application code changed.",
  "reviewFindings": [
    "no blockers identified; live Gazette verification remains required"
  ],
  "manualNotes": "Requested .agent-context destination was superseded by the authoritative runtime output path."
}
```
