# 130 User Questions for Aareguru MCP Server

A comprehensive collection of user questions that Claude can answer using the
Aareguru MCP server.

---

## Category 1: Basic Temperature Queries

**10 Questions**

1. What's the Aare temperature right now?
2. How cold is the water in Bern?
3. Is the Aare warm enough to swim?
4. What's the current water temperature?
5. Can you check the Aare temp for me?
6. How many degrees is the water?
7. Is it too cold to swim today?
8. What's the water like in Thun?
9. Temperature check for Basel please
10. How warm is the Aare in Olten?

---

## Category 2: Safety & Flow Questions

**10 Questions**

11. Is it safe to swim in the Aare today?
12. What's the current danger level?
13. How strong is the current?
14. Is the flow rate dangerous?
15. Should I be worried about the current?
16. What's the BAFU danger assessment?
17. Is the water flowing too fast?
18. Can beginners swim safely today?
19. What's the flow rate in m³/s?
20. Is there a flood warning?

---

## Category 3: Weather Integration

**10 Questions**

21. What's the weather like for swimming?
22. Is it sunny enough to go to the Aare?
23. Will it rain while I'm swimming?
24. What's the air temperature vs water temperature?
25. Is it a good day for the Aare?
26. Should I bring sunscreen?
27. What's the UV index?
28. Is it windy by the river?
29. What's the weather forecast for swimming?
30. Will it be sunny this afternoon?

---

## Category 4: Comparative Questions

**10 Questions**

31. Which city has the warmest water?
32. Compare Bern and Thun temperatures
33. Where's the best place to swim today?
34. Is Basel warmer than Bern?
35. Which location has the calmest water?
36. Show me all cities above 18 degrees
37. Where should I go swimming?
38. Which spot is safest for kids?
39. Compare all available locations
40. What's the coldest spot today?

---

## Category 5: Historical & Trend Questions

**10 Questions**

41. How has the temperature changed this week?
42. Is it warmer than yesterday?
43. Show me the last 7 days of data
44. What was the temperature last weekend?
45. Is this normal for this time of year?
46. When was the water warmest this month?
47. How does today compare to last year?
48. What's the average temperature in August?
49. Show me temperature trends
50. Has the water been getting warmer?

---

## Category 6: Forecast Questions

**10 Questions**

51. Will the water be warmer tomorrow?
52. What's the forecast for this weekend?
53. Should I wait until later to swim?
54. When will it be warmest today?
55. Is the temperature rising or falling?
56. What's the 2-hour forecast?
57. Will conditions improve?
58. Should I swim now or later?
59. What's the outlook for next week?
60. When's the best time to swim today?

---

## Category 7: Location Discovery

**10 Questions**

61. Where can I check Aare temperatures?
62. Which cities have data available?
63. List all swimming spots
64. What locations are monitored?
65. Do you have data for Interlaken?
66. Which cities can I query?
67. Show me all available locations
68. Where are the measurement stations?
69. What's the closest monitored spot to Zurich?
70. Are there any new locations?

---

## Category 8: Contextual & Complex Questions

**10 Questions**

71. I'm planning to swim at 5 PM, what will conditions be like?
72. Is it a good day for Aare swimming (Aareböötle)?
73. What should I know before swimming today?
74. Give me a full swimming report
75. Is it safe for my kids to swim?
76. What gear should I bring based on conditions?
77. How long can I safely stay in the water?
78. Is the water quality good today?
79. What's the visibility like?
80. Should I wear a wetsuit?

---

## Category 9: Conversational Questions

**10 Questions**

81. How's the Aare looking today?
82. Is it Aare weather?
83. Should I go for a swim?
84. What do you think about swimming conditions?
85. Is it worth going to the river?
86. Would you recommend swimming today?
87. Talk me through the current conditions
88. What's the vibe at the Aare?
89. Is everyone swimming today?
90. What's the Swiss German temperature description?

---

## Category 10: Data Analysis Questions

**10 Questions**

91. What's the warmest the Aare has been this year?
92. Calculate the average temperature for July
93. Show me a temperature graph for the month
94. What's the temperature variance this week?
95. How often does it exceed 20°C?
96. What's the median flow rate?
97. Analyze temperature patterns
98. What's the correlation between air and water temp?
99. Show me daily temperature ranges
100.  What's the standard deviation?

---

## Category 11: Specific Use Cases

**10 Questions**

101. I'm a tourist, where should I swim?
102. Best spot for Aare floating?
103. Where do locals swim in Bern?
104. Is Marzili good today?
105. What about the Aare in Thun for SUP?
106. Good conditions for kayaking?
107. Is it safe for wild swimming?
108. Can I bring my dog to swim?
109. Best time of day for swimming?
110. Is the Aare crowded when it's this warm?

---

## Category 12: Multi-Step Queries

**10 Questions**

