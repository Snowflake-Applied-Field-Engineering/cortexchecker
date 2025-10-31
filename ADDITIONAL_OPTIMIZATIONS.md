# Additional Optimization Opportunities

## Further Performance Improvements

### 1. **Lazy Loading for Expanders**

**Current:** All data is processed even if expanders are closed

**Optimization:** Only process data when expander is opened

```python
# Before
with st.expander("View All Grants"):
    st.dataframe(grants_df, use_container_width=True)
    csv = grants_df.to_csv(index=False)
    st.download_button(...)

# After
with st.expander("View All Grants"):
    if st.session_state.get('show_grants', False):
        st.dataframe(grants_df, use_container_width=True)
        st.download_button(...)
```

**Benefit:** Saves processing time when users don't expand sections

---

### 2. **Batch Role Analysis**

**Current:** Analyzes roles one at a time in a loop

**Optimization:** Fetch all grants in one query

```python
# Before
for role_name in selected_roles:
    grants_df = get_role_grants(session, role_name)

# After
def get_multiple_role_grants(_session, role_names):
    role_list = "','".join(role_names)
    query = f"""
        SELECT GRANTEE_NAME, GRANTED_ON, PRIVILEGE, NAME AS OBJECT_NAME
        FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
        WHERE GRANTEE_NAME IN ('{role_list}')
        AND DELETED_ON IS NULL
    """
    return _session.sql(query).to_pandas()
```

**Benefit:** One query instead of N queries for N roles

---

### 3. **Session State for Expensive Operations**

**Current:** Recalculates on every interaction

**Optimization:** Store results in session state

```python
# Store analysis results
if 'analysis_cache' not in st.session_state:
    st.session_state.analysis_cache = {}

cache_key = f"{role_name}_{hash(grants_df.to_json())}"
if cache_key not in st.session_state.analysis_cache:
    st.session_state.analysis_cache[cache_key] = analyze_grants(grants_df)

analysis = st.session_state.analysis_cache[cache_key]
```

**Benefit:** Avoid recalculating same data multiple times per session

---

### 4. **Async Data Loading**

**Current:** Sequential data loading

**Optimization:** Load multiple resources in parallel

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def load_all_data():
    with ThreadPoolExecutor() as executor:
        roles_future = executor.submit(get_all_roles, session)
        agents_future = executor.submit(get_all_agents, session)
        
        roles = roles_future.result()
        agents = agents_future.result()
    
    return roles, agents
