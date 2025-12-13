# Enhanced Configurable Prediction System

## Overview
A user-driven prediction system that allows healthcare analysts to define their own criteria for claim analysis.

## Architecture

### 1. **User-Defined Criteria**
Users can customize:
- **Focus Areas**: What to analyze (procedure codes, modifiers, amounts, etc.)
- **Similarity Rules**: How to identify similar claims
- **Risk Factors**: What to check for potential failures
- **Comparison Context**: Timeframe and scope

### 2. **Prediction Flow**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Input                                                │
│    - Claim ID                                                │
│    - Custom Criteria (Focus, Rules, Risk Factors, Context)  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Fetch Target Claim                                        │
│    - Use native MCP fetch_record()                          │
│    - Retrieve all service lines                             │
│    - Parse with detailed ServiceLine model                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. AI Constructs Similarity Query                           │
│    - Analyzes target claim                                  │
│    - Applies user's similarity rules                        │
│    - Generates natural language query                       │
│    Example: "Find failed claims with procedure 90677         │
│              and amounts between $500-$1500 from last 30d"  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Query Similar Claims                                      │
│    - AI converts NL query → T-SQL                           │
│    - Uses native MCP read_query()                           │
│    - Fetches service lines for each similar claim           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Detailed Comparison                                       │
│    - AI analyzes target vs similar claims                   │
│    - Applies user's focus areas                             │
│    - Checks for user-specified risk factors                 │
│    - Explains similarities and differences                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Rich Prediction Result                                    │
│    - FAIL/PASS prediction with confidence                   │
│    - Detailed reasons                                       │
│    - Risk factors found with severity                       │
│    - Similar claims with outcomes                           │
│    - Explanation of how criteria was applied                │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

### POST /predict-custom
```json
{
  "claim_id": "abc-123-guid",
  "focus_areas": ["procedure codes", "modifiers", "amounts"],
  "similarity_rules": "Same status and amount within 50%",
  "risk_factors": ["missing modifiers", "invalid codes"],
  "comparison_context": "Last 30 days"
}
```

**Response:**
```json
{
  "prediction": "FAIL",
  "confidence_score": 0.87,
  "top_reasons": [
    "Missing modifier GW required for hospice",
    "3 out of 5 similar claims failed",
    "Amount exceeds typical range by 45%"
  ],
  "risk_factors_found": [
    {
      "factor": "Missing Modifier",
      "severity": "HIGH",
      "details": "GW modifier required but not present"
    }
  ],
  "similar_claims": [
    {
      "claim_id": "xyz-456",
      "outcome": "FAIL",
      "similarity_score": 0.92,
      "reason": "Same procedure, similar amount"
    }
  ],
  "similarity_explanation": "Found claims with matching procedures within 50% amount range",
  "criteria_applied": {
    "focus_areas": ["procedure codes", "modifiers"],
    "similarity_rules": "Same status and amount within 50%"
  },
  "focus_areas_analyzed": [
    {
      "area": "Procedure Codes",
      "finding": "90677 found in 3 failed claims"
    },
    {
      "area": "Modifiers", 
      "finding": "Missing GW modifier"
    }
  ]
}
```

## UI Component Features

### Templates
- **Default**: Balanced analysis
- **Strict**: Tight matching, more risk factors
- **Lenient**: Broad matching, fewer restrictions

### Interactive Controls
- Toggleable focus areas
- Toggleable risk factors
- Free-text similarity rules
- Comparison context input

### Rich Results Display
- Prediction with confidence badge
- Risk factors with severity tags (HIGH/MEDIUM/LOW)
- Similar claims comparison table
- Focus area analysis breakdown
- Criteria application summary

## Key Improvements Over Basic Approach

### ❌ Old Approach
```python
# Hardcoded
similar_claims = fetch_claims(f"status eq {status}")
```

### ✅ New Approach
```python
# User defines what "similar" means
user_says: "Find claims with same procedure and amount within 30%"
ai_generates: "SELECT ... WHERE procedure = '90677' 
               AND amount BETWEEN 700 AND 1300"
```

## Technical Stack

1. **Native MCP Tools**
   - `read_query` - T-SQL execution
   - `Search` - Keyword search
   - `Fetch` - Direct record retrieval

2. **AI Pipeline**
   - GPT-4o for query construction
   - Natural language → T-SQL conversion
   - Context-aware comparison

3. **Rich Models**
   - ServiceLine with 60+ fields
   - Claim with full metadata
   - Structured prediction results

## Example Use Cases

### Use Case 1: Hospice Claims Specialist
```javascript
{
  focus_areas: ["modifiers", "place of service", "diagnosis"],
  similarity_rules: "Hospice claims (status 6) with same place of service",
  risk_factors: ["missing GW modifier", "wrong POS code"],
  comparison_context: "Last 60 days of hospice claims"
}
```

### Use Case 2: High-Value Claims Auditor
```javascript
{
  focus_areas: ["amounts", "procedure codes"],
  similarity_rules: "Claims over $5000 with matching primary procedure",
  risk_factors: ["amount outliers", "unbundling issues"],
  comparison_context: "Last 90 days, exclude approved claims"
}
```

### Use Case 3: Modifier Compliance Officer
```javascript
{
  focus_areas: ["modifiers", "additional modifiers"],
  similarity_rules: "Same procedure code regardless of status",
  risk_factors: ["missing required modifiers", "invalid modifier combinations"],
  comparison_context: "All time, focus on modifier patterns"
}
```

## Benefits

1. **Flexibility**: Users define what matters
2. **Explainability**: Clear reasoning for predictions
3. **Adaptability**: Criteria evolves with business rules
4. **Power**: Leverages native Dataverse MCP capabilities
5. **Intelligence**: AI constructs optimal queries

## Next Steps

1. Add saved criteria templates per user
2. Historical tracking of prediction accuracy
3. Batch prediction with custom criteria
4. Export comparison reports
5. Integration with rules engine
