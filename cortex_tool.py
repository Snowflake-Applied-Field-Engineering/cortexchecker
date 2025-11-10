"""
Snowflake Intelligence & Cortex Access Checker
Combined Role Checker & Agent Permission Generator
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
import fnmatch
from datetime import datetime
import json
import re
from functools import lru_cache
from typing import List

# Set page configuration
st.set_page_config(
    layout="wide", 
    page_title="Snowflake Intelligence & Cortex Access Checker"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

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

@st.cache_data(show_spinner="Fetching agent names...", ttl=300)
def get_agent_names(_session, agent_database: str, agent_schema: str) -> List[str]:
    """Get agent names from a specific database and schema."""
    try:
        agent_results = _session.sql(
            f"SHOW AGENTS IN SCHEMA {agent_database}.{agent_schema}"
        ).to_pandas()
        
        if agent_results.empty:
            return ["Other"]
        
        # Normalize column names
        agent_results.columns = [col.strip('"').lower() for col in agent_results.columns]
        
        # Find the name column
        name_col = None
        for col in agent_results.columns:
            if col in ['name', 'agent_name']:
                name_col = col
                break
        
        if not name_col:
            return ["Other"]
        
        agent_names = agent_results[name_col].tolist()
        agent_names.append("Other")
        return agent_names
    except Exception as e:
        # If there's an error (e.g., schema doesn't exist), just return "Other"
        return ["Other"]

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
        
        # Debug: Show what we have (commented out for production)
        # with st.expander("Debug: Raw Agent Info"):
        #     st.write("Available keys:", list(agent_info.keys()))
        #     for key, value in agent_info.items():
        #         st.write(f"**{key}**: type={type(value)}, is_null={value is None}, is_empty={not value if value is not None else 'N/A'}")
        
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
                    # Debug: Show what we got (commented out for production)
                    # with st.expander("Debug: Parsed Agent Spec"):
                    #     st.write("Agent spec type:", type(agent_spec))
                    #     if isinstance(agent_spec, dict):
                    #         st.write("Agent spec keys:", list(agent_spec.keys()))
                    #     st.json(agent_spec)
                    
                    # Extract tools from agent_spec - try multiple possible locations
                    tools_found = None
                    
                    if isinstance(agent_spec, dict):
                        # Check if agent_spec has actual keys (not just an empty dict)
                        actual_keys = [k for k in agent_spec.keys() if not k.startswith('_')]
                        
                        # Debug info commented out for production
                        # if len(actual_keys) == 0:
                        #     st.warning("agent_spec is an empty dictionary or only contains internal keys")
                        # else:
                        #     st.info(f"agent_spec has {len(actual_keys)} keys: {actual_keys}")
                        
                        # Try direct 'tools' key
                        if 'tools' in agent_spec:
                            tools_found = agent_spec['tools']
                            # st.success(f"Found {len(tools_found)} tools in agent_spec['tools']")
                        # Try 'definition' -> 'tools' path
                        elif 'definition' in agent_spec and isinstance(agent_spec['definition'], dict):
                            if 'tools' in agent_spec['definition']:
                                tools_found = agent_spec['definition']['tools']
                                # st.success(f"Found {len(tools_found)} tools in agent_spec['definition']['tools']")
                        # Try 'spec' -> 'tools' path
                        elif 'spec' in agent_spec and isinstance(agent_spec['spec'], dict):
                            if 'tools' in agent_spec['spec']:
                                tools_found = agent_spec['spec']['tools']
                                # st.success(f"Found {len(tools_found)} tools in agent_spec['spec']['tools']")
                        
                        if tools_found:
                            agent_info['tools'] = tools_found
                            
                            # Also extract tool_resources if available (contains semantic_view references)
                            if 'tool_resources' in agent_spec:
                                agent_info['tool_resources'] = agent_spec['tool_resources']
                                # st.info(f"Found tool_resources with {len(agent_spec['tool_resources'])} entries")
                        else:
                            # Maybe tools are at a different path - show error to user
                            st.error(f"Could not find tools in agent specification. Please check that the agent has tools configured.")
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

@st.cache_data(show_spinner="Parsing agent with SQL...", ttl=300)
def parse_agent_tools_with_sql(_session, database, schema, agent_name):
    """
    Enhanced agent parsing using SQL queries to extract all tool resources.
    This method is more comprehensive than Python-based parsing.
    """
    try:
        # Combined query that describes the agent and parses tools in one go
        combined_query = f"""
        WITH agent_describe AS (
            SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
        ),
        parsed AS (
            SELECT 
                -- Get info from the 'tools' array
                tools_flat.VALUE:tool_spec:name::STRING AS TOOL_NAME,
                tools_flat.VALUE:tool_spec:type::STRING AS TOOL_TYPE,
                tools_flat.VALUE:tool_spec:description::STRING AS TOOL_DESCRIPTION,
                
                -- Path 1: Get DB/Schema from 'description' (your original logic)
                REGEXP_SUBSTR(
                    tools_flat.VALUE:tool_spec:description::STRING, 
                    'Database: (\\\\w+)', 1, 1, 'e', 1
                ) AS DB_FROM_DESC,
                REGEXP_SUBSTR(
                    tools_flat.VALUE:tool_spec:description::STRING, 
                    'Schema: (\\\\w+)', 1, 1, 'e', 1
                ) AS SCHEMA_FROM_DESC,

                -- Path 2: Get the full resource path from 'tool_resources'
                -- We check all known keys where a resource path might be
                COALESCE(
                    PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:identifier::STRING,
                    PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:semantic_view::STRING,
                    PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:search_service::STRING,
                    PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:name::STRING,
                    PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:semantic_model_file::STRING
                ) AS FULL_RESOURCE_PATH,
                
                -- Get procedure name with parameter types for generic tools
                PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:name::STRING AS PROCEDURE_NAME_WITH_TYPES,
                
                -- Get search service name for cortex_search tools (fallback when search_service is not available)
                PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:search_service::STRING AS SEARCH_SERVICE_NAME,
                
                -- Get semantic model file path for cortex_analyst_text_to_sql tools
                PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:semantic_model_file::STRING AS SEMANTIC_MODEL_FILE,
                
                -- Get execution environment info
                PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:execution_environment AS EXECUTION_ENV,
                
                -- Extract warehouse from execution_environment
                PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:execution_environment:warehouse::STRING AS TOOL_WH

            FROM 
                agent_describe AS desc_results,
                LATERAL FLATTEN(input => PARSE_JSON(desc_results."agent_spec"):tools) AS tools_flat
        )
        SELECT 
            TOOL_NAME,
            TOOL_TYPE,
            TOOL_DESCRIPTION,
            
            -- Final Columns: 
            -- If DB_FROM_DESC is null, use the value from FULL_RESOURCE_PATH
            COALESCE(
                DB_FROM_DESC, 
                SPLIT_PART(FULL_RESOURCE_PATH, '.', 1)
            ) AS DATABASE_NAME,
            
            -- If SCHEMA_FROM_DESC is null, use the value from FULL_RESOURCE_PATH
            COALESCE(
                SCHEMA_FROM_DESC, 
                SPLIT_PART(FULL_RESOURCE_PATH, '.', 2)
            ) AS SCHEMA_NAME,
            
            -- This extracts the 3rd part (the "MODEL" or object name)
            SPLIT_PART(FULL_RESOURCE_PATH, '.', 3) AS OBJECT_NAME,

            FULL_RESOURCE_PATH,
            PROCEDURE_NAME_WITH_TYPES,
            SEARCH_SERVICE_NAME,
            SEMANTIC_MODEL_FILE,
            EXECUTION_ENV,
            TOOL_WH
        FROM 
            parsed
        """

        # First execute DESCRIBE to populate RESULT_SCAN
        describe_query = f'DESCRIBE AGENT "{database}"."{schema}"."{agent_name}"'
        _session.sql(describe_query).collect()

        # Then execute the combined parsing query
        results_df = _session.sql(combined_query).collect()

        # Convert to pandas DataFrame for easier processing
        df = pd.DataFrame([row.asDict() for row in results_df])

        # Initialize collections
        semantic_views = set()
        semantic_model_files = set()
        semantic_model_stages = set()  # For stage permissions
        search_services = set()
        procedures = set()
        databases = set()
        schemas = set()
        tool_details = []
        tool_warehouses = {}

        # Process each tool
        for _, row in df.iterrows():
            tool_name = row['TOOL_NAME']
            tool_type = row['TOOL_TYPE']
            tool_description = row['TOOL_DESCRIPTION']
            database_name = row['DATABASE_NAME']
            schema_name = row['SCHEMA_NAME']
            object_name = row['OBJECT_NAME']
            full_resource_path = row['FULL_RESOURCE_PATH']
            procedure_name_with_types = row['PROCEDURE_NAME_WITH_TYPES']
            search_service_name = row['SEARCH_SERVICE_NAME']
            semantic_model_file = row['SEMANTIC_MODEL_FILE']
            execution_env = row['EXECUTION_ENV']
            tool_wh = row['TOOL_WH']

            tool_info = {
                "name": tool_name,
                "type": tool_type,
                "description": tool_description,
                "database": database_name,
                "schema": schema_name,
                "object": object_name,
                "full_path": full_resource_path,
                "procedure_name_with_types": procedure_name_with_types,
                "search_service_name": search_service_name,
                "semantic_model_file": semantic_model_file,
                "warehouse": tool_wh
            }

            # Extract warehouse information from TOOL_WH column
            if tool_wh and tool_wh.strip():
                tool_warehouses[tool_name] = tool_wh
                tool_info["warehouse"] = tool_wh

            # Categorize tools by type
            if tool_type == "cortex_analyst_text_to_sql":
                if semantic_model_file:
                    # Handle semantic model files stored in stages
                    semantic_model_files.add(semantic_model_file)
                    tool_info["semantic_model_file"] = semantic_model_file
                    # Extract database and schema from the semantic model file path
                    db, schema, stage = extract_stage_info_from_semantic_model_file(
                        semantic_model_file)
                    if db and schema and stage:
                        # Add database and schema permissions for the stage location
                        databases.add(db)
                        schemas.add(f"{db}.{schema}")
                        # Add stage permission
                        semantic_model_stages.add(f"{db}.{schema}.{stage}")
                elif full_resource_path:
                    # Handle traditional semantic views
                    semantic_views.add(full_resource_path)
                    tool_info["semantic_view"] = full_resource_path
                    # Extract database and schema from the full_resource_path for semantic views
                    # Format is typically: DATABASE.SCHEMA.SEMANTIC_VIEW_NAME
                    path_parts = full_resource_path.split('.')
                    if len(path_parts) >= 2:
                        view_db = path_parts[0]
                        view_schema = path_parts[1]
                        databases.add(view_db)
                        schemas.add(f"{view_db}.{view_schema}")
                    else:
                        # Fallback to parsed values if path parsing fails
                        databases.add(database_name)
                        schemas.add(f"{database_name}.{schema_name}")

            elif tool_type == "cortex_search":
                # Handle Cortex Search Services - use search_service_name if available, otherwise use full_resource_path
                search_service_path = search_service_name or full_resource_path
                if search_service_path:
                    search_services.add(search_service_path)
                    tool_info["search_service"] = search_service_path
                    # Extract database and schema from the search service path
                    # Format is typically: DATABASE.SCHEMA.SEARCH_SERVICE_NAME
                    path_parts = search_service_path.split('.')
                    if len(path_parts) >= 2:
                        search_db = path_parts[0]
                        search_schema = path_parts[1]
                        databases.add(search_db)
                        schemas.add(f"{search_db}.{search_schema}")
                    else:
                        # Fallback to parsed values if path parsing fails
                        databases.add(database_name)
                        schemas.add(f"{database_name}.{schema_name}")

            elif tool_type == "generic":
                if full_resource_path:
                    # Extract database and schema from the full_resource_path for procedures
                    # Format is typically: DATABASE.SCHEMA.PROCEDURE_NAME
                    path_parts = full_resource_path.split('.')
                    if len(path_parts) >= 2:
                        proc_db = path_parts[0]
                        proc_schema = path_parts[1]
                    else:
                        # Fallback to parsed values if path parsing fails
                        proc_db = database_name
                        proc_schema = schema_name

                    # Use procedure name with types if available, otherwise use full_resource_path
                    if procedure_name_with_types:
                        # Combine database.schema with procedure name and types
                        procedure_signature = f"{proc_db}.{proc_schema}.{procedure_name_with_types}"
                    else:
                        procedure_signature = full_resource_path
                    procedures.add(procedure_signature)
                    tool_info["procedure"] = procedure_signature
                    databases.add(proc_db)
                    schemas.add(f"{proc_db}.{proc_schema}")

            tool_details.append(tool_info)

        # Add agent's own database and schema
        databases.add(database)
        schemas.add(f"{database}.{schema}")

        return {
            "semantic_views": list(semantic_views),
            "semantic_model_files": list(semantic_model_files),
            "semantic_model_stages": list(semantic_model_stages),
            "search_services": list(search_services),
            "procedures": list(procedures),
            "databases": list(databases),
            "schemas": list(schemas),
            "tool_details": tool_details,
            "tool_warehouses": tool_warehouses,
            "agent_name": agent_name,
            "agent_database": database,
            "agent_schema": schema,
            "tools_df": df
        }

    except Exception as e:
        st.error(f"Error parsing agent tools: {e}")
        return {
            "semantic_views": [],
            "semantic_model_files": [],
            "semantic_model_stages": [],
            "search_services": [],
            "procedures": [],
            "databases": [],
            "schemas": [],
            "tool_details": [],
            "tool_warehouses": {},
            "agent_name": agent_name,
            "agent_database": database,
            "agent_schema": schema,
            "tools_df": pd.DataFrame()
        }

def extract_stage_info_from_semantic_model_file(semantic_model_file: str):
    """Extract stage information from semantic model file path like @DB.SCHEMA.STAGE/file.yaml"""
    if not semantic_model_file or not semantic_model_file.startswith('@'):
        return None, None, None
    
    stage_path = semantic_model_file[1:]  # Remove @
    path_parts = stage_path.split('/')
    
    if len(path_parts) >= 1:
        stage_identifier = path_parts[0]
        stage_parts = stage_identifier.split('.')
        
        if len(stage_parts) >= 3:
            return stage_parts[0], stage_parts[1], stage_parts[2]
    
    return None, None, None

def read_yaml_from_stage(_session, semantic_model_file: str):
    """
    Read YAML content from a stage using Snowflake session.

    Args:
        _session: Active Snowflake session
        semantic_model_file: Path to semantic model file (e.g., @DATABASE.SCHEMA.STAGE/file.yaml)

    Returns:
        Parsed YAML content as dictionary, or None if failed
    """
    try:
        # Extract stage information
        database, schema, stage_name = extract_stage_info_from_semantic_model_file(
            semantic_model_file)

        if not all([database, schema, stage_name]):
            st.write(
                f"Could not parse stage information from {semantic_model_file}")
            return None

        file_name = semantic_model_file.split('/')[-1]

        st.write(
            f"Reading file from stage: @{database}.{schema}.{stage_name}/{file_name}")

        # First, check if the file exists using LIST
        list_query = f"LIST @{database}.{schema}.{stage_name}/{file_name}"
        try:
            list_result = _session.sql(list_query).collect()
            if not list_result:
                st.write(f"File not found: {semantic_model_file}")
                return None
        except Exception as e:
            st.write(f"Error listing file: {e}")
            return None

        # Try a simpler approach: Use COPY INTO with a regular table and ROW_NUMBER for ordering
        try:
            st.write(f"Reading file content using COPY INTO...")

            # Create a regular table (not temporary) to avoid the stored procedure limitation
            table_name = f"YAML_TEMP_{abs(hash(semantic_model_file)) % 10000}"

            # Create table with row number for ordering
            create_query = f"""
            CREATE OR REPLACE TABLE {table_name} (
                row_num INTEGER AUTOINCREMENT,
                line_content STRING
            )
            """
            _session.sql(create_query).collect()

            # Copy file content
            copy_query = f"""
            COPY INTO {table_name} (line_content)
            FROM @{database}.{schema}.{stage_name}/{file_name}
            FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = NONE FIELD_OPTIONALLY_ENCLOSED_BY = NONE)
            ON_ERROR = 'CONTINUE'
            """
            _session.sql(copy_query).collect()

            # Read content using ROW_NUMBER() for ordering
            select_query = f"""
            SELECT LISTAGG(line_content, '\\n') WITHIN GROUP (ORDER BY row_num) as file_content
            FROM {table_name}
            WHERE line_content IS NOT NULL
            """

            result = _session.sql(select_query).collect()

            if result and result[0]['FILE_CONTENT']:
                file_content = result[0]['FILE_CONTENT']
                st.write(
                    f"File content read successfully ({len(file_content)} characters)")

                # Parse YAML content
                st.write(f"Parsing YAML content...")
                import yaml
                yaml_data = yaml.safe_load(file_content)
                st.write(f"YAML file parsed successfully!")

                # Clean up
                _session.sql(f"DROP TABLE IF EXISTS {table_name}").collect()

                return yaml_data
            else:
                st.write(f"No content found for {semantic_model_file}")
                _session.sql(f"DROP TABLE IF EXISTS {table_name}").collect()
                return None

        except Exception as e:
            st.write(f"Error reading file content: {e}")

            # Final fallback: Try without ordering
            try:
                st.write(f"Trying final fallback approach...")

                # Create table without autoincrement
                table_name = f"YAML_TEMP_{abs(hash(semantic_model_file)) % 10000}"

                create_query = f"""
                CREATE OR REPLACE TABLE {table_name} (
                    line_content STRING
                )
                """
                _session.sql(create_query).collect()

                # Copy file content
                copy_query = f"""
                COPY INTO {table_name}
                FROM @{database}.{schema}.{stage_name}/{file_name}
                FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = NONE FIELD_OPTIONALLY_ENCLOSED_BY = NONE)
                ON_ERROR = 'CONTINUE'
                """
                _session.sql(copy_query).collect()

                # Read content without ordering
                select_query = f"""
                SELECT LISTAGG(line_content, '\\n') as file_content
                FROM {table_name}
                WHERE line_content IS NOT NULL
                """

                result = _session.sql(select_query).collect()

                if result and result[0]['FILE_CONTENT']:
                    file_content = result[0]['FILE_CONTENT']
                    st.write(
                        f"File content read successfully ({len(file_content)} characters)")

                    # Parse YAML content
                    st.write(f"Parsing YAML content...")
                    import yaml
                    yaml_data = yaml.safe_load(file_content)
                    st.write(f"YAML file parsed successfully!")

                    # Clean up
                    _session.sql(f"DROP TABLE IF EXISTS {table_name}").collect()

                    return yaml_data
                else:
                    st.write(
                        f"No content found for {semantic_model_file}")
                    _session.sql(f"DROP TABLE IF EXISTS {table_name}").collect()
                    return None

            except Exception as e2:
                st.write(f"Final fallback approach also failed: {e2}")
                return None

    except Exception as e:
        st.write(f"Error reading YAML from stage: {e}")
        return None

def extract_table_permissions_from_yaml(yaml_content):
    """
    Extract table permissions and Cortex Search Services from parsed YAML content and identify the format type.
    Enhanced to handle different YAML formats for semantic models.

    Args:
        yaml_content: Parsed YAML content from semantic view or semantic model file

    Returns:
        Tuple of (table_permissions_list, cortex_search_services_list, format_type)
        table_permissions_list: List of tuples (database, schema, table_name)
        cortex_search_services_list: List of Cortex Search Service paths
        format_type: "semantic model", "semantic view", or "unknown"
    """
    table_permissions = []
    cortex_search_services = []
    format_type = "unknown"

    if not yaml_content:
        return table_permissions, cortex_search_services, format_type

    # Method 1: Check for semantic_model first (more specific)
    if "semantic_model" in yaml_content:
        format_type = "semantic model"
        semantic_model = yaml_content["semantic_model"]

        if "tables" in semantic_model:
            for table in semantic_model["tables"]:
                if isinstance(table, dict):
                    database = table.get("database") or table.get("db")
                    schema = table.get("schema") or table.get("schema_name")
                    table_name = table.get("table") or table.get(
                        "table_name") or table.get("name")

                    if database and schema and table_name:
                        table_permissions.append(
                            (database, schema, table_name))

    # Method 2: Standard semantic view format (fallback)
    elif "tables" in yaml_content:
        format_type = "semantic view"
        for table in yaml_content["tables"]:
            if "base_table" in table:
                base_table = table["base_table"]
                database = base_table.get("database")
                schema = base_table.get("schema")
                table_name = base_table.get("table")

                if database and schema and table_name:
                    table_permissions.append((database, schema, table_name))

    # Extract Cortex Search Services from YAML content
    def find_cortex_search_services(obj, path=""):
        """Recursively find Cortex Search Service references in YAML structure"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.lower() == 'cortex_search_service' and isinstance(value, dict):
                    database = value.get("database") or value.get("db")
                    schema = value.get("schema") or value.get("schema_name")
                    service = value.get("service") or value.get(
                        "service_name") or value.get("name")

                    if database and schema and service:
                        service_path = f"{database}.{schema}.{service}"
                        cortex_search_services.append(service_path)
                elif isinstance(value, (dict, list)):
                    find_cortex_search_services(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    find_cortex_search_services(item, f"{path}[{i}]")

    # Run the recursive search for Cortex Search Services
    find_cortex_search_services(yaml_content)

    # Method 3: Recursive search for table references in any nested structure
    def find_table_references(obj, path=""):
        """Recursively find table references in YAML structure"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.lower() in ['table', 'base_table', 'source_table'] and isinstance(value, dict):
                    database = value.get("database") or value.get("db")
                    schema = value.get("schema") or value.get("schema_name")
                    table_name = value.get("table") or value.get(
                        "table_name") or value.get("name")

                    if database and schema and table_name:
                        table_permissions.append(
                            (database, schema, table_name))
                elif isinstance(value, (dict, list)):
                    find_table_references(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    find_table_references(item, f"{path}[{i}]")

    # Run the recursive search
    find_table_references(yaml_content)

    # Remove duplicates while preserving order
    seen = set()
    unique_permissions = []
    for perm in table_permissions:
        if perm not in seen:
            seen.add(perm)
            unique_permissions.append(perm)

    # Remove duplicates from Cortex Search Services
    seen_services = set()
    unique_services = []
    for service in cortex_search_services:
        if service not in seen_services:
            seen_services.add(service)
            unique_services.append(service)

    return unique_permissions, unique_services, format_type

@st.cache_data(show_spinner="Analyzing semantic view...", ttl=300)
def get_semantic_view_yaml(_session, view_name):
    """Get YAML definition from semantic view."""
    try:
        # Try SYSTEM$GET_SEMANTIC_MODEL_DEFINITION first (newer function)
        try:
            result_df = _session.sql(
                f"SELECT SYSTEM$GET_SEMANTIC_MODEL_DEFINITION('{view_name}') as yaml_def"
            ).to_pandas()
            if not result_df.empty:
                result_df.columns = [col.strip('"').lower() for col in result_df.columns]
                for col_name in ['yaml_def', 'system$get_semantic_model_definition', result_df.columns[0]]:
                    if col_name in result_df.columns:
                        yaml_content = result_df.iloc[0][col_name]
                        if yaml_content and not pd.isna(yaml_content):
                            return yaml_content
        except:
            pass  # Try the older function
        
        # Try SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW (older function)
        result_df = _session.sql(
            f"SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('{view_name}') as yaml_def"
        ).to_pandas()
        if not result_df.empty:
            result_df.columns = [col.strip('"').lower() for col in result_df.columns]
            for col_name in ['yaml_def', 'system$read_yaml_from_semantic_view', result_df.columns[0]]:
                if col_name in result_df.columns:
                    yaml_content = result_df.iloc[0][col_name]
                    if yaml_content and not pd.isna(yaml_content):
                        return yaml_content
        return None
    except Exception as e:
        st.warning(f"Could not read YAML from {view_name}: {str(e)}")
        return None

def execute_semantic_model_file_queries(_session, semantic_model_files):
    """Execute semantic model file queries and extract table permissions and Cortex Search Services."""
    table_results = {}
    search_service_results = {}

    for semantic_model_file in semantic_model_files:
        try:
            st.write(f"Processing semantic model file: {semantic_model_file}")

            # Read YAML content from stage using session
            yaml_content = read_yaml_from_stage(
                _session, semantic_model_file)

            if yaml_content:
                # Extract table permissions, Cortex Search Services, and format type
                table_permissions, cortex_search_services, format_type = extract_table_permissions_from_yaml(
                    yaml_content)
                table_results[semantic_model_file] = table_permissions
                search_service_results[semantic_model_file] = cortex_search_services

                st.write(
                    f"  Found {len(table_permissions)} tables: {[f'{db}.{schema}.{table}' for db, schema, table in table_permissions]}")
                if cortex_search_services:
                    st.write(
                        f"  Found {len(cortex_search_services)} Cortex Search Services: {cortex_search_services}")
            else:
                st.write(f"  No YAML content found for {semantic_model_file}")
                table_results[semantic_model_file] = []
                search_service_results[semantic_model_file] = []

        except Exception as e:
            st.error(f"  Error processing {semantic_model_file}: {e}")
            table_results[semantic_model_file] = []
            search_service_results[semantic_model_file] = []

    return table_results, search_service_results

def execute_semantic_view_queries(_session, semantic_views):
    """Execute semantic view queries and extract table permissions and Cortex Search Services."""
    table_results = {}
    search_service_results = {}

    for semantic_view in semantic_views:
        try:
            # Execute the query
            query = f"SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('{semantic_view}') as yaml_content"
            result = _session.sql(query).collect()

            if result and result[0]['YAML_CONTENT']:
                # Parse YAML content
                import yaml
                yaml_content = yaml.safe_load(result[0]['YAML_CONTENT'])

                # Extract table permissions, Cortex Search Services, and format type
                table_permissions, cortex_search_services, format_type = extract_table_permissions_from_yaml(
                    yaml_content)
                table_results[semantic_view] = table_permissions
                search_service_results[semantic_view] = cortex_search_services

                # Use appropriate processing message based on format type
                if format_type == "semantic model":
                    st.write(f"Processing semantic model: {semantic_view}")
                else:
                    st.write(f"Processing semantic view: {semantic_view}")

                st.write(
                    f"  Found {len(table_permissions)} tables: {[f'{db}.{schema}.{table}' for db, schema, table in table_permissions]}")
                if cortex_search_services:
                    st.write(
                        f"  Found {len(cortex_search_services)} Cortex Search Services: {cortex_search_services}")

            else:
                st.write(f"Processing semantic view: {semantic_view}")
                st.write(f"  No YAML content found for {semantic_view}")
                table_results[semantic_view] = []
                search_service_results[semantic_view] = []

        except Exception as e:
            st.error(f"  Error processing {semantic_view}: {e}")
            table_results[semantic_view] = []
            search_service_results[semantic_view] = []

    return table_results, search_service_results

# Compile regex pattern once for better performance
TABLE_PATTERN = re.compile(r'(?:table|from):\s*([A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*)', re.IGNORECASE)

def parse_tables_from_yaml(yaml_content):
    """Extract table references from semantic view YAML."""
    if not yaml_content:
        return []
    return list(set(TABLE_PATTERN.findall(yaml_content)))

def check_cortex_database_role_grants(_session, role_name):
    """
    Check if a role has CORTEX_USER or CORTEX_ADMIN database role grants.
    
    Uses the same assumption as the Agent Permission Generator:
    - By default, SNOWFLAKE.CORTEX_USER is granted to PUBLIC role
    - All roles inherit from PUBLIC, so all roles have Cortex access
    - We just check if there are explicit grants to show the method
    
    See: https://docs.snowflake.com/en/sql-reference/snowflake-db-roles#snowflake-cortex-user-database-role
    
    Returns: tuple (has_access, method, found_roles)
        - has_access: Boolean indicating if role has Cortex access (always True)
        - method: 'explicit' if directly granted, 'via_public' otherwise
        - found_roles: List of Cortex database roles found
    """
    try:
        # Check if this role has explicit Cortex database role grants
        # Use the same approach as get_role_grants function
        grants_df = _session.sql(f"""
            SELECT NAME
            FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
            WHERE GRANTEE_NAME = '{role_name.upper()}'
              AND GRANTED_ON = 'DATABASE_ROLE'
              AND DELETED_ON IS NULL
              AND NAME LIKE 'SNOWFLAKE.CORTEX%'
        """).to_pandas()
        
        if not grants_df.empty:
            # Role has explicit Cortex grants
            found_roles = grants_df['NAME'].tolist()
            return True, 'explicit', found_roles
        else:
            # No explicit grant, but assume access via PUBLIC (Snowflake default)
            # This matches the Agent Permission Generator logic
            return True, 'via_public', ['SNOWFLAKE.CORTEX_USER']
        
    except Exception as e:
        # If query fails, assume access via PUBLIC (same as Agent Permission Generator)
        return True, 'via_public', ['SNOWFLAKE.CORTEX_USER']

def test_cortex_access(_session, role_name):
    """
    Test if a role has actual Cortex access by attempting to use COMPLETE function.
    This is a fallback method when database role checking is inconclusive.
    """
    try:
        # Save current role
        current_role_result = _session.sql("SELECT CURRENT_ROLE() AS role").collect()
        original_role = current_role_result[0]['ROLE'] if current_role_result else None
        
        # Try to use the role and call a Cortex function
        _session.sql(f"USE ROLE {role_name}").collect()
        _session.sql("SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic', 'Hi') AS test_result").collect()
        return True
    except Exception as e:
        error_msg = str(e).lower()
        # If error is about privileges, role doesn't have Cortex access
        if 'privilege' in error_msg or 'permission' in error_msg or 'not authorized' in error_msg:
            return False
        # Other errors (model not available, etc.) we'll assume access is OK
        # since the permission check passed
        if 'does not exist' in error_msg or 'not found' in error_msg:
            return True  # Permission was OK, just model/resource issue
        return False
    finally:
        # Always try to switch back to original role
        try:
            if original_role:
                _session.sql(f"USE ROLE {original_role}").collect()
            else:
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

def analyze_grants(grants_df, actual_cortex_access=None, role_name=None, cortex_check_result=None):
    """
    Analyze grants DataFrame and return all metrics in one pass - more efficient.
    
    Args:
        grants_df: DataFrame of grants
        actual_cortex_access: Optional boolean from actual Cortex function test (deprecated, use cortex_check_result)
        role_name: Optional role name for display purposes
        cortex_check_result: Optional tuple (has_access, method, found_roles) from check_cortex_database_role_grants
    """
    if grants_df.empty:
        # Even with empty grants, check cortex access via database roles
        if cortex_check_result and cortex_check_result[0]:
            has_cortex = True
            cortex_method = cortex_check_result[1]
            found_roles = cortex_check_result[2]
        elif actual_cortex_access is not None:
            has_cortex = actual_cortex_access
            cortex_method = 'implicit' if actual_cortex_access else 'none'
            found_roles = []
        else:
            has_cortex = False
            cortex_method = 'none'
            found_roles = []
            
        return {
            'has_cortex': has_cortex,
            'cortex_method': cortex_method,
            'found_roles': found_roles,
            'wh_count': 0,
            'db_count': 0,
            'table_count': 0,
            'readiness_score': 1 if has_cortex else 0,
            'issues': ['No grants found'] if not has_cortex else ['No grants found (but has Cortex access)']
        }
    
    # Use cortex_check_result if provided (preferred method)
    if cortex_check_result is not None:
        has_cortex, cortex_method, found_roles = cortex_check_result
    else:
        # Fall back to checking grants DataFrame for explicit Cortex role grants
        required_roles = ['SNOWFLAKE.CORTEX_USER', 'SNOWFLAKE.CORTEX_ANALYST_USER', 'SNOWFLAKE.CORTEX_ADMIN']
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

def generate_comprehensive_permission_script(
    parsed_tools,
    table_permissions_results,
    yaml_cortex_search_services,
    warehouse_name="COMPUTE_WH"
):
    """Generate comprehensive SQL permission script."""
    agent_name = parsed_tools["agent_name"]
    agent_database = parsed_tools["agent_database"]
    agent_schema = parsed_tools["agent_schema"]
    fully_qualified_agent = f"{agent_database}.{agent_schema}.{agent_name}"

    # Collect all unique table permissions
    all_table_permissions = set()
    for tables in table_permissions_results.values():
        for db, schema, table in tables:
            all_table_permissions.add(f"{db}.{schema}.{table}")

    # Generate database and schema USAGE grants
    all_db_grants = set(parsed_tools["databases"])
    all_schema_grants = set(parsed_tools["schemas"])

    # CRITICAL: Add database and schema grants for tables discovered in semantic view YAML
    # that are not already covered by the agent tool specifications
    table_db_grants = set()
    table_schema_grants = set()

    for tables in table_permissions_results.values():
        for db, schema, table in tables:
            table_db_grants.add(db)
            table_schema_grants.add(f"{db}.{schema}")

    # Combine all database and schema grants
    all_db_grants = all_db_grants.union(table_db_grants)
    all_schema_grants = all_schema_grants.union(table_schema_grants)

    # Generate permission grants
    db_grants = "\n".join([f"GRANT USAGE ON DATABASE {db} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);"
                          for db in sorted(all_db_grants)])

    schema_grants = "\n".join([f"GRANT USAGE ON SCHEMA {schema} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);"
                              for schema in sorted(all_schema_grants)])

    view_grants = "\n".join([f"GRANT SELECT ON VIEW {view} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);"
                            for view in sorted(parsed_tools["semantic_views"])])

    table_grants = "\n".join([f"GRANT SELECT ON TABLE {table} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);"
                              for table in sorted(all_table_permissions)])

    # Combine tool-specified and YAML-extracted Cortex Search Services
    all_search_services = set(parsed_tools["search_services"]).union(
        yaml_cortex_search_services)

    search_grants = "\n".join([f"GRANT USAGE ON CORTEX SEARCH SERVICE {service} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);"
                              for service in sorted(all_search_services)])

    procedure_grants = "\n".join([f"GRANT USAGE ON PROCEDURE {procedure} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);"
                                  for procedure in sorted(parsed_tools.get("procedures", []))])

    # Generate stage grants for semantic model files
    stage_grants = "\n".join([f"GRANT READ ON STAGE {stage} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);"
                              for stage in sorted(parsed_tools.get("semantic_model_stages", []))])

    # Generate tool-specific warehouse grants
    tool_warehouse_grants = ""
    if parsed_tools.get("tool_warehouses"):
        tool_warehouse_grants = "\n".join([
            f"GRANT USAGE ON WAREHOUSE IDENTIFIER('{warehouse}') TO ROLE IDENTIFIER($AGENT_ROLE_NAME); -- Required for tool: {tool_name}"
            for tool_name, warehouse in parsed_tools["tool_warehouses"].items()
        ])
        if tool_warehouse_grants:
            tool_warehouse_grants = f"\n-- Tool-specific warehouse permissions\n{tool_warehouse_grants}"

    # Assemble the complete script
    script = f"""-- =========================================================================================
-- AUTO-GENERATED LEAST-PRIVILEGE SCRIPT FOR AGENT: {fully_qualified_agent}
-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Generated by: Snowflake Cortex Agent Permission Generator
-- =========================================================================================

-- IMPORTANT: Review and adjust the placeholder variables below for your environment.
SET AGENT_ROLE_NAME = '{agent_name}_USER_ROLE';
SET WAREHOUSE_NAME = '{warehouse_name}';

-- Create a dedicated role for the agent's permissions.
USE ROLE SECURITYADMIN; -- Or your own privileged role to assign permissions
CREATE ROLE IF NOT EXISTS IDENTIFIER($AGENT_ROLE_NAME);
GRANT ROLE IDENTIFIER($AGENT_ROLE_NAME) TO ROLE SYSADMIN; -- Optional: Allows SYSADMIN to manage the role.

-- Grant core permission to use the agent object itself.
GRANT USAGE ON AGENT {fully_qualified_agent} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);

