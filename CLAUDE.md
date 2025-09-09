# Claude Agent Guidelines for EstimateDoc

References:
- Architecture: `docs/ARCHITECTURE.md`
- UI/UX: `UI.md`
- Shared standards (authoritative): `docs/AI-AGENTS-GUIDELINES.md`

Note: All general coding, file-organization, navigation, testing, security, and performance rules are maintained centrally in `docs/AI-AGENTS-GUIDELINES.md`. This document focuses on Claude-specific prompting practices that complement (not duplicate) the shared standards.

## Core Principle
EstimateDoc requires high-accuracy outcomes. Treat every calculation, data point, and assumption as decision-critical.

## Claude Prompt Protocol (Mandatory)

<prompt_structure>
<context>
- Project: EstimateDoc - High-accuracy estimation system
- Domain: [Specify domain: financial/construction/project/etc.]
- Accuracy requirement: CRITICAL - Zero tolerance for errors
</context>

<task>
[Clear, specific task description using bullet points]
</task>

<constraints>
- NO mock/fake/placeholder data
- NO hard-coded values
- NO assumptions without explicit confirmation
- MUST validate all inputs
- MUST show calculation steps
</constraints>

<thinking_process>
1. Decompose requirements into explicit steps
2. Identify all data dependencies
3. Map calculation methodology
4. Define validation criteria
5. Plan error handling
6. Document assumptions needed (if any)
</thinking_process>

<verification>
Run double-check protocol after completion
</verification>
</prompt_structure>

All general Data Accuracy and Double-Check Protocol rules are defined in `docs/AI-AGENTS-GUIDELINES.md` (see section 3 and the Double-Check Protocol). Claude prompts must enforce those rules.

## Critical Reminders
1) STOP and ASK when data is missing, requirements are unclear, assumptions would be needed, or default values are requested.
2) NEVER PROCEED with placeholder data, guessed formulas, unverified assumptions, or when validation fails.
3) ALWAYS VERIFY by rechecking calculations, validating against criteria, testing different inputs, and confirming output accuracy.

## File Organization and Navigation
Follow the shared No-Orphaned-Files policy and navigation requirements in `docs/AI-AGENTS-GUIDELINES.md` (section 2), including verification and checklist items.

## Prompt Templates (Claude)

### Calculation Task Template
```xml
<calculation_request>
<objective>Calculate [specific metric/value]</objective>
<inputs>
  <data source="[source]" verified="[yes/no]">
    [List each input with value, unit, and validation status]
  </data>
</inputs>
<formula>
  [Explicit formula or calculation method]
  Source: [Industry standard/User provided/Documentation reference]
</formula>
<constraints>
  - Precision: [decimal places required]
  - Rounding: [rule specification]
  - Range: [acceptable min/max values]
</constraints>
<output_format>
  - Include units
  - Show intermediate steps
  - Provide confidence level
</output_format>
</calculation_request>
```

### Data Validation Template
```xml
<validation_check>
<data_point>[Value to validate]</data_point>
<expected>
  - Type: [number/string/date/etc.]
  - Range: [min-max]
  - Format: [specific format required]
  - Units: [expected units]
</expected>
<validation_steps>
  1. Type check
  2. Range verification
  3. Unit consistency
  4. Cross-reference with source
  5. Business rule compliance
</validation_steps>
</validation_check>
```

## Self-Reflection and Validation Framework

### Build Success Criteria BEFORE Starting
```xml
<pre_task_reflection>
<understand_problem>
  - What is the core problem I'm solving?
  - Why does this calculation matter?
  - What decisions will be made based on this result?
  - What would constitute a successful solution?
  - What would indicate a failed or incorrect solution?
</understand_problem>

<build_validation_criteria>
  - Accuracy requirement: [specific tolerance/precision]
  - Expected range: [min-max bounds for result]
  - Business logic rules: [what must be true]
  - Red flags: [what would indicate an error]
  - Success metrics: [how to measure correctness]
</build_validation_criteria>

<identify_assumptions>
  - What am I assuming to be true?
  - Which assumptions need verification?
  - What happens if assumptions are wrong?
  - How can I test each assumption?
</identify_assumptions>

<risk_assessment>
  - What could go wrong?
  - What are the consequences of each error type?
  - Which errors are most critical to avoid?
  - How will I detect if something goes wrong?
</risk_assessment>
</pre_task_reflection>
```

## Chain-of-Thought with Self-Reflection

1. DEEP THINKING Phase (Mandatory)
```xml
<deep_thinking>
<problem_decomposition>
  - Core question: What exactly am I calculating and why?
  - Sub-problems: Break into smallest solvable units
  - Dependencies: What depends on what?
  - Order of operations: What must be solved first?
</problem_decomposition>

<method_selection>
  - Available approaches: [List all possible methods]
  - Pros/cons of each: [Analyze tradeoffs]
  - Selected method: [Choice with justification]
  - Fallback method: [Alternative if primary fails]
</method_selection>

<data_reflection>
  - Data quality: How reliable is each input?
  - Data gaps: What's missing and how critical is it?
  - Data validation: How will I verify each input?
  - Error propagation: How do input errors affect output?
</data_reflection>

<success_criteria>
  - Validation tests: [List specific checks]
  - Acceptance thresholds: [Define pass/fail boundaries]
  - Confidence requirements: [Minimum confidence level]
  - Quality metrics: [How to measure output quality]
</success_criteria>
</deep_thinking>
```

