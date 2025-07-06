# CLAUDE UI VERIFICATION PROCESS

## CRITICAL: Always Follow This Process for UI Work

### MANDATORY VERIFICATION STEPS (No Exceptions)

#### 1. READ MOCKUP COMPLETELY FIRST
- Read entire mockup HTML/design file line by line
- Do NOT assume anything about component behavior
- Map every text element, attribute, and styling property

#### 2. CONTENT ACCURACY BEFORE STYLING
**Order of Priority:**
1. Exact text content matches
2. HTML structure matches  
3. CSS properties match
4. Visual styling perfection

#### 3. LINE-BY-LINE COMPARISON PROCESS
When user says "compare with mockup":
```
□ Read mockup HTML structure completely
□ Identify every text element and exact content  
□ Map each element to React component
□ Verify content matches BEFORE styling
□ Compare log output line-by-line with mockup
□ Fix content/structure differences FIRST
□ Then fix styling differences
```

#### 4. NEVER TRUST PREVIOUS WORK
- Even if I built a component, verify it against THIS SPECIFIC mockup
- Question every assumption about "how it should work"
- Mockup is the single source of truth

#### 5. SYSTEMATIC DEBUGGING
When user points out differences:
- Read the exact mockup section they mentioned
- Find the equivalent in log output
- Compare character by character if needed
- Fix the root cause, not just symptoms

### COMMON FAILURE PATTERNS TO AVOID

❌ **Assumption-Based Development**: "This component should show round indicators"
✅ **Mockup-Based Development**: Check if mockup shows round indicators

❌ **General Visual Comparison**: "Looks similar enough"  
✅ **Exact Element Comparison**: Every text, class, and property matches

❌ **Styling First**: Focus on colors/fonts before content
✅ **Content First**: Ensure text and structure match exactly

❌ **Surface-Level Fixes**: Changing CSS without understanding structure
✅ **Root Cause Analysis**: Why does the structure differ from mockup?

### VERIFICATION CHECKLIST

Before claiming "matches mockup exactly":
□ Every text element has identical content
□ No extra prefixes/suffixes (like "Round 1 •")
□ HTML structure mirrors mockup structure
□ CSS properties match mockup values
□ Rendered output log compared line-by-line
□ User can see the exact visual result they expect

### MEMORY TRIGGER

**When user says "compare with mockup"** → STOP and follow this process completely
**When user says "it doesn't look like mockup"** → Read mockup again line by line
**When user shows differences** → Find exact mockup section and compare character by character

This document serves as my persistent memory for UI verification work.