-- Grant permissions on the underlying database objects required by the agent's tools.
-- NOTE: These permissions are derived from the agent's tool specification and semantic view YAML definitions.

-- Database and Schema USAGE grants (including agent location, tool-specific locations, and tables from semantic views)
{db_grants}
{schema_grants}

-- Permissions for 'cortex_analyst_text_to_sql' tools
-- Semantic view permissions
{view_grants}

-- Base table permissions (from semantic view YAML)
{table_grants}

-- Permissions for 'cortex_search' tools
{search_grants}

-- Permissions for 'generic' tools (procedures)
{procedure_grants}

-- Permissions for semantic model files (stages)
{stage_grants}

{tool_warehouse_grants}

-- Grant warehouse usage to the role for the user's session.
GRANT USAGE ON WAREHOUSE IDENTIFIER($WAREHOUSE_NAME) TO ROLE IDENTIFIER($AGENT_ROLE_NAME);

-- =========================================================================================
SELECT 'Setup complete for role ' || $AGENT_ROLE_NAME AS "Status";
-- =========================================================================================
"""

    return script

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

def generate_smart_permission_script(
    role_name,
    grants_df,
    parsed_tools,
    table_permissions_results,
    yaml_cortex_search_services,
    warehouse_name="COMPUTE_WH"
):
    """
    Generate SQL script with ONLY missing permissions by comparing what role has vs what agent needs.
    This is the smart version that avoids duplicate grants.
    """
    agent_name = parsed_tools["agent_name"]
    agent_database = parsed_tools["agent_database"]
    agent_schema = parsed_tools["agent_schema"]
    fully_qualified_agent = f"{agent_database}.{agent_schema}.{agent_name}"
    
    # Get what the role currently has
    existing_grants = {
        'databases': set(),
        'schemas': set(),
        'tables': set(),
        'views': set(),
        'agents': set(),
        'search_services': set(),
        'procedures': set(),
        'stages': set(),
        'warehouses': set()
    }
    
    for _, row in grants_df.iterrows():
        obj_name = row['OBJECT_NAME']
        granted_on = row['GRANTED_ON']
        
        if granted_on == 'DATABASE':
            existing_grants['databases'].add(obj_name.upper())
        elif granted_on == 'SCHEMA':
            existing_grants['schemas'].add(obj_name.upper())
        elif granted_on == 'TABLE':
            existing_grants['tables'].add(obj_name.upper())
        elif granted_on == 'VIEW':
            existing_grants['views'].add(obj_name.upper())
        elif granted_on == 'AGENT':
            existing_grants['agents'].add(obj_name.upper())
        elif granted_on == 'CORTEX SEARCH SERVICE':
            existing_grants['search_services'].add(obj_name.upper())
        elif granted_on == 'PROCEDURE':
            existing_grants['procedures'].add(obj_name.upper())
        elif granted_on == 'STAGE':
            existing_grants['stages'].add(obj_name.upper())
        elif granted_on == 'WAREHOUSE':
            existing_grants['warehouses'].add(obj_name.upper())
    
    # Collect what the agent needs
    needed_databases = set(parsed_tools["databases"])
    needed_schemas = set(parsed_tools["schemas"])
    needed_views = set(parsed_tools["semantic_views"])
    needed_search_services = set(parsed_tools["search_services"]).union(yaml_cortex_search_services)
    needed_procedures = set(parsed_tools.get("procedures", []))
    needed_stages = set(parsed_tools.get("semantic_model_stages", []))
    
    # Collect tables from semantic views
    needed_tables = set()
    for tables in table_permissions_results.values():
        for db, schema, table in tables:
            needed_tables.add(f"{db}.{schema}.{table}")
            needed_databases.add(db)
            needed_schemas.add(f"{db}.{schema}")
    
    # Calculate MISSING permissions
    missing_databases = [db for db in needed_databases if db.upper() not in existing_grants['databases']]
    missing_schemas = [schema for schema in needed_schemas if schema.upper() not in existing_grants['schemas']]
    missing_views = [view for view in needed_views if view.upper() not in existing_grants['views']]
    missing_tables = [table for table in needed_tables if table.upper() not in existing_grants['tables']]
    missing_search_services = [svc for svc in needed_search_services if svc.upper() not in existing_grants['search_services']]
    missing_procedures = [proc for proc in needed_procedures if proc.upper() not in existing_grants['procedures']]
    missing_stages = [stage for stage in needed_stages if stage.upper() not in existing_grants['stages']]
    missing_agent = fully_qualified_agent.upper() not in existing_grants['agents']
    missing_warehouse = warehouse_name.upper() not in existing_grants['warehouses']
    
    # Generate SQL for ONLY missing permissions
    sql_parts = []
    
    sql_parts.append(f"""-- =========================================================================================
