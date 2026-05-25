# EHA-Uncued Synthetic Template Diversity Audit

Date: 2026-05-25

## Dataset Shape

The pilot contains 60 latent tasks. Conditions are balanced at 12 tasks each: clean, conflicting evidence, false consensus, buried primary, and generated lore. Families are 24 packet judgment, 24 evidence selection, and 12 active verification.

Each neutral metadata view contains 240 documents. Document body length ranges from 45 to 67 words, with median 55 and mean 54.07 words in both views.

## Metadata Distributions

The visible-metadata view has four title values, four source types, and 36 timestamps. Source types are balanced: 60 field notes, 60 operations memos, 60 registry entries, and 60 timeline notes. The hidden-metadata view masks source type to `document` for all 240 documents while preserving the same body distribution and timestamp count. In each view, 60 documents contain visible citations.

## Template Overlap

The strongest repeated sentence is the neutral relation-control sentence: "The note uses the same site code, workstream name, and monthly close date as the surrounding packet so that relation checks depend on the stated values rather than labels." It appears in all 240 documents per view. The top repeated 5-grams are therefore variants of that sentence.

This is an intentional control, but it is also a synthetic regularity. It reduces role leakage through metadata but limits ecological validity. The paper should describe this as supporting controlled diagnosis, not as proof that no template shortcut exists.

## Claim Boundary

No obvious single metadata field solves the task under the shortcut baselines, but template regularity remains a limitation. Future work should add semi-real document slices, more prose generators, and expanded template families before making broader benchmark claims.

