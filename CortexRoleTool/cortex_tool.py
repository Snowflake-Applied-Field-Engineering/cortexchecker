"""
Cortex Tool - Combined Role Checker & Agent Permission Generator
Integrates cortexchecker and CART (Cortex Agent Role Tool) functionality
"""

import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
import fnmatch
from datetime import datetime
import json
import re

# Set page configuration
st.set_page_config(
    layout="wide", 
    page_title="Cortex Tool"
)

# ------------------------------------
# Utility Functions
# ------------------------------------

@st.cache_data(show_spinner="Fetching available roles...")
def get_all_roles(_session):
    """Fetches all roles visible to the Streamlit app owner/session."""
    try:
        roles_df = _session.sql("SELECT NAME FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES WHERE DELETED_ON IS NULL ORDER BY NAME").collect()
        return [row['NAME'] for row in roles_df]
    except Exception as e:
        st.error(f"Could not query roles from ACCOUNT_USAGE. Falling back to INFORMATION_SCHEMA.ROLES. Error: {e}")
        try:
            roles_df = _session.sql("SELECT ROLE_NAME FROM INFORMATION_SCHEMA.ROLES ORDER BY ROLE_NAME").collect()
            return [row['ROLE_NAME'] for row in roles_df]
        except Exception as e_fallback:
            st.error(f"Failed to retrieve roles. Please check the app owner's privileges. Error: {e_fallback}")
            return []

@st.cache_data(show_spinner="Fetching agents...")
def get_all_agents(_session, database=None, schema=None):
    """Fetch all Cortex Agents in the account or specific database/schema."""
    try:
        if database and schema:
            query = f"SHOW AGENTS IN SCHEMA {database}.{schema}"
        elif database:
            query = f"SHOW AGENTS IN DATABASE {database}"
        else:
            query = "SHOW AGENTS IN ACCOUNT"
        
        agents_df = _session.sql(query).collect()
        return [{'name': row['name'], 'database': row['database_name'], 'schema': row['schema_name']} 
                for row in agents_df]
    except Exception as e:
        st.warning(f"Could not fetch agents: {e}")
        return []

@st.cache_data(show_spinner="Analyzing agent...")
def describe_agent(_session, database, schema, agent_name):
    """Get detailed information about a Cortex Agent."""
    try:
        query = f"DESCRIBE AGENT {database}.{schema}.{agent_name}"
        result = _session.sql(query).collect()
        
        agent_info = {}
        for row in result:
            prop = row['property']
            value = row['value']
            agent_info[prop] = value
        
        return agent_info
    except Exception as e:
        st.error(f"Failed to describe agent: {e}")
        return None

def parse_agent_tools(agent_info):
    """Parse tools from agent description."""
    tools = []
    if 'tools' in agent_info:
        try:
            tools_data = json.loads(agent_info['tools']) if isinstance(agent_info['tools'], str) else agent_info['tools']
            if isinstance(tools_data, list):
                tools = tools_data
        except:
            pass
    return tools

def extract_semantic_views(tools):
    """Extract semantic views from agent tools."""
    semantic_views = []
    for tool in tools:
        if tool.get('type') == 'cortex_analyst_text_to_sql':
            if 'semantic_model' in tool:
                semantic_views.append(tool['semantic_model'])
    return semantic_views

def extract_search_services(tools):
    """Extract Cortex Search services from agent tools."""
    search_services = []
    for tool in tools:
        if tool.get('type') == 'cortex_search':
            if 'search_service' in tool:
                search_services.append(tool['search_service'])
    return search_services

def extract_procedures(tools):
    """Extract stored procedures from agent tools."""
    procedures = []
    for tool in tools:
        if tool.get('type') == 'generic':
            if 'procedure' in tool:
                procedures.append(tool['procedure'])
    return procedures