-- SMART PERMISSION FIX FOR ROLE: {role_name}
-- Agent: {fully_qualified_agent}
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- =========================================================================================
-- This script grants ONLY the missing permissions (existing grants are skipped)
-- =========================================================================================

USE ROLE SECURITYADMIN;
""")
    
    # Count missing permissions
    total_missing = (
        len(missing_databases) + len(missing_schemas) + len(missing_views) +
        len(missing_tables) + len(missing_search_services) + len(missing_procedures) +
        len(missing_stages) + (1 if missing_agent else 0) + (1 if missing_warehouse else 0)
    )
    
    if total_missing == 0:
        sql_parts.append(f"""-- ✅ ROLE {role_name} ALREADY HAS ALL REQUIRED PERMISSIONS!
-- No grants needed. Role is fully configured for this agent.

SELECT '✅ Role {role_name} is already fully configured!' AS "Status";
""")
        return "\n".join(sql_parts)
    
    sql_parts.append(f"-- Missing permissions: {total_missing}\n")
    
    # Agent access
    if missing_agent:
        sql_parts.append(f"""-- Grant agent access
GRANT USAGE ON AGENT {fully_qualified_agent} TO ROLE {role_name};
""")
    
    # Database grants
    if missing_databases:
        sql_parts.append("-- Database USAGE grants (missing)")
        for db in sorted(missing_databases):
            sql_parts.append(f"GRANT USAGE ON DATABASE {db} TO ROLE {role_name};")
        sql_parts.append("")
    
    # Schema grants
    if missing_schemas:
        sql_parts.append("-- Schema USAGE grants (missing)")
        for schema in sorted(missing_schemas):
            sql_parts.append(f"GRANT USAGE ON SCHEMA {schema} TO ROLE {role_name};")
        sql_parts.append("")
    
    # View grants
    if missing_views:
        sql_parts.append("-- Semantic view permissions (missing)")
        for view in sorted(missing_views):
            sql_parts.append(f"GRANT SELECT ON VIEW {view} TO ROLE {role_name};")
        sql_parts.append("")
    
    # Table grants
    if missing_tables:
        sql_parts.append("-- Base table permissions (missing)")
        for table in sorted(missing_tables):
            sql_parts.append(f"GRANT SELECT ON TABLE {table} TO ROLE {role_name};")
        sql_parts.append("")
    
    # Search service grants
    if missing_search_services:
        sql_parts.append("-- Cortex Search Service permissions (missing)")
        for service in sorted(missing_search_services):
            sql_parts.append(f"GRANT USAGE ON CORTEX SEARCH SERVICE {service} TO ROLE {role_name};")
        sql_parts.append("")
    
    # Procedure grants
    if missing_procedures:
        sql_parts.append("-- Procedure permissions (missing)")
        for procedure in sorted(missing_procedures):
            sql_parts.append(f"GRANT USAGE ON PROCEDURE {procedure} TO ROLE {role_name};")
        sql_parts.append("")
    
    # Stage grants
    if missing_stages:
        sql_parts.append("-- Stage permissions (missing)")
        for stage in sorted(missing_stages):
            sql_parts.append(f"GRANT READ ON STAGE {stage} TO ROLE {role_name};")
        sql_parts.append("")
    
    # Warehouse grant
    if missing_warehouse:
        sql_parts.append(f"""-- Warehouse access (missing)