111. Check Bern temperature, then compare with Thun
112. Show me today's conditions and tomorrow's forecast
113. List cities, then show me the warmest one
114. Get historical data and predict tomorrow
115. Compare all cities and recommend the best
116. Check danger level, then give safety advice
117. Show current temp and last week's average
118. Get forecast and historical comparison
119. Find warmest city and check its flow rate
120. Analyze trends and predict peak time

---

## Category 13: Edge Cases & Special Requests

**10 Questions**

121. What if there's no data available?
122. Show me cities with missing data
123. What's the data update frequency?
124. When was the last measurement?
125. Is the sensor working in Basel?
126. What's the data source?
127. How accurate are the measurements?
128. What's the margin of error?
129. Can you explain the danger levels?
130. What does 'geil aber chli chalt' mean?

---

## Summary by Category

| Category             | Count   | Focus Area                |
| -------------------- | ------- | ------------------------- |
| Basic Temperature    | 10      | Simple temp queries       |
| Safety & Flow        | 10      | Current strength & danger |
| Weather Integration  | 10      | Weather conditions        |
| Comparative          | 10      | Multi-city comparison     |
| Historical & Trends  | 10      | Past data analysis        |
| Forecast             | 10      | Future predictions        |
| Location Discovery   | 10      | Available cities          |
| Contextual & Complex | 10      | Detailed scenarios        |
| Conversational       | 10      | Natural language          |
| Data Analysis        | 10      | Statistical queries       |
| Specific Use Cases   | 10      | Activity-based            |
| Multi-Step           | 10      | Complex workflows         |
| Edge Cases           | 10      | Error handling            |
| **Total**            | **130** | **Complete coverage**     |

---

## Tool Mapping

### Which tools answer which questions?

**`get_current_temperature`** → Categories 1, 9

- Quick temperature checks
- Simple conversational queries

**`get_current_conditions`** → Categories 2, 3, 8

- Safety assessments
- Weather integration
- Full swimming reports

**`get_historical_data`** → Categories 5, 10

- Trend analysis
- Statistical queries
- Historical comparisons

**`list_cities`** → Category 7

- Location discovery
- Available spots

**`get_flow_danger_level`** → Category 2

- Safety-critical queries
- Flow rate checks

**`get_forecast`** → Category 3

- Future predictions
- Optimal timing

---

## Coverage Analysis

### Question Complexity Distribution

```
Simple (1 tool call):        ~60 questions (46%)
Moderate (2-3 tool calls):   ~50 questions (38%)
Complex (4+ tool calls):     ~20 questions (16%)
```

### Expected Response Time

```
Simple:    < 1 second
Moderate:  1-3 seconds
Complex:   3-5 seconds
```

### Success Rate Goals

```
✅ Single-turn resolution:  95%+
✅ Accurate responses:      98%+
✅ Helpful formatting:      100%
```

---

## Implementation Priority

### Phase 1 (MVP) - 70% Coverage

Tools: 1-5

- Categories 1, 2, 5, 7, 9
- ~90 questions covered

### Phase 2 (Enhanced) - 95% Coverage

Tools: 6-7

- Categories 3, 4, 6, 8, 10, 11
- ~123 questions covered

### Phase 3 (Complete) - 100% Coverage

All tools + error handling

- Categories 12, 13
- All 130 questions covered

---

## Testing Strategy

### Sample Test Cases

**Category 1 (Basic)**:

```
Q: "What's the Aare temperature in Bern?"
Expected: Temperature + Swiss German + swimming status
Tool: get_current_temperature
```

**Category 4 (Temporal)**:

```
Q: "Will the water be warmer in 2 hours?"
Expected: Current temp → forecast → recommendation
Tool: get_forecast
```

---

## User Experience Goals

### Response Quality

Every response should include:

1. ✅ **Direct answer** to the question
2. ✅ **Context** (Swiss German, safety notes)
3. ✅ **Formatting** (emojis, tables, bullets)
4. ✅ **Proactive info** (suggestions, warnings)

### Example Perfect Response

**Question**: "Is it safe to swim in Bern today?"

**Response**:

```markdown
🏊 **Aare Swimming Safety Report - Bern**

🌡️ **Water Temperature**: 17.2°C

- "geil aber chli chalt" (awesome but a bit cold)
- Comfortable for most swimmers

💧 **Flow Conditions**: 245 m³/s

- Danger Level: 2/5 (Moderate)
- Safe for experienced swimmers

☀️ **Weather**: Sunny, 24°C

✅ **Verdict**: Yes, it's safe to swim! Conditions are good. Be aware of the
current strength.

💡 **Tip**: Water will be warmest around 4-5 PM.
```

---

## Conclusion

These 130 questions represent the comprehensive scope of user needs for the
Aareguru MCP server, ensuring Claude can provide helpful, accurate, and
contextual responses for all swimming-related queries about the Aare river.