@st.cache_data(show_spinner="Analyzing semantic view...")
def get_semantic_view_yaml(_session, view_name):
    """Get YAML definition from semantic view."""
    try:
        query = f"SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('{view_name}') as yaml_def"
        result = _session.sql(query).collect()
        if result:
            return result[0]['YAML_DEF']
    except Exception as e:
        st.warning(f"Could not read YAML from {view_name}: {e}")
    return None

def parse_tables_from_yaml(yaml_content):
    """Extract table references from semantic view YAML."""
    tables = []
    if yaml_content:
        # Simple regex to find table references in YAML
        # This is a simplified parser - production would use proper YAML parsing
        table_pattern = r'(?:table|from):\s*([A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*)'
        matches = re.findall(table_pattern, yaml_content, re.IGNORECASE)
        tables.extend(matches)
    return list(set(tables))

@st.cache_data(show_spinner="Analyzing grants for selected roles...")
def get_role_grants(_session, role_name):
    """Fetches all grants granted to the specified role."""
    role_name_upper = role_name.upper()
    
    try:
        combined_sql_account_usage = f"""
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
        
        grants_rows = _session.sql(combined_sql_account_usage).collect()
        
        if grants_rows:
            grants_df = pd.DataFrame([row.as_dict() for row in grants_rows])
            return grants_df
        else:
            return pd.DataFrame(columns=['GRANTED_ON', 'PRIVILEGE', 'GRANTED_ROLE', 'OBJECT_NAME'])
        
    except Exception as e:
        st.warning(f"Failed to query ACCOUNT_USAGE views for **{role_name}**. Error: {str(e)[:200]}")
        return pd.DataFrame(columns=['GRANTED_ON', 'PRIVILEGE', 'GRANTED_ROLE', 'OBJECT_NAME'])

def check_cortex_access(grants_df):
    """Analyzes the grants DataFrame for Cortex Analyst privileges."""
    required_roles = [
        'SNOWFLAKE.CORTEX_USER',
        'SNOWFLAKE.CORTEX_ANALYST_USER'
    ]
    
    if grants_df.empty or 'GRANTED_ROLE' not in grants_df.columns:
        granted_roles = []
    else:
        granted_roles = [str(r).upper() for r in grants_df['GRANTED_ROLE'].dropna().unique()]
    
    found_roles = [role for role in required_roles if role in granted_roles]
    has_access = len(found_roles) > 0
    
    return has_access, found_roles

def generate_agent_permission_sql(agent_name, database, schema, tools, semantic_views_data, role_name=None):
    """Generate comprehensive SQL for agent permissions."""
    if not role_name:
        role_name = f"{agent_name}_USER_ROLE"
    
    sql_lines = []
    sql_lines.append("-- " + "="*80)
    sql_lines.append(f"-- AUTO-GENERATED LEAST-PRIVILEGE SCRIPT FOR AGENT: {database}.{schema}.{agent_name}")
    sql_lines.append(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_lines.append(f"-- Generated by: Cortex Tool")
    sql_lines.append("-- " + "="*80)
    sql_lines.append("")
    sql_lines.append("-- IMPORTANT: Review and adjust the placeholder variables below for your environment.")
    sql_lines.append(f"SET AGENT_ROLE_NAME = '{role_name}';")
    sql_lines.append("SET WAREHOUSE_NAME = 'COMPUTE_WH';")
    sql_lines.append("")
    
    # Create role
    sql_lines.append("-- Create a dedicated role for the agent's permissions.")
    sql_lines.append("USE ROLE SECURITYADMIN;")
    sql_lines.append("CREATE ROLE IF NOT EXISTS IDENTIFIER($AGENT_ROLE_NAME);")
    sql_lines.append("GRANT ROLE IDENTIFIER($AGENT_ROLE_NAME) TO ROLE SYSADMIN;")
    sql_lines.append("")
    
    # Grant agent usage
    sql_lines.append("-- Grant core permission to use the agent object itself.")
    sql_lines.append(f"GRANT USAGE ON AGENT {database}.{schema}.{agent_name} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
    sql_lines.append("")
    
    # Database and schema grants
    databases = set([database])
    schemas = set([f"{database}.{schema}"])
    
    sql_lines.append("-- Grant permissions on the underlying database objects required by the agent's tools.")
    sql_lines.append("")
    
    # Process semantic views and tables
    if semantic_views_data:
        sql_lines.append("-- Permissions for 'cortex_analyst_text_to_sql' tools")
        sql_lines.append("-- Semantic view permissions")
        for view_info in semantic_views_data:
            view_name = view_info['view']
            sql_lines.append(f"GRANT SELECT ON VIEW {view_name} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
            
            # Add database/schema from view
            parts = view_name.split('.')
            if len(parts) >= 2:
                databases.add(parts[0])
                schemas.add(f"{parts[0]}.{parts[1]}")
            
            # Grant on tables
            if view_info.get('tables'):
                sql_lines.append("")
                sql_lines.append("-- Base table permissions (from semantic view YAML)")
                for table in view_info['tables']:
                    sql_lines.append(f"GRANT SELECT ON TABLE {table} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
                    
                    # Add database/schema from table
                    parts = table.split('.')
                    if len(parts) >= 2:
                        databases.add(parts[0])
                        schemas.add(f"{parts[0]}.{parts[1]}")
        sql_lines.append("")
    
    # Process search services
    search_services = extract_search_services(tools)
    if search_services:
        sql_lines.append("-- Permissions for 'cortex_search' tools")
        for service in search_services:
            sql_lines.append(f"GRANT USAGE ON CORTEX SEARCH SERVICE {service} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
            
            # Add database/schema from service
            parts = service.split('.')
            if len(parts) >= 2:
                databases.add(parts[0])
                schemas.add(f"{parts[0]}.{parts[1]}")
        sql_lines.append("")
    
    # Process procedures
    procedures = extract_procedures(tools)
    if procedures:
        sql_lines.append("-- Permissions for 'generic' tools (procedures)")
        for proc in procedures:
            sql_lines.append(f"GRANT USAGE ON PROCEDURE {proc} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
            
            # Add database/schema from procedure
            parts = proc.split('.')
            if len(parts) >= 2:
                databases.add(parts[0])
                schemas.add(f"{parts[0]}.{parts[1]}")
        sql_lines.append("")
    
    # Grant database and schema usage
    sql_lines.append("-- Database and Schema USAGE grants")
    for db in sorted(databases):
        sql_lines.append(f"GRANT USAGE ON DATABASE {db} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
    for sch in sorted(schemas):
        sql_lines.append(f"GRANT USAGE ON SCHEMA {sch} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
    sql_lines.append("")
    
    # Warehouse grant
    sql_lines.append("-- Grant warehouse usage to the role for the user's session.")
    sql_lines.append("GRANT USAGE ON WAREHOUSE IDENTIFIER($WAREHOUSE_NAME) TO ROLE IDENTIFIER($AGENT_ROLE_NAME);")
    sql_lines.append("")
    
    # Optional: Create user
    sql_lines.append("-- Optional: Create a dedicated user for this agent")
    sql_lines.append("-- SET AGENT_USER_NAME = '" + agent_name.lower() + "_user';")
    sql_lines.append("-- SET AGENT_USER_PASSWORD = '<SECURE_PASSWORD>';")
    sql_lines.append("-- CREATE USER IF NOT EXISTS IDENTIFIER($AGENT_USER_NAME)")
    sql_lines.append("--   PASSWORD = $AGENT_USER_PASSWORD")
    sql_lines.append("--   DEFAULT_ROLE = IDENTIFIER($AGENT_ROLE_NAME)")
    sql_lines.append("--   DEFAULT_WAREHOUSE = IDENTIFIER($WAREHOUSE_NAME);")
    sql_lines.append("-- GRANT ROLE IDENTIFIER($AGENT_ROLE_NAME) TO USER IDENTIFIER($AGENT_USER_NAME);")
    sql_lines.append("")
    
    sql_lines.append("-- " + "="*80)
    sql_lines.append("SELECT 'Setup complete for role ' || $AGENT_ROLE_NAME AS \"Status\";")
    sql_lines.append("-- " + "="*80)
    
    return "\n".join(sql_lines)

def generate_role_remediation_sql(role_name, issues):
    """Generate SQL commands to fix missing permissions for a role."""
    sql_commands = []
    sql_commands.append(f"-- Remediation SQL for role: {role_name}")
    sql_commands.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_commands.append("")
    
    if "Missing CORTEX_USER or CORTEX_ANALYST_USER role" in issues:
        sql_commands.append("-- Grant Cortex database role")
        sql_commands.append(f"GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE {role_name};")
        sql_commands.append("-- OR grant Cortex Analyst User role (more permissive)")
        sql_commands.append(f"-- GRANT DATABASE ROLE SNOWFLAKE.CORTEX_ANALYST_USER TO ROLE {role_name};")
        sql_commands.append("")
    
    if "No warehouse USAGE privileges" in issues:
        sql_commands.append("-- Grant warehouse access (replace COMPUTE_WH with your warehouse name)")
        sql_commands.append(f"GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE {role_name};")
        sql_commands.append("")
    
    if "No database or schema access" in issues:
        sql_commands.append("-- Grant database and schema access (replace with your database/schema names)")
        sql_commands.append(f"GRANT USAGE ON DATABASE <DATABASE_NAME> TO ROLE {role_name};")
        sql_commands.append(f"GRANT USAGE ON SCHEMA <DATABASE_NAME>.<SCHEMA_NAME> TO ROLE {role_name};")
        sql_commands.append("")
    
    if "No SELECT privileges on tables/views" in issues:
        sql_commands.append("-- Grant SELECT on tables (replace with your database/schema names)")
        sql_commands.append(f"GRANT SELECT ON ALL TABLES IN SCHEMA <DATABASE_NAME>.<SCHEMA_NAME> TO ROLE {role_name};")
        sql_commands.append(f"GRANT SELECT ON ALL VIEWS IN SCHEMA <DATABASE_NAME>.<SCHEMA_NAME> TO ROLE {role_name};")
        sql_commands.append("")
    
    if not issues:
        sql_commands.append("-- No issues found! Role is fully ready for Cortex Analyst.")
    
    return "\n".join(sql_commands)

# ------------------------------------
# Main Application
# ------------------------------------

def main():
    st.title("Cortex Tool")
    st.markdown("**Combined Role Checker & Agent Permission Generator**")
    st.markdown("Analyze role permissions for Cortex Analyst and generate least-privilege SQL for Cortex Agents")
    st.markdown("---")
    
    # Get session
    try:
        session = get_active_session()
    except Exception:
        st.error("This application must be run as a Streamlit in Snowflake app within Snowsight to access the database session.")
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
            
            if search_term:
                filtered_roles = [r for r in all_roles if search_term.upper() in r.upper()]
            else:
                filtered_roles = all_roles
            
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
                            # Check Cortex access
                            has_cortex, found_roles = check_cortex_access(grants_df)
                            
                            # Metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Cortex Access", "Yes" if has_cortex else "No")
                            with col2:
                                wh_count = len(grants_df[grants_df['GRANTED_ON'] == 'WAREHOUSE']['OBJECT_NAME'].unique())
                                st.metric("Warehouses", wh_count)
                            with col3:
                                db_count = len(grants_df[grants_df['GRANTED_ON'] == 'DATABASE']['OBJECT_NAME'].unique())
                                st.metric("Databases", db_count)
                            with col4:
                                table_count = len(grants_df[grants_df['GRANTED_ON'].isin(['TABLE', 'VIEW'])]['OBJECT_NAME'].unique())
                                st.metric("Tables/Views", table_count)
                            
                            # Readiness assessment
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
                            
                            progress_pct = readiness_score / 4
                            
                            if progress_pct == 1.0:
                                st.success(f"**FULLY READY** - Score: {readiness_score}/4")
                            elif progress_pct >= 0.75:
                                st.warning(f"**MOSTLY READY** - Score: {readiness_score}/4")
                            else:
                                st.error(f"**NOT READY** - Score: {readiness_score}/4")
                            
                            st.progress(progress_pct)
                            
                            if issues:
                                st.markdown("**Issues to Address:**")
                                for issue in issues:
                                    st.markdown(f"- {issue}")
                                
                                # Remediation SQL
                                with st.expander("View Remediation SQL"):
                                    sql_script = generate_role_remediation_sql(role_name, issues)
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
                                
                                csv = grants_df.to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
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
        
        # Agent discovery
        col1, col2 = st.columns([2, 1])
        with col1:
            agent_input_method = st.radio(
                "How would you like to specify the agent?",
                ["Select from list", "Enter manually"],
                horizontal=True
            )
        
        agent_name = None
        database = None
        schema = None
        
        if agent_input_method == "Select from list":
            # Fetch agents
            agents = get_all_agents(session)
            
            if agents:
                agent_options = [f"{a['database']}.{a['schema']}.{a['name']}" for a in agents]
                selected_agent = st.selectbox("Select an agent:", agent_options)
                
                if selected_agent:
                    parts = selected_agent.split('.')
                    database, schema, agent_name = parts[0], parts[1], parts[2]
            else:
                st.warning("No agents found. Make sure you have access to view agents.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                database = st.text_input("Database:", placeholder="MY_DATABASE")
            with col2:
                schema = st.text_input("Schema:", placeholder="MY_SCHEMA")
            with col3:
                agent_name = st.text_input("Agent Name:", placeholder="MY_AGENT")
        
        if agent_name and database and schema:
            st.markdown("---")
            
            if st.button("Analyze Agent", type="primary"):
                with st.spinner("Analyzing agent..."):
                    # Describe agent
                    agent_info = describe_agent(session, database, schema, agent_name)
                    
                    if agent_info:
                        st.success(f"Successfully analyzed agent: {database}.{schema}.{agent_name}")
                        
                        # Display agent info
                        with st.expander("Agent Details", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Database:** `{database}`")
                                st.markdown(f"**Schema:** `{schema}`")
                                st.markdown(f"**Agent:** `{agent_name}`")
                            with col2:
                                if 'created_on' in agent_info:
                                    st.markdown(f"**Created:** {agent_info['created_on']}")
                                if 'owner' in agent_info:
                                    st.markdown(f"**Owner:** {agent_info['owner']}")
                        
                        # Parse tools
                        tools = parse_agent_tools(agent_info)
                        
                        if tools:
                            st.markdown("### Agent Tools")
                            
                            # Categorize tools
                            analyst_tools = [t for t in tools if t.get('type') == 'cortex_analyst_text_to_sql']
                            search_tools = [t for t in tools if t.get('type') == 'cortex_search']
                            generic_tools = [t for t in tools if t.get('type') == 'generic']
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Analyst Tools", len(analyst_tools))
                            with col2:
                                st.metric("Search Tools", len(search_tools))
                            with col3:
                                st.metric("Generic Tools", len(generic_tools))
                            
                            # Process semantic views
                            semantic_views_data = []
                            if analyst_tools:
                                st.markdown("#### Semantic Views")
                                for tool in analyst_tools:
                                    if 'semantic_model' in tool:
                                        view_name = tool['semantic_model']
                                        st.markdown(f"- `{view_name}`")
                                        
                                        # Get YAML and parse tables
                                        yaml_content = get_semantic_view_yaml(session, view_name)
                                        tables = parse_tables_from_yaml(yaml_content) if yaml_content else []
                                        
                                        semantic_views_data.append({
                                            'view': view_name,
                                            'yaml': yaml_content,
                                            'tables': tables
                                        })
                                        
                                        if tables:
                                            with st.expander(f"Tables used by {view_name}"):
                                                for table in tables:
                                                    st.markdown(f"  - `{table}`")
                            
                            # Display search services
                            if search_tools:
                                st.markdown("#### Search Services")
                                for tool in search_tools:
                                    if 'search_service' in tool:
                                        st.markdown(f"- `{tool['search_service']}`")
                            
                            # Display procedures
                            if generic_tools:
                                st.markdown("#### Procedures")
                                for tool in generic_tools:
                                    if 'procedure' in tool:
                                        st.markdown(f"- `{tool['procedure']}`")
                            
                            # Generate SQL
                            st.markdown("---")
                            st.markdown("### Generated Permissions SQL")
                            
                            role_name = st.text_input(
                                "Role name for generated SQL:",
                                value=f"{agent_name}_USER_ROLE",
                                help="Name of the role to create for agent access"
                            )
                            
                            sql_script = generate_agent_permission_sql(
                                agent_name, database, schema, tools, semantic_views_data, role_name
                            )
                            
                            st.code(sql_script, language="sql")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    label="Download SQL Script",
                                    data=sql_script,
                                    file_name=f"{agent_name}_permissions.sql",
                                    mime="text/plain"
                                )
                            with col2:
                                st.info("Review and execute this SQL in a Snowflake worksheet")
                        else:
                            st.warning("No tools found for this agent")
                    else:
                        st.error("Failed to analyze agent. Check that the agent exists and you have permissions.")
        else:
            st.info("Specify an agent to begin analysis")
    
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
                    # Get role grants
                    grants_df = get_role_grants(session, selected_role)
                    
                    # Get agent info
                    agent_info = describe_agent(session, database, schema, agent_name)
                    
                    if not grants_df.empty and agent_info:
                        st.success("Analysis complete!")
                        
                        # Check if role can use agent
                        st.markdown("### Compatibility Check")
                        
                        # Check 1: Agent usage permission
                        agent_grants = grants_df[
                            (grants_df['GRANTED_ON'] == 'AGENT') & 
                            (grants_df['OBJECT_NAME'] == f"{database}.{schema}.{agent_name}")
                        ]
                        has_agent_access = not agent_grants.empty
                        
                        # Check 2: Cortex roles
                        has_cortex, _ = check_cortex_access(grants_df)
                        
                        # Check 3: Warehouse access
                        has_warehouse = not grants_df[grants_df['GRANTED_ON'] == 'WAREHOUSE'].empty
                        
                        # Display results
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if has_agent_access:
                                st.success("Agent Access")
                            else:
                                st.error("No Agent Access")
                        with col2:
                            if has_cortex:
                                st.success("Cortex Role")
                            else:
                                st.error("No Cortex Role")
                        with col3:
                            if has_warehouse:
                                st.success("Warehouse Access")
                            else:
                                st.error("No Warehouse")
                        
                        # Overall verdict
                        if has_agent_access and has_cortex and has_warehouse:
                            st.success("**Role is fully compatible with this agent!**")
                        else:
                            st.warning("**Role needs additional permissions**")
                            
                            # Generate fix SQL
                            with st.expander("View Fix SQL"):
                                fix_sql = []
                                if not has_agent_access:
                                    fix_sql.append(f"GRANT USAGE ON AGENT {database}.{schema}.{agent_name} TO ROLE {selected_role};")
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
    **Cortex Tool** combines:
    - Role permission checking
    - Agent permission generation
    - Compatibility analysis
    
    Built for Snowflake Cortex AI
    """)
    st.sidebar.markdown("**Version:** 1.0.0")

if __name__ == "__main__":
    main()