GRANT USAGE ON WAREHOUSE {warehouse_name} TO ROLE {role_name};
""")
    
    sql_parts.append(f"""-- =========================================================================================
SELECT '✅ Granted {total_missing} missing permissions to role {role_name}' AS "Status";
-- =========================================================================================
""")
    
    return "\n".join(sql_parts)

# ------------------------------------
# Main Application
# ------------------------------------

def main():
    # Hero section with better branding
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem 0 1rem 0;'>
        <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>
            Snowflake Intelligence & Cortex Access Checker
        </h1>
        <p style='font-size: 1.2rem; color: #888; margin-bottom: 0.5rem;'>
            Intelligent Permission Management for Cortex AI Agents
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights - centered layout
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### Auto-Generate SQL")
            st.markdown("Create least-privilege scripts instantly")
        with col_b:
            st.markdown("### Role Compatibility")
            st.markdown("Check if roles can use agents")
    
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
        ["Agent Permission Generator", "Cortex Role Check"],
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
                            # Check Cortex database role grants (including PUBLIC and hierarchy)
                            with st.spinner("Checking Cortex access..."):
                                cortex_check = check_cortex_database_role_grants(session, role_name)
                            
                            # Analyze grants with cortex check result
                            analysis = analyze_grants(grants_df, role_name=role_name, cortex_check_result=cortex_check)
                            
                            # Metrics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            # Show Cortex access with method indicator
                            cortex_display = "No"
                            if analysis['has_cortex']:
                                if analysis['cortex_method'] == 'explicit':
                                    cortex_display = "Yes (Direct)"
                                elif analysis['cortex_method'] == 'via_public':
                                    cortex_display = "Yes (via PUBLIC)"
                                elif analysis['cortex_method'] == 'via_hierarchy':
                                    cortex_display = "Yes (Inherited)"
                                else:
                                    cortex_display = "Yes"
                            
                            col1.metric("Cortex Access", cortex_display)
                            col2.metric("Warehouses", analysis['wh_count'])
                            col3.metric("Databases", analysis['db_count'])
                            col4.metric("Tables/Views", analysis['table_count'])
                            
                            # Add explanation for different access methods
                            if analysis['has_cortex']:
                                if analysis['cortex_method'] == 'via_public':
                                    roles_str = ", ".join(analysis['found_roles']) if analysis['found_roles'] else "CORTEX_USER"
                                    st.info(f"This role has Cortex access because **{roles_str}** is granted to the PUBLIC role (Snowflake default)")
                                elif analysis['cortex_method'] == 'via_hierarchy':
                                    roles_str = ", ".join(analysis['found_roles']) if analysis['found_roles'] else "Cortex roles"
                                    st.info(f"This role inherits Cortex access through role hierarchy: **{roles_str}**")
                                elif analysis['cortex_method'] == 'explicit':
                                    roles_str = ", ".join(analysis['found_roles']) if analysis['found_roles'] else "Cortex roles"
                                    st.success(f"This role has explicit Cortex database role grants: **{roles_str}**")
                            
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
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.download_button(
                                            label="Download SQL Script",
                                            data=sql_script,
                                            file_name=f"fix_{role_name}_permissions.sql",
                                            mime="text/plain",
                                            key=f"download_remediation_{role_name}",
                                            use_container_width=True
                                        )
                                    with col2:
                                        exec_key = f"exec_remediation_{role_name}"
                                        if st.button("Execute SQL", key=f"btn_{exec_key}", type="primary", use_container_width=True):
                                            st.session_state[exec_key] = True
                                    
                                    # Show execution results below buttons (prevents scroll to top)
                                    if st.session_state.get(exec_key, False):
                                        with st.spinner("Executing remediation SQL..."):
                                            try:
                                                # Count statements for feedback
                                                statement_count = len([s for s in sql_script.split(';') if s.strip() and not s.strip().startswith('--')])
                                                
                                                # Execute the entire script as a multi-statement SQL
                                                # This preserves variable context (SET statements work)
                                                result = session.sql(sql_script).collect()
                                                
                                                st.success(f"Remediation executed successfully! ({statement_count} statements)")
                                                
                                                # Show what was fixed
                                                st.markdown("**Permissions granted:**")
                                                for issue in analysis['issues']:
                                                    if "Cortex database role" in issue:
                                                        st.markdown(f"- ✓ Cortex database role granted to `{role_name}`")
                                                    elif "warehouse" in issue.lower():
                                                        st.markdown(f"- ✓ Warehouse usage granted")
                                                    elif "database" in issue.lower() or "schema" in issue.lower():
                                                        st.markdown(f"- ✓ Database/Schema access granted")
                                                    elif "table" in issue.lower():
                                                        st.markdown(f"- ✓ Table permissions granted")
                                                
                                                with st.expander("View Execution Details"):
                                                    if result:
                                                        st.write("**Final result:**")
                                                        for row in result:
                                                            st.json(row.as_dict())
                                                    st.write(f"**Total statements executed:** {statement_count}")
                                                    st.write(f"**Executed at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                                                
                                                # Clear the execution flag
                                                st.session_state[exec_key] = False
                                            except Exception as e:
                                                st.error(f"Error executing SQL: {str(e)}")
                                                st.info("**Common issues:**\n- Need SECURITYADMIN or higher privileges\n- Some grants may already exist")
                                                with st.expander("View Error Details"):
                                                    st.code(str(e))
                                                st.session_state[exec_key] = False
                            
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
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            database = st.text_input(
                "Agent Database",
                value="",
                placeholder="e.g., SNOWFLAKE_INTELLIGENCE",
                key="agent_db"
            )
        
        with col2:
            schema = st.text_input(
                "Agent Schema",
                value="",
                placeholder="e.g., AGENTS",
                key="agent_schema"
            )
        
        with col3:
            # Get agent names for dropdown if database and schema are provided
            if database and schema:
                agent_names = get_agent_names(session, database, schema)
                agent_name = st.selectbox(
                    "Agent Name - Select Other for Manual Entry",
                    options=agent_names,
                    key="agent_name_select"
                )
                
                # If "Other" is selected, show text input
                if agent_name == "Other":
                    agent_name = st.text_input(
                        "Manually Enter Agent Name",
                        value="",
                        placeholder="e.g., SI_CYBERSECURITY_ANALYST",
                        key="agent_name_manual"
                    )
            else:
                agent_name = st.text_input(
                    "Agent Name",
                    value="",
                    placeholder="Enter database and schema first",
                    disabled=True,
                    key="agent_name_disabled"
                )
        
        # Generate button
        if st.button("Generate Permission Script", type="primary", use_container_width=True):
            if not database or not schema or not agent_name:
                st.error("Please fill in all agent fields")
            else:
                # Parse agent tools
                with st.spinner("Parsing agent tools..."):
                    parsed_tools = parse_agent_tools_with_sql(
                        session, database, schema, agent_name)

                if parsed_tools["tools_df"].empty:
                    st.error("No tools found in agent specification")
                else:
                    # Display parsed tools
                    st.markdown(
                        '<div class="section-header">Parsed Tool Information</div>', unsafe_allow_html=True)

                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Total Tools", len(parsed_tools["tool_details"]))
                    with col2:
                        st.metric("Semantic Views", len(parsed_tools["semantic_views"]))
                    with col3:
                        st.metric("Semantic Model Files", len(
                            parsed_tools["semantic_model_files"]))
                    with col4:
                        st.metric("Semantic Model Stages", len(
                            parsed_tools["semantic_model_stages"]))
                    with col5:
                        st.metric("Search Services", len(parsed_tools["search_services"]))

                    # Display tools table
                    st.subheader("Tools Overview")
                    st.dataframe(parsed_tools["tools_df"], use_container_width=True)

                    # Process semantic views and semantic model files
                    table_permissions_results = {}
                    # Collect Cortex Search Services from YAML content
                    yaml_cortex_search_services = set()

                    if parsed_tools["semantic_views"]:
                        with st.spinner("Processing semantic views..."):
                            semantic_view_table_results, semantic_view_search_results = execute_semantic_view_queries(
                                session, parsed_tools["semantic_views"])
                            table_permissions_results.update(semantic_view_table_results)
                            # Collect Cortex Search Services from semantic views
                            for search_services in semantic_view_search_results.values():
                                yaml_cortex_search_services.update(search_services)

                    if parsed_tools["semantic_model_files"]:
                        with st.spinner("Processing semantic model files..."):
                            semantic_model_table_results, semantic_model_search_results = execute_semantic_model_file_queries(
                                session, parsed_tools["semantic_model_files"])
                            table_permissions_results.update(semantic_model_table_results)
                            # Collect Cortex Search Services from semantic model files
                            for search_services in semantic_model_search_results.values():
                                yaml_cortex_search_services.update(search_services)

                    # Generate permission script
                    with st.spinner("Generating permission script..."):
                        permission_script = generate_comprehensive_permission_script(
                            parsed_tools=parsed_tools,
                            table_permissions_results=table_permissions_results,
                            yaml_cortex_search_services=yaml_cortex_search_services,
                            warehouse_name="COMPUTE_WH"
                        )

                    # Display results
                    st.markdown(
                        '<div class="section-header">Generated Permission Script</div>', unsafe_allow_html=True)

                    # Calculate final database and schema counts including tables from semantic views
                    final_db_count = len(set(parsed_tools['databases']).union(
                        {db for tables in table_permissions_results.values()
                         for db, schema, table in tables}
                    ))
                    final_schema_count = len(set(parsed_tools['schemas']).union(
                        {f"{db}.{schema}" for tables in table_permissions_results.values()
                         for db, schema, table in tables}
                    ))

                    # Summary
                    st.info(f"""
                    **Agent**: {parsed_tools['agent_name']}  
                    **Location**: {parsed_tools['agent_database']}.{parsed_tools['agent_schema']}  
                    **Databases**: {final_db_count} (including tables from semantic views)  
                    **Schemas**: {final_schema_count} (including tables from semantic views)  
                    **Tables**: {sum(len(tables) for tables in table_permissions_results.values())}
                    """)

                    # Script display
                    st.code(permission_script, language="sql")

                    # Download button
                    st.download_button(
                        label="Download SQL Script",
                        data=permission_script,
                        file_name=f"{agent_name}_permissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                        mime="text/plain"
                    )

                    # Store in session state for potential reuse
                    st.session_state.last_permission_script = permission_script
                    st.session_state.last_parsed_tools = parsed_tools
    
    # ------------------------------------
    # Cortex Role Check
    # ------------------------------------
    elif tool_mode == "Cortex Role Check":
        st.header("Cortex Role Check")
        st.markdown("Check if a role can use a specific agent")
        
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
                        
                        # Check Cortex database role grants
                        with st.spinner("Checking Cortex access..."):
                            cortex_check = check_cortex_database_role_grants(session, selected_role)
                        
                        analysis = analyze_grants(grants_df, role_name=selected_role, cortex_check_result=cortex_check)
                        has_cortex = analysis['has_cortex']
                        has_warehouse = analysis['wh_count'] > 0
                        
                        # Display results
                        col1, col2, col3 = st.columns(3)
                        if has_agent_access:
                            col1.success("Agent Access")
                        else:
                            col1.error("No Agent Access")
                        
                        if has_cortex:
                            if analysis['cortex_method'] == 'explicit':
                                col2.success("Cortex Access (Direct)")
                            elif analysis['cortex_method'] == 'via_public':
                                col2.success("Cortex Access (via PUBLIC)")
                            elif analysis['cortex_method'] == 'via_hierarchy':
                                col2.success("Cortex Access (Inherited)")
                            else:
                                col2.success("Cortex Access")
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
                                # Use SMART permission comparison logic
                                with st.spinner("Analyzing role permissions and generating smart fix..."):
                                    parsed_tools = parse_agent_tools_with_sql(session, database, schema, agent_name)
                                    
                                    if not parsed_tools["tools_df"].empty:
                                        # Process semantic views and model files
                                        table_permissions_results = {}
                                        yaml_cortex_search_services = set()
                                        
                                        if parsed_tools["semantic_views"]:
                                            semantic_view_table_results, semantic_view_search_results = execute_semantic_view_queries(
                                                session, parsed_tools["semantic_views"])
                                            table_permissions_results.update(semantic_view_table_results)
                                            for search_services in semantic_view_search_results.values():
                                                yaml_cortex_search_services.update(search_services)
                                        
                                        if parsed_tools["semantic_model_files"]:
                                            semantic_model_table_results, semantic_model_search_results = execute_semantic_model_file_queries(
                                                session, parsed_tools["semantic_model_files"])
                                            table_permissions_results.update(semantic_model_table_results)
                                            for search_services in semantic_model_search_results.values():
                                                yaml_cortex_search_services.update(search_services)
                                        
                                        # Generate SMART permission script (only missing permissions)
                                        permission_script = generate_smart_permission_script(
                                            role_name=selected_role,
                                            grants_df=grants_df,
                                            parsed_tools=parsed_tools,
                                            table_permissions_results=table_permissions_results,
                                            yaml_cortex_search_services=yaml_cortex_search_services,
                                            warehouse_name="COMPUTE_WH"
                                        )
                                        
                                        st.code(permission_script, language="sql")
                                        
                                        # Check if role already has everything
                                        if "ALREADY HAS ALL REQUIRED PERMISSIONS" in permission_script:
                                            st.success("✅ This role already has all required permissions! No changes needed.")
                                        else:
                                            st.info("📝 The SQL above grants ONLY the missing permissions. Existing grants are preserved.")
                                        
                                        st.download_button(
                                            label="Download Fix SQL Script",
                                            data=permission_script,
                                            file_name=f"fix_{selected_role}_{agent_name}_permissions.sql",
                                            mime="text/plain",
                                            key=f"download_fix_{selected_role}"
                                        )
                                    else:
                                        # Fallback to simple grants if agent parsing fails
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
    **Snowflake Intelligence & Cortex Access Checker**
    
    Intelligent permission management for Cortex AI
    
    **Features:**
    - Agent permission generation
    - Role-agent compatibility check
    - Deep dependency analysis
    - Execute SQL directly
    """)
    st.sidebar.markdown("**Version:** 2.0.0")
    st.sidebar.caption("Built for Snowflake Cortex")

if __name__ == "__main__":
    main()
