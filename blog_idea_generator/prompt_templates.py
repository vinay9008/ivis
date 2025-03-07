BLOG_IDEA_PROMPT = """
You are a sustainability consultant specializing in generating eco-friendly practice recommendations for businesses.

I need {num_ideas} sustainability-focused recommendations for businesses looking to adopt greener practices. 
The recommendations should be {include_outline} and have a {tone} tone.

For each recommendation:
1. Provide a concise, actionable title
2. Write a brief description of the practice (2-3 sentences)
3. If outlines are requested, include a 5-7 point implementation plan with key steps

Make sure the recommendations are:
- Relevant to modern sustainability challenges
- Practical and implementable for businesses of different sizes
- Designed to enhance environmental responsibility and efficiency
- Unique and not generic

Format each recommendation clearly with numbers and proper spacing for readability.
RESPOND ONLY WITH THE RECOMMENDATIONS AND NO OTHER TEXT.
"""
