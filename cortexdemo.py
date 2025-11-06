"""
Cortex Tool - Combined Role Checker & Agent Permission Generator
Optimized version with improved performance and efficiency
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
import fnmatch
from datetime import datetime
import json
import re
from functools import lru_cache

# Set page configuration
st.set_page_config(
    layout="wide", 
    page_title="Snowflake Cortex Security Hub",
    page_icon="🔐"
)

# ------------------------------------
# Utility Functions
# ------------------------------------

@st.cache_data(show_spinner="Fetching available roles...", ttl=300)
def get_all_roles(_session):
    """Fetches all roles visible to the Streamlit app owner/session."""
    try:
        # More efficient query - only get what we need
        roles_df = _session.sql(
            "SELECT DISTINCT NAME FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES "
            "WHERE DELETED_ON IS NULL ORDER BY NAME"
        ).to_pandas()
        # Remove duplicates and return unique list (Issue #2 fix)
        return sorted(list(set(roles_df['NAME'].tolist())))
    except Exception as e:
        st.error(f"Could not query roles from ACCOUNT_USAGE. Error: {e}")
        try:
            roles_df = _session.sql(
                "SELECT DISTINCT ROLE_NAME FROM INFORMATION_SCHEMA.ROLES ORDER BY ROLE_NAME"
            ).to_pandas()
            # Remove duplicates and return unique list (Issue #2 fix)
            return sorted(list(set(roles_df['ROLE_NAME'].tolist())))
        except Exception as e_fallback:
            st.error(f"Failed to retrieve roles. Error: {e_fallback}")
            return []

@st.cache_data(show_spinner="Fetching agents...", ttl=300)
def get_all_agents(_session, database=None, schema=None):
    """Fetch all Cortex Agents in the account or specific database/schema."""
    try:
        if database and schema:
            query = f"SHOW AGENTS IN SCHEMA {database}.{schema}"
        elif database:
            query = f"SHOW AGENTS IN DATABASE {database}"
        else:
            query = "SHOW AGENTS IN ACCOUNT"
        
        agents_df = _session.sql(query).to_pandas()
        
        # Issue #3 fix: Handle empty results and normalize column names
        if agents_df.empty:
            return []
        
        # Normalize column names - remove quotes and convert to lowercase
        agents_df.columns = [col.strip('"').lower() for col in agents_df.columns]
        
        # SHOW AGENTS can return different column formats depending on Snowflake version
        # Try to map common column name variations
        name_col = None
        db_col = None
        schema_col = None
        
        # Find the right column names
        for col in agents_df.columns:
            if col in ['name', 'agent_name']:
                name_col = col
            elif col in ['database_name', 'database']:
                db_col = col
            elif col in ['schema_name', 'schema']:
                schema_col = col
        
        # Check if we found all required columns
        if not name_col or not db_col or not schema_col:
            st.warning(f"Could not find required columns in SHOW AGENTS. Available columns: {agents_df.columns.tolist()}")
            return []
        
        return [
            {'name': row[name_col], 'database': row[db_col], 'schema': row[schema_col]} 
            for _, row in agents_df.iterrows()
        ]
    except Exception as e:
        st.warning(f"Could not fetch agents: {e}")
        return []

@st.cache_data(show_spinner="Analyzing agent...", ttl=300)
def describe_agent(_session, database, schema, agent_name):
    """Get detailed information about a Cortex Agent."""
    try:
        # Properly quote identifiers to handle special characters like hyphens and spaces
        query = f'DESCRIBE AGENT "{database}"."{schema}"."{agent_name}"'
        result_df = _session.sql(query).to_pandas()
        
        if result_df.empty:
            st.error("Agent description returned no data")
            return None
        
        # Normalize column names - remove quotes and convert to lowercase
        result_df.columns = [col.strip('"').lower() for col in result_df.columns]
        
        # DESCRIBE AGENT returns a single row with columns: name, database_name, schema_name, 
        # owner, comment, profile, agent_spec, created_on
        # Convert the first row to a dictionary
        agent_info = result_df.iloc[0].to_dict()
        
        # Debug: Show what we have
        with st.expander("Debug: Raw Agent Info"):
            st.write("Available keys:", list(agent_info.keys()))
            for key, value in agent_info.items():
                st.write(f"**{key}**: type={type(value)}, is_null={value is None}, is_empty={not value if value is not None else 'N/A'}")
        
        # Try to parse agent_spec or profile for tools
        agent_spec_value = agent_info.get('agent_spec')
        profile_value = agent_info.get('profile')
        
        # Check if agent_spec is actually empty (pandas NaN shows as empty string)
        if pd.isna(agent_spec_value) or agent_spec_value == '' or agent_spec_value is None:
            st.info("agent_spec is empty, trying profile field...")
            agent_spec_value = None
        
        # Try profile if agent_spec is empty
        if agent_spec_value is None and profile_value:
            if not pd.isna(profile_value) and profile_value != '':
                st.info("Using profile field for agent configuration")
                agent_spec_value = profile_value
        
        if agent_spec_value:
            try:
                # Handle different types
                if isinstance(agent_spec_value, bytes):
                    agent_spec_value = agent_spec_value.decode('utf-8')
                
                if isinstance(agent_spec_value, str):
                    agent_spec = json.loads(agent_spec_value)
                elif isinstance(agent_spec_value, dict):
                    agent_spec = agent_spec_value
                else:
                    st.warning(f"Unexpected agent_spec type: {type(agent_spec_value)}")
                    agent_spec = None
                
                if agent_spec:
                    # Debug: Show what we got
                    with st.expander("Debug: Parsed Agent Spec"):
                        st.write("Agent spec type:", type(agent_spec))
                        if isinstance(agent_spec, dict):
                            st.write("Agent spec keys:", list(agent_spec.keys()))
                        st.json(agent_spec)
                    
                    # Extract tools from agent_spec - try multiple possible locations
                    tools_found = None
                    
                    if isinstance(agent_spec, dict):
                        # Try direct 'tools' key
                        if 'tools' in agent_spec:
                            tools_found = agent_spec['tools']
                            st.success(f"Found {len(tools_found)} tools in agent_spec['tools']")
                        # Try 'definition' -> 'tools' path
                        elif 'definition' in agent_spec and isinstance(agent_spec['definition'], dict):
                            if 'tools' in agent_spec['definition']:
                                tools_found = agent_spec['definition']['tools']
                                st.success(f"Found {len(tools_found)} tools in agent_spec['definition']['tools']")
                        # Try 'spec' -> 'tools' path
                        elif 'spec' in agent_spec and isinstance(agent_spec['spec'], dict):
                            if 'tools' in agent_spec['spec']:
                                tools_found = agent_spec['spec']['tools']
                                st.success(f"Found {len(tools_found)} tools in agent_spec['spec']['tools']")
                        
                        if tools_found:
                            agent_info['tools'] = tools_found
                            
                            # Also extract tool_resources if available (contains semantic_view references)
                            if 'tool_resources' in agent_spec:
                                agent_info['tool_resources'] = agent_spec['tool_resources']
                                st.info(f"Found tool_resources with {len(agent_spec['tool_resources'])} entries")
                        else:
                            # Maybe tools are at a different path
                            st.info(f"No 'tools' key found in agent_spec. Available keys: {list(agent_spec.keys())}")
                            # Check nested structures
                            for key, value in agent_spec.items():
                                if isinstance(value, dict):
                                    st.info(f"  Nested structure in '{key}': {list(value.keys())}")
            except Exception as e:
                st.warning(f"Could not parse agent_spec: {e}")
                st.code(f"Raw value: {repr(agent_spec_value)[:500]}")
        else:
            st.warning("Both agent_spec and profile are empty - agent may not have tools configured yet")
        
        return agent_info
    except Exception as e:
        st.error(f"Failed to describe agent: {e}")
        return None

def parse_agent_tools(agent_info):
    """Parse tools from agent description."""
    if 'tools' not in agent_info:
        return []
    
    try:
        tools_data = json.loads(agent_info['tools']) if isinstance(agent_info['tools'], str) else agent_info['tools']
        return tools_data if isinstance(tools_data, list) else []
    except:
        return []

def extract_tool_resources(tools):
    """Extract all resources (views, services, procedures) from tools in one pass."""
    semantic_views = []
    search_services = []
    procedures = []
    
    for tool in tools:
        tool_type = tool.get('type')
        if tool_type == 'cortex_analyst_text_to_sql' and 'semantic_model' in tool:
            semantic_views.append(tool['semantic_model'])
        elif tool_type == 'cortex_search' and 'search_service' in tool:
            search_services.append(tool['search_service'])
        elif tool_type == 'generic' and 'procedure' in tool:
            procedures.append(tool['procedure'])
    
    return semantic_views, search_services, procedures

@st.cache_data(show_spinner="Analyzing semantic view...", ttl=300)
def get_semantic_view_yaml(_session, view_name):
    """Get YAML definition from semantic view."""
    try:
        result_df = _session.sql(
            f"SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('{view_name}') as yaml_def"
        ).to_pandas()
        if not result_df.empty:
            # Try different possible column names
            for col_name in ['yaml_def', 'YAML_DEF', result_df.columns[0]]:
                if col_name in result_df.columns:
                    return result_df.iloc[0][col_name]
        return None
    except Exception as e:
        st.warning(f"Could not read YAML from {view_name}: {e}")
        return None

# Compile regex pattern once for better performance
TABLE_PATTERN = re.compile(r'(?:table|from):\s*([A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*)', re.IGNORECASE)

def parse_tables_from_yaml(yaml_content):
    """Extract table references from semantic view YAML."""
    if not yaml_content:
        return []
    return list(set(TABLE_PATTERN.findall(yaml_content)))

def test_cortex_access(_session, role_name):
    """
    Test if a role has actual Cortex access by attempting to use COMPLETE function.
    This catches implicit grants like PUBLIC role having CORTEX_USER by default.
    """
    try:
        # Try to use the role and call a Cortex function
        test_query = f"""
            USE ROLE {role_name};
            SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic', 'test') AS test_result;
        """
        # We don't care about the result, just if it works
        _session.sql(f"USE ROLE {role_name}").collect()
        _session.sql("SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic', 'Hi') AS test_result").collect()
        return True
    except Exception as e:
        error_msg = str(e).lower()
        # If error is about privileges, role doesn't have Cortex access
        if 'privilege' in error_msg or 'permission' in error_msg or 'not authorized' in error_msg:
            return False
        # Other errors might be transient, so we'll be conservative
        return False
    finally:
        # Always try to switch back to original role
        try:
            _session.sql("USE ROLE SYSADMIN").collect()
        except:
            pass

@st.cache_data(show_spinner="Analyzing grants...", ttl=300)
def get_role_grants(_session, role_name):
    """Fetches all grants granted to the specified role - optimized query."""
    role_name_upper = role_name.upper()
    
    try:
        # Optimized query - select only needed columns
        query = f"""
            SELECT 
                GRANTED_ON,
                PRIVILEGE,
                CASE WHEN GRANTED_ON = 'ROLE' THEN NAME ELSE NULL END AS GRANTED_ROLE,
                NAME AS OBJECT_NAME
            FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
            WHERE GRANTEE_NAME = '{role_name_upper}' 
              AND DELETED_ON IS NULL
            ORDER BY GRANTED_ON, NAME
        """
        
        # Convert directly to pandas for better performance
        grants_df = _session.sql(query).to_pandas()
        
        if grants_df.empty:
            return pd.DataFrame(columns=['GRANTED_ON', 'PRIVILEGE', 'GRANTED_ROLE', 'OBJECT_NAME'])
        
        return grants_df
        
    except Exception as e:
        st.warning(f"Failed to query ACCOUNT_USAGE for {role_name}. Error: {str(e)[:200]}")
        return pd.DataFrame(columns=['GRANTED_ON', 'PRIVILEGE', 'GRANTED_ROLE', 'OBJECT_NAME'])

def analyze_grants(grants_df, actual_cortex_access=None, role_name=None):
    """
    Analyze grants DataFrame and return all metrics in one pass - more efficient.
    
    Args:
        grants_df: DataFrame of grants
        actual_cortex_access: Optional boolean from actual Cortex function test
        role_name: Optional role name for display purposes
    """
    if grants_df.empty:
        return {
            'has_cortex': actual_cortex_access if actual_cortex_access is not None else False,
            'cortex_method': 'implicit' if actual_cortex_access else 'none',
            'found_roles': [],
            'wh_count': 0,
            'db_count': 0,
            'table_count': 0,
            'readiness_score': 0,
            'issues': ['No grants found']
        }
    
    # Check explicit Cortex role grants
    required_roles = ['SNOWFLAKE.CORTEX_USER', 'SNOWFLAKE.CORTEX_ANALYST_USER']
    granted_roles = grants_df[grants_df['GRANTED_ROLE'].notna()]['GRANTED_ROLE'].str.upper().unique()
    found_roles = [role for role in required_roles if role in granted_roles]
    has_explicit_cortex = len(found_roles) > 0
    
    # Determine actual Cortex access
    if actual_cortex_access is not None:
        # Use actual test result
        has_cortex = actual_cortex_access
        if actual_cortex_access and not has_explicit_cortex:
            cortex_method = 'implicit'  # Has access but not via explicit grant (e.g., PUBLIC role)
        elif actual_cortex_access and has_explicit_cortex:
            cortex_method = 'explicit'  # Has explicit grant
        else:
            cortex_method = 'none'
    else:
        # Fall back to grant-based detection
        has_cortex = has_explicit_cortex
        cortex_method = 'explicit' if has_explicit_cortex else 'none'
    
    # Count resources in one pass using groupby
    counts = grants_df.groupby('GRANTED_ON')['OBJECT_NAME'].nunique()
    wh_count = counts.get('WAREHOUSE', 0)
    db_count = counts.get('DATABASE', 0)
    table_count = counts.get('TABLE', 0) + counts.get('VIEW', 0)
    
    # Calculate readiness
    readiness_score = 0
    issues = []
    
    if has_cortex:
        readiness_score += 1
    else:
        issues.append("Missing CORTEX_USER or CORTEX_ANALYST_USER role")
    
    if wh_count > 0:
        readiness_score += 1
    else:
        issues.append("No warehouse USAGE privileges")
    
    if db_count > 0:
        readiness_score += 1
    else:
        issues.append("No database or schema access")
    
    if table_count > 0:
        readiness_score += 1
    else:
        issues.append("No SELECT privileges on tables/views")
    
    return {
        'has_cortex': has_cortex,
        'cortex_method': cortex_method,
        'found_roles': found_roles,
        'wh_count': wh_count,
        'db_count': db_count,
        'table_count': table_count,
        'readiness_score': readiness_score,
        'issues': issues
    }

def generate_agent_permission_sql(agent_name, database, schema, tools, semantic_views_data, role_name=None):
    """Generate comprehensive SQL for agent permissions - optimized with list comprehension."""
    if not role_name:
        role_name = f"{agent_name}_USER_ROLE"
    
    # Use list for better performance than repeated string concatenation
    sql_lines = [
        "-- " + "="*80,
        f"-- AUTO-GENERATED LEAST-PRIVILEGE SCRIPT FOR AGENT: {database}.{schema}.{agent_name}",
        f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- Generated by: Cortex Tool",
        "-- " + "="*80,
        "",
        "-- IMPORTANT: Review and adjust the placeholder variables below.",
        f"SET AGENT_ROLE_NAME = '{role_name}';",
        "SET WAREHOUSE_NAME = 'COMPUTE_WH';",
        "",
        "-- Create role",
        "USE ROLE SECURITYADMIN;",
        "CREATE ROLE IF NOT EXISTS IDENTIFIER($AGENT_ROLE_NAME);",
        "GRANT ROLE IDENTIFIER($AGENT_ROLE_NAME) TO ROLE SYSADMIN;",
        "",
        "-- Grant agent usage",
        f'GRANT USAGE ON AGENT "{database}"."{schema}"."{agent_name}" TO ROLE IDENTIFIER($AGENT_ROLE_NAME);',
        ""
    ]
    
    # Collect databases and schemas efficiently
    databases = {database}
    schemas = {f"{database}.{schema}"}
    
    # Process semantic views
    if semantic_views_data:
        sql_lines.extend([
            "-- Semantic view permissions",
            ""
        ])
        for view_info in semantic_views_data:
            view_name = view_info['view']
            sql_lines.append(f"GRANT SELECT ON VIEW {view_name} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
            
            # Extract database/schema
            parts = view_name.split('.')
            if len(parts) >= 2:
                databases.add(parts[0])
                schemas.add(f"{parts[0]}.{parts[1]}")
            
            # Add table grants
            if view_info.get('tables'):
                sql_lines.extend(["", "-- Base table permissions"])
                for table in view_info['tables']:
                    sql_lines.append(f"GRANT SELECT ON TABLE {table} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
                    parts = table.split('.')
                    if len(parts) >= 2:
                        databases.add(parts[0])
                        schemas.add(f"{parts[0]}.{parts[1]}")
        sql_lines.append("")
    
    # Process search services and procedures
    semantic_views, search_services, procedures = extract_tool_resources(tools)
    
    if search_services:
        sql_lines.extend(["-- Search service permissions", ""])
        for service in search_services:
            sql_lines.append(f"GRANT USAGE ON CORTEX SEARCH SERVICE {service} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
            parts = service.split('.')
            if len(parts) >= 2:
                databases.add(parts[0])
                schemas.add(f"{parts[0]}.{parts[1]}")
        sql_lines.append("")
    
    if procedures:
        sql_lines.extend(["-- Procedure permissions", ""])
        for proc in procedures:
            sql_lines.append(f"GRANT USAGE ON PROCEDURE {proc} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
            parts = proc.split('.')
            if len(parts) >= 2:
                databases.add(parts[0])
                schemas.add(f"{parts[0]}.{parts[1]}")
        sql_lines.append("")
    
    # Grant database and schema usage
    sql_lines.extend(["-- Database and schema permissions", ""])
    for db in sorted(databases):
        sql_lines.append(f"GRANT USAGE ON DATABASE {db} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
    for sch in sorted(schemas):
        sql_lines.append(f"GRANT USAGE ON SCHEMA {sch} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
    
    sql_lines.extend([
        "",
        "-- Warehouse permission",
        "GRANT USAGE ON WAREHOUSE IDENTIFIER($WAREHOUSE_NAME) TO ROLE IDENTIFIER($AGENT_ROLE_NAME);",
        "",
        "-- " + "="*80,
        "SELECT 'Setup complete for role ' || $AGENT_ROLE_NAME AS \"Status\";",
        "-- " + "="*80
    ])
    
    return "\n".join(sql_lines)

def generate_role_remediation_sql(role_name, issues):
    """Generate SQL commands to fix missing permissions."""
    sql_commands = [
        f"-- Remediation SQL for role: {role_name}",
        f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    if "Missing CORTEX_USER or CORTEX_ANALYST_USER role" in issues:
        sql_commands.extend([
            "-- Grant Cortex database role",
            f"GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE {role_name};",
            ""
        ])
    
    if "No warehouse USAGE privileges" in issues:
        sql_commands.extend([
            "-- Grant warehouse access",
            f"GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE {role_name};",
            ""
        ])
    
    if "No database or schema access" in issues:
        sql_commands.extend([
            "-- Grant database and schema access",
            f"GRANT USAGE ON DATABASE <DATABASE_NAME> TO ROLE {role_name};",
            f"GRANT USAGE ON SCHEMA <DATABASE_NAME>.<SCHEMA_NAME> TO ROLE {role_name};",
            ""
        ])
    
    if "No SELECT privileges on tables/views" in issues:
        sql_commands.extend([
            "-- Grant SELECT on tables",
            f"GRANT SELECT ON ALL TABLES IN SCHEMA <DATABASE_NAME>.<SCHEMA_NAME> TO ROLE {role_name};",
            f"GRANT SELECT ON ALL VIEWS IN SCHEMA <DATABASE_NAME>.<SCHEMA_NAME> TO ROLE {role_name};",
            ""
        ])
    
    if not issues:
        sql_commands.append("-- No issues found! Role is fully ready.")
    
    return "\n".join(sql_commands)

# ------------------------------------
# Main Application
# ------------------------------------

def main():
    # Hero section with better branding
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem 0 1rem 0;'>
        <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>
            🔐 Snowflake Cortex Security Hub
        </h1>
        <p style='font-size: 1.2rem; color: #888; margin-bottom: 0.5rem;'>
            Intelligent Permission Management for Cortex AI Agents
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🔍 Role Analysis")
        st.markdown("Validate role permissions for Cortex readiness")
    with col2:
        st.markdown("### ⚙️ Auto-Generate SQL")
        st.markdown("Create least-privilege scripts instantly")
    with col3:
        st.markdown("### 🎯 Deep Scanning")
        st.markdown("Extract dependencies from semantic views")
    
    st.markdown("---")
    
    # Get session
    try:
        session = get_active_session()
    except Exception:
        st.error("This application must be run as a Streamlit in Snowflake app.")
        st.stop()
    
    # Sidebar navigation
    st.sidebar.header("Tool Selection")
    tool_mode = st.sidebar.radio(
        "Choose a tool:",
        ["Role Permission Checker", "Agent Permission Generator", "Combined Analysis"],
        help="Select which functionality to use"
    )
    
    st.sidebar.markdown("---")
    
    # Add refresh button
    if st.sidebar.button("Refresh Data", help="Clear cache and reload data"):
        st.cache_data.clear()
        st.rerun()
    
    # ------------------------------------
    # Mode 1: Role Permission Checker
    # ------------------------------------
    if tool_mode == "Role Permission Checker":
        st.header("Role Permission Checker")
        st.markdown("Analyze Snowflake roles for Cortex Analyst readiness")
        
        all_roles = get_all_roles(session)
        
        if all_roles:
            # Search functionality
            search_term = st.sidebar.text_input("Search roles:", placeholder="Type to filter roles...")
            
            filtered_roles = [r for r in all_roles if search_term.upper() in r.upper()] if search_term else all_roles
            
            st.sidebar.caption(f"Showing {len(filtered_roles)} of {len(all_roles)} roles")
            
            # Bulk analysis
            with st.sidebar.expander("Bulk Analysis"):
                pattern = st.text_input("Analyze roles matching pattern:", placeholder="e.g., ANALYST_*")
                if pattern and st.button("Analyze All Matching"):
                    matching_roles = [r for r in all_roles if fnmatch.fnmatch(r.upper(), pattern.upper())]
                    if matching_roles:
                        st.success(f"Found {len(matching_roles)} matching roles")
                        filtered_roles = matching_roles
            
            # Role selection
            selected_roles = st.sidebar.multiselect(
                "Select roles to analyze:",
                options=filtered_roles,
                default=[],
                help="Select one or more roles"
            )
            
            if selected_roles:
                for role_name in selected_roles:
                    with st.expander(f"Analysis: {role_name}", expanded=len(selected_roles) == 1):
                        grants_df = get_role_grants(session, role_name)
                        
                        if not grants_df.empty:
                            # Test actual Cortex access (catches implicit grants like PUBLIC role)
                            with st.spinner("Testing Cortex access..."):
                                actual_access = test_cortex_access(session, role_name)
                            
                            # Analyze grants with actual test result
                            analysis = analyze_grants(grants_df, actual_cortex_access=actual_access, role_name=role_name)
                            
                            # Metrics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            # Show Cortex access with method indicator
                            cortex_display = "Yes"
                            if analysis['has_cortex']:
                                if analysis['cortex_method'] == 'implicit':
                                    cortex_display = "Yes (implicit)"
                                elif analysis['cortex_method'] == 'explicit':
                                    cortex_display = "Yes (explicit)"
                            else:
                                cortex_display = "No"
                            
                            col1.metric("Cortex Access", cortex_display)
                            col2.metric("Warehouses", analysis['wh_count'])
                            col3.metric("Databases", analysis['db_count'])
                            col4.metric("Tables/Views", analysis['table_count'])
                            
                            # Add explanation for implicit access
                            if analysis['cortex_method'] == 'implicit':
                                st.info("This role has Cortex access via implicit grant (e.g., PUBLIC role has CORTEX_USER by default)")
                            
                            # Readiness display
                            progress_pct = analysis['readiness_score'] / 4
                            
                            if progress_pct == 1.0:
                                st.success(f"**FULLY READY** - Score: {analysis['readiness_score']}/4")
                            elif progress_pct >= 0.75:
                                st.warning(f"**MOSTLY READY** - Score: {analysis['readiness_score']}/4")
                            else:
                                st.error(f"**NOT READY** - Score: {analysis['readiness_score']}/4")
                            
                            st.progress(progress_pct)
                            
                            if analysis['issues']:
                                st.markdown("**Issues to Address:**")
                                for issue in analysis['issues']:
                                    st.markdown(f"- {issue}")
                                
                                # Remediation SQL
                                with st.expander("View Remediation SQL"):
                                    sql_script = generate_role_remediation_sql(role_name, analysis['issues'])
                                    st.code(sql_script, language="sql")
                                    st.download_button(
                                        label="Download SQL Script",
                                        data=sql_script,
                                        file_name=f"fix_{role_name}_permissions.sql",
                                        mime="text/plain",
                                        key=f"download_remediation_{role_name}"
                                    )
                            
                            # Grants table
                            with st.expander("View All Grants"):
                                st.dataframe(grants_df, use_container_width=True, hide_index=True)
                                
                                st.download_button(
                                    label="Download CSV",
                                    data=grants_df.to_csv(index=False),
                                    file_name=f"{role_name}_grants.csv",
                                    mime="text/csv",
                                    key=f"download_csv_{role_name}"
                                )
                        else:
                            st.error(f"Could not retrieve grants for {role_name}")
            else:
                st.info("Select one or more roles from the sidebar to begin analysis")
        else:
            st.warning("No roles found. Check your permissions.")
    
    # ------------------------------------
    # Mode 2: Agent Permission Generator
    # ------------------------------------
    elif tool_mode == "Agent Permission Generator":
        st.header("Agent Permission Generator")
        st.markdown("Generate least-privilege SQL for Cortex Agents")
        
        st.markdown("### Agent Configuration")
        
        # Get all agents first
        agents = get_all_agents(session)
        
        # Create a mapping of agent display name to agent details
        agent_map = {}
        if agents:
            for agent in agents:
                display_name = f"{agent['database']}.{agent['schema']}.{agent['name']}"
                agent_map[display_name] = agent
        
        # Agent input fields in a row
        col1, col2, col3 = st.columns(3)
        
        # Initialize variables
        database = None
        schema = None
        agent_name = None
        
        with col3:
            # Agent dropdown - show this first
            if agent_map:
                agent_options = [""] + sorted(agent_map.keys())
                selected_agent = st.selectbox(
                    "Agent Name - Select Other for Manual Entry", 
                    agent_options,
                    key="agent_name_select"
                )
                
                # If an agent is selected, auto-populate database and schema
                if selected_agent and selected_agent in agent_map:
                    agent_details = agent_map[selected_agent]
                    database = agent_details['database']
                    schema = agent_details['schema']
                    agent_name = agent_details['name']
            else:
                agent_name = st.text_input("Agent Name", placeholder="CTF2024", key="agent_name_manual")
        
        with col1:
            # Database field - auto-populated if agent selected, otherwise manual entry
            if database:
                database = st.text_input("Agent Database", value=database, key="agent_db", disabled=True)
            else:
                database = st.text_input("Agent Database", placeholder="SNOWFLAKE_INTELLIGENCE", key="agent_db")
        
        with col2:
            # Schema field - auto-populated if agent selected, otherwise manual entry
            if schema:
                schema = st.text_input("Agent Schema", value=schema, key="agent_schema", disabled=True)
            else:
                schema = st.text_input("Agent Schema", placeholder="AGENTS", key="agent_schema")
        
        # Generate button
        if st.button("🔧 Generate Permission Script", type="primary", use_container_width=True):
            if agent_name and database and schema:
                with st.spinner("Analyzing agent..."):
                    agent_info = describe_agent(session, database, schema, agent_name)
                    
                    if agent_info:
                        # Parse tools
                        tools = parse_agent_tools(agent_info)
                        
                        if tools:
                            # Extract resources efficiently
                            semantic_views, search_services, procedures = extract_tool_resources(tools)
                            
                            # Also check tool_resources for semantic views (newer agent format)
                            if 'tool_resources' in agent_info:
                                tool_resources = agent_info['tool_resources']
                                for resource_name, resource_data in tool_resources.items():
                                    if isinstance(resource_data, dict) and 'semantic_view' in resource_data:
                                        semantic_view = resource_data['semantic_view']
                                        if semantic_view not in semantic_views:
                                            semantic_views.append(semantic_view)
                                            st.info(f"Found semantic view in tool_resources: {semantic_view}")
                            
                            # Process semantic views to get tables
                            semantic_views_data = []
                            all_tables = []
                            semantic_model_files = set()
                            semantic_model_stages = set()
                            
                            for view_name in semantic_views:
                                yaml_content = get_semantic_view_yaml(session, view_name)
                                tables = parse_tables_from_yaml(yaml_content) if yaml_content else []
                                all_tables.extend(tables)
                                
                                semantic_views_data.append({
                                    'view': view_name,
                                    'yaml': yaml_content,
                                    'tables': tables
                                })
                            
                            # Build tools overview table
                            tools_data = []
                            
                            # Debug: Show raw tool structure
                            with st.expander("Debug: Raw Tools Structure"):
                                st.write(f"Number of tools: {len(tools)}")
                                for idx, tool in enumerate(tools):
                                    st.write(f"**Tool {idx}:**")
                                    st.write(f"  Type: {type(tool)}")
                                    if isinstance(tool, dict):
                                        st.write(f"  Keys: {list(tool.keys())}")
                                    st.json(tool)
                            
                            for idx, tool in enumerate(tools):
                                # Handle different tool structures
                                if isinstance(tool, dict):
                                    # Check if tool properties are nested in 'tool_spec', 'definition', or 'spec'
                                    tool_data = tool
                                    
                                    # Try 'tool_spec' first (most common for Snowflake agents)
                                    if 'tool_spec' in tool:
                                        tool_data = tool['tool_spec']
                                    # Try 'definition' 
                                    elif 'definition' in tool:
                                        tool_data = tool['definition']
                                    # Try 'spec'
                                    elif 'spec' in tool:
                                        tool_data = tool['spec']
                                    
                                    # Now extract properties from the correct location
                                    tool_name = tool_data.get('name', tool_data.get('tool_name', f'tool_{idx}'))
                                    tool_type = tool_data.get('type', tool_data.get('tool_type', 'unknown'))
                                    tool_desc = tool_data.get('description', tool_data.get('desc', 'No description'))
                                    
                                    # Use tool_data for further parsing (it has the actual properties)
                                    tool = tool_data
                                else:
                                    tool_name = f'tool_{idx}'
                                    tool_type = 'unknown'
                                    tool_desc = 'No description'
                                
                                # Extract resource details based on tool type
                                db_name = schema_name = object_name = full_resource = None
                                proc_name = search_service = semantic_file = None
                                
                                if tool_type == 'cortex_analyst_text_to_sql' and 'semantic_model' in tool:
                                    full_resource = tool['semantic_model']
                                    parts = full_resource.split('.')
                                    if len(parts) >= 3:
                                        db_name, schema_name, object_name = parts[0], parts[1], parts[2]
                                    semantic_file = tool.get('semantic_model_file', 'None')
                                    
                                elif tool_type == 'cortex_search' and 'search_service' in tool:
                                    search_service = tool['search_service']
                                    full_resource = search_service
                                    parts = search_service.split('.')
                                    if len(parts) >= 3:
                                        db_name, schema_name, object_name = parts[0], parts[1], parts[2]
                                        
                                elif tool_type == 'generic' and 'procedure' in tool:
                                    proc_name = tool['procedure']
                                    full_resource = proc_name
                                    parts = proc_name.split('.')
                                    if len(parts) >= 3:
                                        db_name, schema_name = parts[0], parts[1]
                                        # Procedure might have signature
                                        object_name = parts[2]
                                
                                tools_data.append({
                                    'TOOL_NAME': tool_name,
                                    'TOOL_TYPE': tool_type,
                                    'TOOL_DESCRIPTION': tool_desc,
                                    'DATABASE_NAME': db_name or 'None',
                                    'SCHEMA_NAME': schema_name or 'None',
                                    'OBJECT_NAME': object_name or 'None',
                                    'FULL_RESOURCE_PATH': full_resource or 'None',
                                    'PROCEDURE_NAME_WITH_TYPES': proc_name or 'None',
                                    'SEARCH_SERVICE_NAME': search_service or 'None',
                                    'SEMANTIC_MODEL_FILE': semantic_file or 'None'
                                })
                            
                            # Display parsed tool information
                            st.markdown("---")
                            st.markdown("### 📊 Parsed Tool Information")
                            
                            # Metrics row
                            col1, col2, col3, col4, col5 = st.columns(5)
                            col1.metric("Total Tools", len(tools))
                            col2.metric("Semantic Views", len(semantic_views))
                            col3.metric("Semantic Model Files", len(semantic_model_files))
                            col4.metric("Semantic Model Stages", len(semantic_model_stages))
                            col5.metric("Search Services", len(search_services))
                            
                            # Tools overview table
                            st.markdown("#### Tools Overview")
                            if tools_data:
                                tools_df = pd.DataFrame(tools_data)
                                st.dataframe(tools_df, use_container_width=True, hide_index=True)
                            
                            # Processing messages
                            for view_name in semantic_views:
                                view_tables = [sv['tables'] for sv in semantic_views_data if sv['view'] == view_name]
                                if view_tables and view_tables[0]:
                                    tables_str = "', '".join(view_tables[0])
                                    st.info(f"Processing semantic view: {view_name}")
                                    st.success(f"Found {len(view_tables[0])} tables: ['{tables_str}']")
                            
                            # Generate SQL
                            st.markdown("---")
                            st.markdown("### 📜 Generated Permission Script")
                            
                            # Summary box
                            all_databases = {database}
                            all_schemas = {f"{database}.{schema}"}
                            
                            for sv in semantic_views_data:
                                for table in sv['tables']:
                                    parts = table.split('.')
                                    if len(parts) >= 2:
                                        all_databases.add(parts[0])
                                        all_schemas.add(f"{parts[0]}.{parts[1]}")
                            
                            st.info(f"""
