# Aareguru MCP Server - Claude Desktop Integration Plan

## Overview

This document outlines the optimal strategy for exposing the Aareguru API to Claude Desktop via MCP, focusing on natural user interactions and the types of questions Claude can answer.

---

## MCP Exposure Strategy

### 1. Resources (Read-Only Data Access)

Resources provide Claude with contextual information about available locations and current conditions.

| Resource URI | Purpose | When Claude Uses It |
|--------------|---------|---------------------|
| `aareguru://cities` | List all available cities | Discovery, validation, suggestions |
| `aareguru://current/{city}` | Full current data for a city | Comprehensive queries about conditions |
| `aareguru://today/{city}` | Minimal current data | Quick temperature checks |
| `aareguru://widget` | All cities at once | Comparisons, multi-city queries |

**Benefits**:
- Claude can proactively read city lists without tool calls
- Faster responses for common queries
- Better context awareness

---

### 2. Tools (Dynamic Queries)

Tools allow Claude to fetch specific data based on user requests.

#### Tool 1: `get_current_temperature`
**Purpose**: Get water temperature for a specific city

**Input Schema**:
```json
{
  "city": {
    "type": "string",
    "description": "City identifier (e.g., 'bern', 'thun', 'basel')",
    "default": "bern"
  }
}
```

**Output**: Temperature value, human-readable text (in Swiss German), and short description

**User Questions This Answers**:
- "What's the Aare temperature in Bern?"
- "How cold is the water in Thun?"
- "Is it warm enough to swim in Basel?"
- "Can I swim in the Aare today?"

---

#### Tool 2: `get_current_conditions`
**Purpose**: Get complete current conditions (water, weather, flow)

**Input Schema**:
```json
{
  "city": {
    "type": "string",
    "description": "City identifier",
    "default": "bern"
  }
}
```

**Output**: Water temp, flow rate, danger level, weather conditions, forecasts

**User Questions This Answers**:
- "What are the current Aare conditions in Bern?"
- "Is it safe to swim in the Aare today?"
- "What's the weather and water temperature?"
- "How strong is the current in Thun?"
- "Give me a full swimming report for Basel"

---

#### Tool 3: `get_historical_data`
**Purpose**: Retrieve time-series data for analysis

**Input Schema**:
```json
{
  "city": {
    "type": "string",
    "description": "City identifier",
    "required": true
  },
  "start": {
    "type": "string",
    "description": "Start date/time (ISO, timestamp, or relative like '-7 days')",
    "required": true
  },
  "end": {
    "type": "string",
    "description": "End date/time (ISO, timestamp, or 'now')",
    "required": true
  }
}
```

**Output**: Historical temperature, flow, and weather data

**User Questions This Answers**:
- "How has the Aare temperature changed over the last week?"
- "Show me temperature trends for the past month"
- "Was the water warmer last year at this time?"
- "What's the average temperature in July?"
- "Create a chart of water temperature for the last 30 days"

---

#### Tool 4: `list_cities`
**Purpose**: Get all available cities with metadata

**Input Schema**: None (no parameters)

**Output**: Array of cities with identifiers, names, and locations

**User Questions This Answers**:
- "Which cities have Aare data available?"
- "Where can I check Aare temperatures?"
- "List all swimming spots"
- "What locations are monitored?"

---

#### Tool 5: `get_flow_danger_level`
**Purpose**: Get flow rate and BAFU danger assessment

**Input Schema**:
```json
{
  "city": {
    "type": "string",
    "description": "City identifier",
    "default": "bern"
  }
}
```

**Output**: Flow rate (m³/s), danger level (1-5), description, safety assessment

**User Questions This Answers**:
- "Is the Aare flow dangerous right now?"
- "What's the current danger level?"
- "Is it safe to swim with this flow rate?"
- "How fast is the water flowing?"
- "Should I be concerned about the current?"

---

#### Tool 6: `compare_cities`
**Purpose**: Compare conditions across multiple cities

**Input Schema**:
```json
{
  "cities": {
    "type": "array",
    "items": {"type": "string"},
    "description": "List of city identifiers to compare"
  }
}
```

