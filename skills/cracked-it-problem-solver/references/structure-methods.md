# Structure Methods: Hypothesis Pyramids and Issue Trees

## Overview

After stating the problem with TOSCA, the next step is to structure it. Two main approaches exist:

1. **Hypothesis Pyramid** - Start with an answer, break it down to validate it
2. **Issue Tree** - Start with a question, break it down to explore all angles

## Hypothesis Pyramid

### What It Is

A top-down structure starting from a proposed solution (hypothesis) and breaking it into conditions that must be true for the hypothesis to hold.

### Structure

```
[LEADING HYPOTHESIS: The answer]
    ├─ [SUB-HYPOTHESIS 1: Condition that must be true]
    ├─ [SUB-HYPOTHESIS 2: Another condition]
    └─ [SUB-HYPOTHESIS 3: Another condition]
         ├─ [SUB-SUB-HYPOTHESIS 3.1]
         └─ [SUB-SUB-HYPOTHESIS 3.2]
```

### When to Use

- You have a strong initial hypothesis/candidate solution
- Time pressure to deliver quickly
- Experienced team with relevant domain expertise
- Problem owner has pre-sold solution that needs validation
- Pattern recognition applies (similar problem solved before)

### Advantages

1. **Efficient** - Focuses efforts on one solution path
2. **Fast** - No need to explore all options
3. **Persuasive** - Structure doubles as selling argument
4. **Practical** - Matches how experts actually think

### Dangers (Critical!)

1. **Confirmation Bias** - You'll find what you're looking for
2. **Narrow Framing** - Ignores alternative solutions
3. **Wrong Framework** - May use inappropriate mental models
4. **Premature Diagnosis** - Mistaking new problems for familiar ones
5. **Groupthink** - Team reinforces each other's biases

### MECE Principle

Sub-hypotheses should be:
- **Mutually Exclusive** - Don't overlap
- **Collectively Exhaustive** - Cover all necessary conditions

Example:
- Leading Hypothesis: "Expand to Canada via partnership with De Marque"
- Sub-hypotheses:
  1. Market is attractive (size, growth, accessibility)
  2. Partner is suitable (capabilities, reliability, alignment)
  3. Entry mode works (JV structure, control, economics)
  4. Implementation is feasible (resources, timeline, risks)

### How to Build

**Step 1:** State the leading hypothesis (candidate solution)

**Step 2:** Ask "For this to be true, what must be true?"
- Identify necessary conditions
- Break down into 3-7 sub-hypotheses

**Step 3:** For each sub-hypothesis, ask again "What must be true?"
- Continue breaking down 2-3 levels deep
- Stop when you reach testable elementary hypotheses

**Step 4:** Check MECE at each level
- Are conditions mutually exclusive?
- Have you covered all necessary conditions?

**Step 5:** Identify which hypotheses to test (see analysis-methods.md)

### Example: Librinova Expansion

**Leading Hypothesis:**
"Librinova should expand to Canada through partnership with De Marque"

**Level 1 Sub-Hypotheses:**
1. The Canadian market is attractive
2. De Marque is the right partner
3. The partnership structure will work
4. Librinova has capacity to execute

**Level 2 (Under "Market is attractive"):**
1.1. Market size is sufficient (>50k self-published books/year)
1.2. Distribution channels are accessible
1.3. Competition is manageable
1.4. Suppliers (printers, editors) are available
1.5. Canadian publishers are open to platform

## Issue Tree

### What It Is

A top-down structure starting from a question and breaking it into sub-questions, exploring the problem space without preconceived solutions.

### Structure

```
[CORE QUESTION]
    ├─ [SUB-QUESTION 1]
    │   ├─ [SUB-SUB-QUESTION 1.1]
    │   └─ [SUB-SUB-QUESTION 1.2]
    ├─ [SUB-QUESTION 2]
    └─ [SUB-QUESTION 3]
```

### When to Use

- Problem is genuinely novel or poorly understood
- No strong hypothesis exists
- Multiple stakeholders with competing views
- High risk of confirmation bias
- Need comprehensive exploration
- Diverse team with varied perspectives

### Advantages

