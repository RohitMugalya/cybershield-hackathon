import re

with open('app2.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace use_column_width=True with width="stretch"
code = code.replace('use_column_width=True', 'use_container_width=True')

# Replace use_container_width=True in specific components
# We must avoid st.button as use_container_width=True is still valid for st.button.
# For dataframe, plotly_chart, pydeck_chart, image:

def replacer(match):
    prefix = match.group(1)
    return prefix + ', width="stretch"'

# Match st.plotly_chart(..., use_container_width=True)
code = re.sub(r'(st\.plotly_chart\([^)]*),\s*use_container_width=True', replacer, code)
# Match st.dataframe(..., use_container_width=True)
code = re.sub(r'(st\.dataframe\([^)]*),\s*use_container_width=True', replacer, code)
# Match st.pydeck_chart(..., use_container_width=True)
code = re.sub(r'(st\.pydeck_chart\([^)]*),\s*use_container_width=True', replacer, code)

# Match .image(..., use_container_width=True)
code = re.sub(r'(\.image\([^)]*),\s*use_container_width=True', r'\1, width="stretch"', code)
code = re.sub(r'(st\.image\([^)]*),\s*use_container_width=True', r'\1, width="stretch"', code)

code = code.replace('use_container_width=True, height=450', 'width="stretch", height=450')
code = code.replace('use_container_width=True, height=500', 'width="stretch", height=500')

# Also, user asked for frame rate drop or quality drop to increase smoothness.
# Let's adjust frame_skip in app2.py
code = code.replace('frame_skip = 5', 'frame_skip = 8')
code = code.replace('frame_skip = 3 if HAS_CUDA else 5', 'frame_skip = 4 if HAS_CUDA else 7')

with open('app2.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Updated app2.py with deprecation fixes and frame skip optimizations.')