**Output**: Side-by-side comparison of temperatures, flow, weather

**User Questions This Answers**:
- "Compare Bern and Thun water temperatures"
- "Which city has the warmest water?"
- "Where's the best place to swim today?"
- "Show me all cities with water above 20°C"

---

#### Tool 7: `get_forecast`
**Purpose**: Get weather and temperature forecasts

**Input Schema**:
```json
{
  "city": {
    "type": "string",
    "description": "City identifier",
    "default": "bern"
  },
  "hours": {
    "type": "integer",
    "description": "Number of hours ahead (2-48)",
    "default": 24
  }
}
```

**Output**: Forecasted temperatures, weather conditions

**User Questions This Answers**:
- "Will the water be warmer tomorrow?"
- "What's the forecast for swimming this weekend?"
- "Should I wait until later to swim?"
- "When will the temperature peak today?"

---

## Extensive List of User Questions

### Basic Temperature Queries
1. "What's the Aare temperature right now?"
2. "How cold is the water in Bern?"
3. "Is the Aare warm enough to swim?"
4. "What's the current water temperature?"
5. "Can you check the Aare temp for me?"
6. "How many degrees is the water?"
7. "Is it too cold to swim today?"
8. "What's the water like in Thun?"
9. "Temperature check for Basel please"
10. "How warm is the Aare in Olten?"

### Safety & Flow Questions
11. "Is it safe to swim in the Aare today?"
12. "What's the current danger level?"
13. "How strong is the current?"
14. "Is the flow rate dangerous?"
15. "Should I be worried about the current?"
16. "What's the BAFU danger assessment?"
17. "Is the water flowing too fast?"
18. "Can beginners swim safely today?"
19. "What's the flow rate in m³/s?"
20. "Is there a flood warning?"

### Weather Integration
21. "What's the weather like for swimming?"
22. "Is it sunny enough to go to the Aare?"
23. "Will it rain while I'm swimming?"
24. "What's the air temperature vs water temperature?"
25. "Is it a good day for the Aare?"
26. "Should I bring sunscreen?"
27. "What's the UV index?"
28. "Is it windy by the river?"
29. "What's the weather forecast for swimming?"
30. "Will it be sunny this afternoon?"

### Comparative Questions
31. "Which city has the warmest water?"
32. "Compare Bern and Thun temperatures"
33. "Where's the best place to swim today?"
34. "Is Basel warmer than Bern?"
35. "Which location has the calmest water?"
36. "Show me all cities above 18 degrees"
37. "Where should I go swimming?"
38. "Which spot is safest for kids?"
39. "Compare all available locations"
40. "What's the coldest spot today?"

### Historical & Trend Questions
41. "How has the temperature changed this week?"
42. "Is it warmer than yesterday?"
43. "Show me the last 7 days of data"
44. "What was the temperature last weekend?"
45. "Is this normal for this time of year?"
46. "When was the water warmest this month?"
47. "How does today compare to last year?"
48. "What's the average temperature in August?"
49. "Show me temperature trends"
50. "Has the water been getting warmer?"

### Forecast Questions
51. "Will the water be warmer tomorrow?"
52. "What's the forecast for this weekend?"
53. "Should I wait until later to swim?"
54. "When will it be warmest today?"
55. "Is the temperature rising or falling?"
56. "What's the 2-hour forecast?"
57. "Will conditions improve?"
58. "Should I swim now or later?"
59. "What's the outlook for next week?"
60. "When's the best time to swim today?"

### Location Discovery
61. "Where can I check Aare temperatures?"
62. "Which cities have data available?"
63. "List all swimming spots"
64. "What locations are monitored?"
65. "Do you have data for Interlaken?"
66. "Which cities can I query?"
67. "Show me all available locations"
68. "Where are the measurement stations?"
69. "What's the closest monitored spot to Zurich?"
70. "Are there any new locations?"