1. **Thorough** - Explores problem systematically
2. **Unbiased** - Doesn't favor particular solution
3. **Comprehensive** - Less likely to miss important angles
4. **Discovery-oriented** - May reveal unexpected insights

### Disadvantages

1. **Slower** - More exploration required
2. **Harder to build** - Requires strong structuring skills
3. **Less focused** - May analyze unnecessary branches
4. **Delayed solution** - Takes longer to converge

### MECE Principle (Even More Critical)

Sub-questions should be:
- **Mutually Exclusive** - Don't overlap in what they ask
- **Collectively Exhaustive** - Together they fully answer parent question

### How to Build

**Step 1:** Start with core question from TOSCA

**Step 2:** Ask "To answer this, what do I need to know?"
- Identify 3-7 major sub-questions
- Check MECE

**Step 3:** For each sub-question, ask "What do I need to know to answer this?"
- Break down 2-3 levels deep
- Stop when questions become directly answerable through analysis

**Step 4:** Three ways to break down (see next section):
- Industry/value driver logic
- Functional decomposition
- Pure logic/calculation

**Step 5:** Map to analytical frameworks when helpful (see analytical-frameworks.md)

### Example: Librinova Expansion (Issue Tree Approach)

**Core Question:**
"How should Librinova pursue international expansion?"

**Level 1 Sub-Questions:**
1. Where should we expand? (Geography selection)
2. When should we expand? (Timing)
3. How should we enter? (Entry mode)
4. What resources do we need? (Implementation)

**Level 2 (Under "Where should we expand?"):**
1.1. Which markets are most attractive?
1.2. Where can we build competitive advantage?
1.3. Where do we have access/partnerships?

## Comparison: When to Use Each

| Criterion | Hypothesis Pyramid | Issue Tree |
|-----------|-------------------|------------|
| **Problem familiarity** | Familiar, pattern recognized | Novel, poorly understood |
| **Hypothesis strength** | Strong candidate solution | Weak or no hypothesis |
| **Time available** | Limited, pressure to deliver | Sufficient for exploration |
| **Team composition** | Experienced, aligned | Diverse, varied views |
| **Risk tolerance** | Can afford focused bet | Need comprehensive view |
| **Stakeholder alignment** | Pre-sold solution | Competing views |

**Default rule:** When in doubt, use issue tree. The pyramid's speed isn't worth the confirmation bias risk unless you're very confident.

## Common Structuring Mistakes

1. **Mixing approaches**
   - Starting with question but sneaking in hypothesis
   - Issue tree that's actually disguised pyramid

2. **Violating MECE**
   - Overlapping branches (not mutually exclusive)
   - Missing important angles (not collectively exhaustive)

3. **Wrong level of detail**
   - Too high-level: Doesn't guide analysis
   - Too detailed: Overwhelms with branches

4. **Forgetting it's iterative**
   - Structure evolves as you learn
   - Revise as analyses reveal new insights

5. **Forcing frameworks**
   - Using framework that doesn't fit
   - Missing problem-specific factors

## The Iterative Nature

**Key Insight:** Structuring is not one-time, it's iterative.

As you conduct analyses (Solve step), you'll:
- Discover new sub-questions or sub-hypotheses
- Realize some branches are more important than others
- Find some branches don't matter
- Need to reframe the overall structure

**Process:**
1. Create initial structure (pyramid or tree)
2. Begin analyses
3. Learn from findings
4. Revise structure
5. Repeat until problem is solved

## From Structure to Analysis

Once structure is complete (pyramid or tree), it guides the Solve phase:

**For Hypothesis Pyramids:**
- Each sub-hypothesis becomes an analysis to conduct
- Prioritize by decisiveness (will it change recommendation?)
- Test systematically level by level

**For Issue Trees:**
- Each terminal sub-question becomes an analysis
- Prioritize by importance and difficulty
- Answer systematically branch by branch

See `references/analysis-methods.md` for how to plan and execute analyses.

## Special Case: When Neither Works

If you struggle to build either structure:
- Problem may be too ambiguous for logical decomposition
- May need user-centered creative solutions
- Consider pivoting to Design Thinking (see references/design-thinking.md)

Design thinking is especially useful when:
- Problem is hard to articulate precisely
- Solutions must be designed for people
- Context is highly complex and uncertain
- Need creative, innovative approaches
