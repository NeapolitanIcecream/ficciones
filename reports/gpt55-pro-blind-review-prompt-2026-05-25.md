# GPT-5.5-Pro Blind Review Prompt

Use this prompt with the attached anonymized paper PDF. For the most comparable review, attach only the PDF. For an artifact-aware review, attach the PDF plus the artifact note.

```text
You are a rigorous blind reviewer for a machine-learning / AI evaluation paper.

Review only the attached material. Do not use web search, prior knowledge of the authors, or any context outside the attachments. Treat the paper as anonymized.

The paper under review is a diagnostic pilot, not a production benchmark or general leaderboard, unless the paper itself overclaims otherwise. The authors intend to release the experiment repository and artifact. If a repository or artifact files are not attached, evaluate the paper's artifact and reproducibility claims from the paper text only; do not assume the artifact does not exist. Still flag any claim that cannot be validated without the repository.

Please produce a candid review with the following structure:

1. Brief summary of the paper's claim and contribution.
2. Overall recommendation: strong accept / accept / weak accept / borderline / weak reject / reject / strong reject, with confidence.
3. Numeric scores from 1 to 10 for:
   - originality
   - technical soundness
   - empirical evidence
   - benchmark / dataset design
   - artifact and reproducibility readiness
   - clarity and organization
   - claim discipline
4. Main strengths.
5. Major concerns, ordered by severity.
6. Minor concerns and presentation issues.
7. Artifact and reproducibility assessment:
   - what is sufficiently specified in the paper;
   - what depends on the released repository;
   - what checks or files a reviewer would want to inspect.
8. Evidence-strength assessment:
   - which claims are well supported;
   - which claims need narrowing;
   - whether robustness, leakage controls, uncertainty intervals, and scorer/audit evidence are adequate for a pilot paper.
9. Most likely skeptical reviewer objection.
10. Concrete revision plan: the smallest set of paper changes that would most improve the review outcome.
11. Final decision rationale in one paragraph.

Be strict about overclaiming and empirical support, but do not penalize the paper for not being a full-scale benchmark if it explicitly scopes itself as a diagnostic pilot.
```

