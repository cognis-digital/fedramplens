# Demo 08 - Malformed POA&M date

A FedRAMP **Moderate** permit portal whose boundary is clean, but one
POA&M item (`V-301`) has a scheduled-completion value of `"Q3 2026"`
instead of an ISO-8601 date. The analyzer can't decide whether it's
overdue, so it surfaces the formatting problem rather than silently
ignoring the milestone.

## Where this comes from

POA&M spreadsheets exported to JSON frequently carry free-text dates
("Q3 2026", "TBD", "End of FY"). FedRAMP and OSCAL both expect
`YYYY-MM-DD`. This demo shows the tool refusing to let an unparseable
date slip through unnoticed.

## Run it

```sh
python -m fedramplens analyze demos/08-bad-poam-date/boundary.json
python -m fedramplens --format json analyze demos/08-bad-poam-date/boundary.json | jq '.findings'
```

## Expected

One **bad_poam_date** (low) finding for `V-301` reporting the invalid
date `'Q3 2026'`. The well-formed `V-302` is fine.
`Authorization-ready: YES` and **exit 0** (low severity). Both items
still count toward `poam_open` and the risk score.

## How to act

Replace `"Q3 2026"` with a concrete date such as `"2026-09-30"`. Re-run;
the finding clears and the item becomes eligible for overdue detection.