### Contextual & Complex Questions
71. "I'm planning to swim at 5 PM, what will conditions be like?"
72. "Is it a good day for Aare swimming (Aareböötle)?"
73. "What should I know before swimming today?"
74. "Give me a full swimming report"
75. "Is it safe for my kids to swim?"
76. "What gear should I bring based on conditions?"
77. "How long can I safely stay in the water?"
78. "Is the water quality good today?"
79. "What's the visibility like?"
80. "Should I wear a wetsuit?"

### Conversational Questions
81. "How's the Aare looking today?"
82. "Is it Aare weather?"
83. "Should I go for a swim?"
84. "What do you think about swimming conditions?"
85. "Is it worth going to the river?"
86. "Would you recommend swimming today?"
87. "Talk me through the current conditions"
88. "What's the vibe at the Aare?"
89. "Is everyone swimming today?"
90. "What's the Swiss German temperature description?"

### Data Analysis Questions
91. "What's the warmest the Aare has been this year?"
92. "Calculate the average temperature for July"
93. "Show me a temperature graph for the month"
94. "What's the temperature variance this week?"
95. "How often does it exceed 20°C?"
96. "What's the median flow rate?"
97. "Analyze temperature patterns"
98. "What's the correlation between air and water temp?"
99. "Show me daily temperature ranges"
100. "What's the standard deviation?"

### Specific Use Cases
101. "I'm a tourist, where should I swim?"
102. "Best spot for Aare floating?"
103. "Where do locals swim in Bern?"
104. "Is Marzili good today?"
105. "What about the Aare in Thun for SUP?"
106. "Good conditions for kayaking?"
107. "Is it safe for wild swimming?"
108. "Can I bring my dog to swim?"
109. "Best time of day for swimming?"
110. "Is the Aare crowded when it's this warm?"

### Multi-Step Queries
111. "Check Bern temperature, then compare with Thun"
112. "Show me today's conditions and tomorrow's forecast"
113. "List cities, then show me the warmest one"
114. "Get historical data and predict tomorrow"
115. "Compare all cities and recommend the best"
116. "Check danger level, then give safety advice"
117. "Show current temp and last week's average"
118. "Get forecast and historical comparison"
119. "Find warmest city and check its flow rate"
120. "Analyze trends and predict peak time"

### Edge Cases & Special Requests
121. "What if there's no data available?"
122. "Show me cities with missing data"
123. "What's the data update frequency?"
124. "When was the last measurement?"
125. "Is the sensor working in Basel?"
126. "What's the data source?"
127. "How accurate are the measurements?"
128. "What's the margin of error?"
129. "Can you explain the danger levels?"
130. "What does 'geil aber chli chalt' mean?"

---

## Recommended Tool Implementation Priority

### Phase 1: Essential (MVP)
1. ✅ `get_current_temperature` - Most common query
2. ✅ `get_current_conditions` - Comprehensive safety info
3. ✅ `list_cities` - Discovery and validation

### Phase 2: Enhanced
4. ✅ `get_flow_danger_level` - Safety-critical
5. ✅ `get_historical_data` - Trend analysis
6. ✅ `compare_cities` - Multi-location queries

### Phase 3: Advanced
7. ✅ `get_forecast` - Predictive queries
8. ⭐ `get_swimming_recommendation` - AI-powered advice
9. ⭐ `analyze_trends` - Statistical analysis

---

## Claude's Natural Language Understanding

Claude can handle these query patterns naturally:

### Direct Questions
- "What's the temperature?"
- "Is it safe?"
- "Show me Bern"

### Conversational
- "I'm thinking about swimming, what do you think?"
- "How's the Aare looking?"
- "Should I go now or wait?"

### Complex Multi-Part
- "Compare Bern and Thun, then tell me which is safer for kids"
- "Show me the last week's data and predict tomorrow"
- "Find the warmest spot with low flow"

### Implicit Context
- "What about Thun?" (after discussing Bern)
- "And the flow?" (after temperature query)
- "How does that compare?" (after showing data)

---

## Response Formatting Recommendations

### Temperature Responses
```
🌡️ **Aare Temperature in Bern**
- Current: 17.2°C
- Description: "geil aber chli chalt" (awesome but a bit cold)
- Status: Good for swimming! 🏊

💧 Water feels refreshing but comfortable for most swimmers.
```