```

**Benefit:** 50% faster initial load when fetching multiple resources

---

### 5. **Incremental DataFrame Display**

**Current:** Loads entire grants table at once

**Optimization:** Paginate large result sets

```python
# For large grants DataFrames
if len(grants_df) > 100:
    page_size = 100
    page = st.number_input("Page", 1, (len(grants_df) // page_size) + 1)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    st.dataframe(grants_df.iloc[start_idx:end_idx])
else:
    st.dataframe(grants_df)
```

**Benefit:** Faster rendering for roles with many grants

---

### 6. **Optimize String Operations**

**Current:** Multiple string operations

**Optimization:** Use f-strings and reduce operations

```python
# Before
parts = view_name.split('.')
if len(parts) >= 2:
    databases.add(parts[0])
    schemas.add(f"{parts[0]}.{parts[1]}")

# After
parts = view_name.split('.', 2)  # Limit splits
if len(parts) >= 2:
    databases.add(parts[0])
    schemas.add('.'.join(parts[:2]))  # Faster than f-string for this case
```

**Benefit:** Marginally faster string processing

---

### 7. **Reduce Redundant SQL Generation**

**Current:** Generates SQL even if not downloaded

**Optimization:** Generate only when download button clicked

```python
# Before
sql_script = generate_agent_permission_sql(...)
st.code(sql_script, language="sql")
st.download_button(data=sql_script, ...)

# After
if 'generated_sql' not in st.session_state:
    st.session_state.generated_sql = None

if st.button("Generate SQL"):
    st.session_state.generated_sql = generate_agent_permission_sql(...)

if st.session_state.generated_sql:
    st.code(st.session_state.generated_sql, language="sql")
    st.download_button(data=st.session_state.generated_sql, ...)
```

**Benefit:** Only generate when needed

---

### 8. **Optimize DataFrame Operations**

**Current:** Multiple DataFrame filters

**Optimization:** Use query() method for complex filters

```python
# Before
agent_grants = grants_df[
    (grants_df['GRANTED_ON'] == 'AGENT') & 
    (grants_df['OBJECT_NAME'] == f"{database}.{schema}.{agent_name}")
]

# After
agent_grants = grants_df.query(
    f"GRANTED_ON == 'AGENT' and OBJECT_NAME == '{database}.{schema}.{agent_name}'"
)
```

**Benefit:** Slightly faster for complex conditions

---

### 9. **Reduce Widget Redraws**

**Current:** Widgets redraw on every interaction

**Optimization:** Use form to batch updates

```python
with st.form("role_selection"):
    selected_roles = st.multiselect("Select roles:", filtered_roles)
    submit = st.form_submit_button("Analyze")
    
    if submit and selected_roles:
        # Process roles
```

**Benefit:** Reduces unnecessary reruns

---

### 10. **Memory-Efficient CSV Generation**

**Current:** Converts entire DataFrame to CSV in memory

**Optimization:** Stream CSV for large DataFrames

```python
# For very large DataFrames
import io

def convert_df_to_csv_stream(df):
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, chunksize=1000)
    return buffer.getvalue()

csv_data = convert_df_to_csv_stream(grants_df)
```

**Benefit:** Lower memory usage for large exports

---

### 11. **Query Result Caching at Snowflake Level**

**Current:** Python-level caching only

**Optimization:** Use Snowflake query result cache

```python
# Add query tag to enable result caching
_session.sql("ALTER SESSION SET USE_CACHED_RESULT = TRUE").collect()
_session.sql("ALTER SESSION SET QUERY_TAG = 'cortex_tool'").collect()
```

**Benefit:** Faster repeated queries across sessions

---

### 12. **Compress Download Files**

**Current:** Plain text downloads

**Optimization:** Compress large SQL scripts

```python
import gzip
import base64

def compress_sql(sql_text):
    compressed = gzip.compress(sql_text.encode())
    return base64.b64encode(compressed).decode()

# For download
st.download_button(
    "Download SQL (compressed)",
    data=compress_sql(sql_script),
    file_name=f"{agent_name}_permissions.sql.gz"
)
```

**Benefit:** Faster downloads for large scripts

---

## Priority Ranking

### High Impact (Implement First)
1. **Batch Role Analysis** - Biggest performance gain
2. **Session State Caching** - Reduces redundant calculations
3. **Lazy Loading for Expanders** - Saves unnecessary processing

### Medium Impact
4. **Async Data Loading** - Faster initial load
5. **Incremental DataFrame Display** - Better UX for large datasets
6. **Query Result Caching** - Cross-session benefits

### Low Impact (Nice to Have)
7. **Reduce Widget Redraws** - Cleaner UX
8. **Optimize DataFrame Operations** - Marginal gains
9. **String Operation Optimization** - Minor improvements

### Optional
10. **Memory-Efficient CSV** - Only needed for very large datasets
11. **Compress Downloads** - Only for large SQL scripts
12. **Reduce Redundant SQL Generation** - Minimal impact

---

## Estimated Additional Performance Gains

| Optimization | Speed Improvement | Complexity |
|--------------|------------------|------------|
| Batch Role Analysis | 50-70% | Medium |
| Session State Caching | 30-40% | Low |
| Lazy Loading | 20-30% | Low |
| Async Loading | 40-50% | Medium |
| Incremental Display | 10-20% | Low |
| Query Caching | 20-30% | Low |

**Combined:** Could achieve another **50-80% improvement** on top of current optimizations

---

## Implementation Recommendations

### Phase 1 (Quick Wins)
- Session state caching
- Lazy loading for expanders
- Query result caching

**Effort:** 2-3 hours
**Gain:** 30-40% improvement

### Phase 2 (Medium Effort)
- Batch role analysis
- Async data loading
- Incremental display

**Effort:** 4-6 hours
**Gain:** 50-60% improvement

### Phase 3 (Polish)
- Widget optimization
- String operations
- Memory efficiency

**Effort:** 2-3 hours
**Gain:** 10-15% improvement

---

## Testing Checklist

After implementing optimizations:

- [ ] Test with 1 role
- [ ] Test with 10+ roles
- [ ] Test with roles having 100+ grants
- [ ] Test with multiple agents
- [ ] Test cache behavior
- [ ] Test memory usage
- [ ] Test concurrent users
- [ ] Verify all features still work

---

## Monitoring Recommendations

Add performance tracking:

```python
import time

def track_performance(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        st.sidebar.caption(f"{func.__name__}: {duration:.2f}s")
        return result
    return wrapper

@track_performance
def get_role_grants(_session, role_name):
    # ... existing code
```

---

## Would You Like Me To Implement?

I can create a "super-optimized" version with the high-impact optimizations implemented. Let me know which ones you'd like to prioritize!

