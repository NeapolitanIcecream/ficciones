# Qualitative Failure Examples

These are deterministic local audit examples for scorer/schema interpretation. They are not independent human validation.

## Strict True Failures

### uncued_012_visible / gemini-3.1-pro-preview

- Condition/family: `conflicting_evidence` / `packet_judgment`
- Polluted support: `uncued_012_d03`
- Rejected docs: `uncued_012_d04`
- Sensitivity: strict=`fail`, prose=`fail`, action=`fail`
- Local audit note: No prose available in prediction payload.

### uncued_015_visible / gemini-3.1-pro-preview

- Condition/family: `conflicting_evidence` / `packet_judgment`
- Polluted support: `uncued_015_d01`
- Rejected docs: `uncued_015_d04,uncued_015_d03`
- Sensitivity: strict=`fail`, prose=`fail`, action=`fail`
- Local audit note: No prose available in prediction payload.

### uncued_016_hidden / gemini-3.1-pro-preview

- Condition/family: `conflicting_evidence` / `packet_judgment`
- Polluted support: `uncued_016_d01`
- Rejected docs: `uncued_016_d02`
- Sensitivity: strict=`fail`, prose=`fail`, action=`fail`
- Local audit note: No prose available in prediction payload.

### uncued_017_visible / gemini-3.1-pro-preview

- Condition/family: `conflicting_evidence` / `evidence_selection`
- Polluted support: `uncued_017_d03`
- Rejected docs: `uncued_017_d04`
- Sensitivity: strict=`fail`, prose=`fail`, action=`fail`
- Local audit note: No prose available in prediction payload.

## Likely Schema-Allocation Artifacts

### uncued_012_visible / claude-opus-4-7

- Condition/family: `conflicting_evidence` / `packet_judgment`
- Polluted support: `uncued_012_d03`
- Rejected docs: `uncued_012_d04`
- Sensitivity: strict=`fail`, prose=`pass`, action=`pass`
- Local audit note: No prose available in prediction payload.

### uncued_013_visible / claude-opus-4-7

- Condition/family: `conflicting_evidence` / `packet_judgment`
- Polluted support: `uncued_013_d01`
- Rejected docs: `uncued_013_d03,uncued_013_d02`
- Sensitivity: strict=`fail`, prose=`pass`, action=`pass`
- Local audit note: No prose available in prediction payload.

### uncued_013_hidden / claude-opus-4-7

- Condition/family: `conflicting_evidence` / `packet_judgment`
- Polluted support: `uncued_013_d03`
- Rejected docs: `uncued_013_d04`
- Sensitivity: strict=`fail`, prose=`pass`, action=`pass`
- Local audit note: No prose available in prediction payload.

### uncued_014_hidden / claude-opus-4-7

- Condition/family: `conflicting_evidence` / `packet_judgment`
- Polluted support: `uncued_014_d02`
- Rejected docs: `uncued_014_d02,uncued_014_d04,uncued_014_d01`
- Sensitivity: strict=`fail`, prose=`pass`, action=`pass`
- Local audit note: No prose available in prediction payload.

## Borderline Rows

_No matching rows._