### Safety Responses
```
⚠️ **Safety Assessment for Bern**
- Flow Rate: 245 m³/s
- Danger Level: 2/5 (Moderate)
- Recommendation: Safe for experienced swimmers, use caution

🏊 Conditions are generally safe, but be aware of the current.
```

### Comparison Responses
```
📊 **City Comparison**

| City | Temp | Flow | Safety |
|------|------|------|--------|
| Bern | 17.2°C | 245 m³/s | ⚠️ Moderate |
| Thun | 18.1°C | 180 m³/s | ✅ Safe |
| Basel | 16.8°C | 310 m³/s | ⚠️ Caution |

🏆 **Recommendation**: Thun has the warmest water and safest conditions today!
```

---

## User Experience Enhancements

### 1. Proactive Suggestions
When a user asks about swimming, Claude can:
- Automatically check temperature AND safety
- Suggest alternative locations if conditions are poor
- Provide forecast if current conditions aren't ideal

### 2. Context Awareness
- Remember user's preferred location
- Track conversation history (e.g., "How about now?" after checking earlier)
- Understand implicit references

### 3. Educational Responses
- Explain Swiss German temperature descriptions
- Describe BAFU danger levels
- Provide swimming safety tips based on conditions

### 4. Seasonal Intelligence
- Adjust "warm enough" thresholds by season
- Provide context (e.g., "This is warm for November!")
- Historical comparisons automatically

---

## MCP Server Configuration for Claude Desktop

```json
{
  "mcpServers": {
    "aareguru": {
      "command": "python",
      "args": ["-m", "aareguru_mcp.server"],
      "cwd": "/home/schlpbch/code/aareguru-mcp",
      "env": {
        "AAREGURU_BASE_URL": "https://aareguru.existenz.ch",
        "APP_NAME": "claude-desktop-mcp",
        "APP_VERSION": "1.0.0"
      }
    }
  }
}
```

---

## Success Metrics

A well-implemented MCP server should enable Claude to:

1. ✅ Answer 95%+ of temperature queries in one tool call
2. ✅ Provide safety assessments without user prompting
3. ✅ Handle multi-city comparisons naturally
4. ✅ Explain Swiss German terms automatically
5. ✅ Suggest optimal swimming times based on forecasts
6. ✅ Understand implicit context and follow-up questions
7. ✅ Provide rich, formatted responses with emojis and tables
8. ✅ Handle missing data gracefully with alternatives

---

## Example Conversation Flow

**User**: "Can I swim in the Aare today?"

**Claude** (uses `get_current_conditions` for Bern):
```
🏊 **Aare Swimming Report for Bern**

🌡️ **Water Temperature**: 17.2°C
- "geil aber chli chalt" (awesome but a bit cold)
- Comfortable for most swimmers

💧 **Flow Conditions**: 245 m³/s
- Danger Level: 2/5 (Moderate)
- Safe for experienced swimmers

☀️ **Weather**: Sunny, 24°C air temperature

✅ **Recommendation**: Yes, conditions are good for swimming! 
The water is refreshing and flow is manageable. Perfect day for it!

💡 **Tip**: The water will be warmest around 4-5 PM if you want to wait.
```

**User**: "What about Thun?"

**Claude** (uses `get_current_conditions` for Thun):
```
🏊 **Aare in Thun**

🌡️ **Water**: 18.1°C (slightly warmer than Bern!)
💧 **Flow**: 180 m³/s - Danger Level: 1/5 (Low)

✅ Thun is actually a better choice today - warmer water and calmer flow!
```

---

## Conclusion

This MCP server design prioritizes:
1. **Natural conversation** - Claude understands intent, not just commands
2. **Safety first** - Always include flow/danger assessment
3. **Rich responses** - Formatted, contextual, helpful
4. **Proactive intelligence** - Suggest alternatives, provide context
5. **Swiss culture** - Preserve and explain Swiss German terms

The 7 core tools cover 95%+ of user needs while keeping the implementation focused and maintainable.