2. EXECUTION Phase with Continuous Reflection
```xml
<execution_with_reflection>
<step_1>
  Action: [Data gathering and validation]
  Self-check: Did I get all required data? Is it validated?
  Confidence: [0-100%]
  Issues: [Any concerns or uncertainties]
</step_1>

<step_2>
  Action: [Apply calculation method]
  Self-check: Is this the right formula? Am I applying it correctly?
  Intermediate result: [Show value with units]
  Reasonableness: [Does this make sense so far?]
</step_2>

<step_3>
  Action: [Show intermediate results]
  Self-check: Are units consistent? Are magnitudes reasonable?
  Pattern check: [Do results follow expected patterns?]
  Error check: [Any red flags or anomalies?]
</step_3>

<step_4>
  Action: [Apply final transformations]
  Self-check: Are transformations mathematically valid?
  Precision check: [Is precision appropriate?]
  Final validation: [Does result meet initial criteria?]
</step_4>

<step_5>
  Action: [Format output with units]
  Self-check: Is format clear and unambiguous?
  Completeness: [Is all required information included?]
  Usability: [Can user make decisions with this output?]
</step_5>
</execution_with_reflection>
```

3. Deep Verification Phase
```xml
<deep_verification>
<calculation_verification>
  - Recalculate using different method: [Alternative approach]
  - Compare results: [Do they match within tolerance?]
  - Explain discrepancies: [If any, why do they exist?]
</calculation_verification>

<criteria_validation>
  - Success criteria met: [Check each criterion]
  - Red flags detected: [List any warnings]
  - Confidence level: [Final confidence percentage]
  - Quality score: [Rate output quality 1-10]
</criteria_validation>

<sanity_checks>
  - Magnitude check: Is result in expected ballpark?
  - Unit analysis: Do units work out correctly?
  - Boundary testing: Does result handle edge cases?
  - Business logic: Does result make business sense?
</sanity_checks>

<error_analysis>
  - Potential error sources: [List all possibilities]
  - Error magnitude: [Estimate impact of each]
  - Mitigation applied: [How each was addressed]
  - Residual risk: [What uncertainty remains?]
</error_analysis>
</deep_verification>
```

4. Post-Task Reflection (Mandatory)
```xml
<post_task_reflection>
<outcome_assessment>
  - Did I achieve the original goal?
  - How well did I meet success criteria?
  - What confidence do I have in the result?
  - Would I stake my reputation on this answer?
</outcome_assessment>

<learning_extraction>
  - What worked well?
  - What was challenging?
  - What would I do differently?
  - What patterns should I remember?
</learning_extraction>

<quality_certification>
  - Data quality: [Rate 1-10 with justification]
  - Method quality: [Rate 1-10 with justification]
  - Result quality: [Rate 1-10 with justification]
  - Overall confidence: [Percentage with explanation]
</quality_certification>

<final_recommendation>
  - Can this result be used for decision-making? [Yes/No/Qualified]
  - Caveats or limitations: [List any important notes]
  - Suggested validation: [Additional checks user might want]
</final_recommendation>
</post_task_reflection>
```

## Error Handling Protocol (Prompts)
```xml
<error_response>
<issue>[Specific problem identified]</issue>
<required_data>
  - Field: [name]
  - Expected format: [specification]
  - Why needed: [explanation]
  - Impact if missing: [consequence]
</required_data>
<user_request>
  "I need the following data to proceed with accurate calculations:
  [Bulleted list of specific requirements]
  
  Please provide:
  1. [Specific data point 1]
  2. [Specific data point 2]
  
  Without this data, I cannot guarantee accuracy."
</user_request>
</error_response>
```

## Prompt Optimization Techniques
- Be explicit and direct; define outputs, units, and precision
- Use multi-shot examples with real data and complete calculation chains
- Enable parallel processing by structuring tasks explicitly
- Use XML-like structure for clarity and verifiability

## Metacognitive Checkpoints
Insert checkpoints throughout tasks:
```xml
<metacognitive_checkpoint>
<current_state>
  - Where am I in the process?
  - What have I accomplished so far?
  - What remains to be done?
</current_state>

<quality_check>
  - Is my current approach working?
  - Am I making unverified assumptions?
  - Have I deviated from the plan?
  - Should I reconsider my method?
</quality_check>

<confidence_assessment>
  - Current confidence level: [0-100%]
  - Reasons for confidence/doubt: [List factors]
  - Information needed to increase confidence: [Specify]
</confidence_assessment>

<decision_point>
  - Continue with current approach? [Yes/No]
  - If no, alternative approach: [Describe]
  - Justification: [Explain reasoning]
</decision_point>
</metacognitive_checkpoint>
```

### Mandatory Checkpoint Locations
1. After problem understanding
2. Before method selection
3. After 25% completion
4. After 50% completion
5. After 75% completion
6. Before final output
7. After any error or unexpected result

## Critical Thinking Triggers
- "Break this down step-by-step"
- "Show your reasoning explicitly"
- "Validate each assumption before proceeding"
- "If any data is missing, stop and request it"
- "Double-check your calculations"
- "Explain why this approach is correct"
- "What could go wrong with this calculation?"

## Project-Specific Rules
- Estimates must be traceable to source data
- All margins of error must be explicitly stated
- Historical data must be date-stamped
- Confidence levels must accompany estimates
- Calculation methods must be industry-standard or user-approved

### Financial Calculations
- Use decimal arithmetic for currency; avoid binary floating-point
- Always specify currency codes (confirm default with user)
- Include applicable fees and taxes; document rounding rules
- Prefer banker's rounding for financial values; track precision end-to-end

For everything not explicitly Claude-prompt-specific, defer to `docs/AI-AGENTS-GUIDELINES.md`.

