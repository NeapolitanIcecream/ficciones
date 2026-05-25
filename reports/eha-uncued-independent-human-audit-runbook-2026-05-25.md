# EHA-Uncued Independent Human Audit Runbook

Date: 2026-05-25

## Status

This is a design for a future independent human audit. It has not been executed. The paper must not claim independent human validation until this protocol is run and labels are adjudicated.

## Sampling Plan

Target at least two annotators. Sample 80 to 120 scored rows from the 480-row pilot, blind to model identity where practical. Stratify by:

- all five conditions;
- all three task families;
- both neutral metadata views;
- operational successes and failures;
- oversampling generated lore, conflicting evidence, active verification, and rows where belief correctness and operational escape disagree.

## Annotation Fields

Annotators label:

- semantic verdict agreement with the gold verdict;
- support-field hygiene;
- polluted evidence rejection or avoidance;
- action executability;
- exact target match for active-verification rows;
- whether the automatic scorer appears too strict, too lenient, or acceptable;
- free-text rationale and adjudication notes.

## Adjudication

Compute agreement before adjudication. For binary fields, report percent agreement and Cohen's kappa when label prevalence permits. For graded/action fields, report exact agreement and adjudicated disagreement categories. Final adjudication should be performed by a third reviewer or a joint reconciliation meeting with documented reasons.

## Output Requirements

Record:

- sampled row IDs and sampling seed;
- annotator instructions;
- blind packet files;
- raw labels;
- adjudicated labels;
- agreement tables;
- changes, if any, to scorer interpretation.