**Agent:** {agent_name}  
**Location:** {database}.{schema}  
**Databases:** {len(all_databases)} (including tables from semantic views)  
**Schemas:** {len(all_schemas)} (including tables from semantic views)  
**Tables:** {len(all_tables)}
                            """)
                            
                            # Generate SQL script
                            sql_script = generate_agent_permission_sql(
                                agent_name, database, schema, tools, semantic_views_data, 
                                role_name=f"{agent_name}_USER_ROLE"
                            )
                            
                            st.code(sql_script, language="sql")
                            
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                st.download_button(
                                    label="Download SQL Script",
                                    data=sql_script,
                                    file_name=f"{agent_name}_permissions.sql",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                            with col2:
                                st.info("Review and execute this SQL in a Snowflake worksheet")
                        else:
                            st.warning("No tools found for this agent")
                    else:
                        st.error("Failed to analyze agent. Check that the agent exists and you have permissions.")
            else:
                st.warning("Please provide Database, Schema, and Agent Name")
    
    # ------------------------------------
    # Mode 3: Combined Analysis
    # ------------------------------------
    else:
        st.header("Combined Analysis")
        st.markdown("Analyze both roles and agents together")
        
        st.info("This feature allows you to check if a specific role has the necessary permissions to use a specific agent.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Select Role")
            all_roles = get_all_roles(session)
            selected_role = st.selectbox("Choose a role:", all_roles if all_roles else [])
        
        with col2:
            st.subheader("Select Agent")
            agents = get_all_agents(session)
            if agents:
                agent_options = [f"{a['database']}.{a['schema']}.{a['name']}" for a in agents]
                selected_agent = st.selectbox("Choose an agent:", agent_options)
            else:
                selected_agent = None
                st.warning("No agents found")
        
        if selected_role and selected_agent:
            if st.button("Analyze Compatibility", type="primary"):
                parts = selected_agent.split('.')
                database, schema, agent_name = parts[0], parts[1], parts[2]
                
                with st.spinner("Analyzing..."):
                    grants_df = get_role_grants(session, selected_role)
                    agent_info = describe_agent(session, database, schema, agent_name)
                    
                    if not grants_df.empty and agent_info:
                        st.success("Analysis complete!")
                        
                        st.markdown("### Compatibility Check")
                        
                        # Check permissions
                        agent_grants = grants_df[
                            (grants_df['GRANTED_ON'] == 'AGENT') & 
                            (grants_df['OBJECT_NAME'] == f"{database}.{schema}.{agent_name}")
                        ]
                        has_agent_access = not agent_grants.empty
                        
                        # Test actual Cortex access
                        with st.spinner("Testing Cortex access..."):
                            actual_access = test_cortex_access(session, selected_role)
                        
                        analysis = analyze_grants(grants_df, actual_cortex_access=actual_access, role_name=selected_role)
                        has_cortex = analysis['has_cortex']
                        has_warehouse = analysis['wh_count'] > 0
                        
                        # Display results
                        col1, col2, col3 = st.columns(3)
                        if has_agent_access:
                            col1.success("Agent Access")
                        else:
                            col1.error("No Agent Access")
                        
                        if has_cortex:
                            if analysis['cortex_method'] == 'implicit':
                                col2.success("Cortex Access (implicit)")
                            else:
                                col2.success("Cortex Access (explicit)")
                        else:
                            col2.error("No Cortex Access")
                        
                        if has_warehouse:
                            col3.success("Warehouse Access")
                        else:
                            col3.error("No Warehouse")
                        
                        # Overall verdict
                        if has_agent_access and has_cortex and has_warehouse:
                            st.success("**Role is fully compatible with this agent!**")
                        else:
                            st.warning("**Role needs additional permissions**")
                            
                            with st.expander("View Fix SQL"):
                                fix_sql = []
                                if not has_agent_access:
                                    fix_sql.append(f'GRANT USAGE ON AGENT "{database}"."{schema}"."{agent_name}" TO ROLE {selected_role};')
                                if not has_cortex:
                                    fix_sql.append(f"GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE {selected_role};")
                                if not has_warehouse:
                                    fix_sql.append(f"GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE {selected_role};")
                                
                                st.code("\n".join(fix_sql), language="sql")
                    else:
                        st.error("Failed to complete analysis")
    
    # Sidebar footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info("""
    **Snowflake Cortex Security Hub**
    
    🔐 Intelligent permission management for Cortex AI
    
    **Features:**
    - Role readiness validation
    - Least-privilege SQL generation
    - Deep dependency analysis
    - Compatibility checking
    """)
    st.sidebar.markdown("**Version:** 2.0.0")
    st.sidebar.caption("Built with ❄️ for Snowflake Cortex")

if __name__ == "__main__":
    main()

