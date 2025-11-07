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
    page_title="Snowflake Intelligence & Cortex Access Checker",
    page_icon="🔒"
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
        # SQL query to parse agent tools using LATERAL FLATTEN
        combined_query = f"""
        WITH agent_describe AS (
            SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
        ),
        parsed AS (
            SELECT 
                tools_flat.VALUE:tool_spec:name::STRING AS TOOL_NAME,
                tools_flat.VALUE:tool_spec:type::STRING AS TOOL_TYPE,
                tools_flat.VALUE:tool_spec:description::STRING AS TOOL_DESCRIPTION,
                
                REGEXP_SUBSTR(
                    tools_flat.VALUE:tool_spec:description::STRING, 
                    'Database: (\\\\w+)', 1, 1, 'e', 1
                ) AS DB_FROM_DESC,
                REGEXP_SUBSTR(
                    tools_flat.VALUE:tool_spec:description::STRING, 
                    'Schema: (\\\\w+)', 1, 1, 'e', 1
                ) AS SCHEMA_FROM_DESC,

                COALESCE(
                    PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:identifier::STRING,
                    PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:semantic_view::STRING,
                    PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:search_service::STRING,
                    PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:name::STRING,
                    PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:semantic_model_file::STRING
                ) AS FULL_RESOURCE_PATH,
                
                PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:name::STRING AS PROCEDURE_NAME_WITH_TYPES,
                PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:search_service::STRING AS SEARCH_SERVICE_NAME,
                PARSE_JSON(desc_results."agent_spec"):tool_resources[TOOL_NAME]:semantic_model_file::STRING AS SEMANTIC_MODEL_FILE

            FROM 
                agent_describe AS desc_results,
                LATERAL FLATTEN(input => PARSE_JSON(desc_results."agent_spec"):tools) AS tools_flat
        )
        SELECT 
            TOOL_NAME,
            TOOL_TYPE,
            TOOL_DESCRIPTION,
            
            COALESCE(
                DB_FROM_DESC, 
                SPLIT_PART(FULL_RESOURCE_PATH, '.', 1)
            ) AS DATABASE_NAME,
            
            COALESCE(
                SCHEMA_FROM_DESC, 
                SPLIT_PART(FULL_RESOURCE_PATH, '.', 2)
            ) AS SCHEMA_NAME,
            
            SPLIT_PART(FULL_RESOURCE_PATH, '.', 3) AS OBJECT_NAME,
            FULL_RESOURCE_PATH,
            PROCEDURE_NAME_WITH_TYPES,
            SEARCH_SERVICE_NAME,
            SEMANTIC_MODEL_FILE
        FROM 
            parsed
        """

        # First execute DESCRIBE to populate RESULT_SCAN
        describe_query = f'DESCRIBE AGENT "{database}"."{schema}"."{agent_name}"'
        _session.sql(describe_query).collect()

        # Then execute the combined parsing query
        results = _session.sql(combined_query).collect()

        # Initialize collections
        semantic_views = set()
        semantic_model_files = set()
        search_services = set()
        procedures = set()
        databases = {database}
        schemas = {f"{database}.{schema}"}
        
        # Process each tool
        for row in results:
            tool_type = row['TOOL_TYPE']
            full_path = row['FULL_RESOURCE_PATH']
            semantic_file = row['SEMANTIC_MODEL_FILE']
            search_service = row['SEARCH_SERVICE_NAME']
            proc_name = row['PROCEDURE_NAME_WITH_TYPES']
            db_name = row['DATABASE_NAME']
            schema_name = row['SCHEMA_NAME']
            
            # Add database and schema
            if db_name:
                databases.add(db_name)
            if db_name and schema_name:
                schemas.add(f"{db_name}.{schema_name}")
            
            # Categorize by tool type
            if tool_type == 'cortex_analyst_text_to_sql':
                if semantic_file:
                    semantic_model_files.add(semantic_file)
                elif full_path:
                    semantic_views.add(full_path)
                    # Extract DB/schema from path
                    parts = full_path.split('.')
                    if len(parts) >= 2:
                        databases.add(parts[0])
                        schemas.add(f"{parts[0]}.{parts[1]}")
                        
            elif tool_type == 'cortex_search':
                service_path = search_service or full_path
                if service_path:
                    search_services.add(service_path)
                    parts = service_path.split('.')
                    if len(parts) >= 2:
                        databases.add(parts[0])
                        schemas.add(f"{parts[0]}.{parts[1]}")
                        
            elif tool_type == 'generic':
                if full_path:
                    parts = full_path.split('.')
                    if len(parts) >= 2:
                        proc_db = parts[0]
                        proc_schema = parts[1]
                        databases.add(proc_db)
                        schemas.add(f"{proc_db}.{proc_schema}")
                        
                        if proc_name:
                            procedure_sig = f"{proc_db}.{proc_schema}.{proc_name}"
                        else:
                            procedure_sig = full_path
                        procedures.add(procedure_sig)
        
        return {
            'semantic_views': list(semantic_views),
            'semantic_model_files': list(semantic_model_files),
            'search_services': list(search_services),
            'procedures': list(procedures),
            'databases': list(databases),
            'schemas': list(schemas)
        }
        
    except Exception as e:
        st.warning(f"SQL-based parsing failed, falling back to basic parsing: {e}")
        return {
            'semantic_views': [],
            'semantic_model_files': [],
            'search_services': [],
            'procedures': [],
            'databases': [database],
            'schemas': [f"{database}.{schema}"]
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

@st.cache_data(show_spinner="Reading semantic model file...", ttl=300)
def read_yaml_from_stage(_session, semantic_model_file: str):
    """Read YAML content from a Snowflake stage using regular table with AUTOINCREMENT."""
    try:
        db, schema, stage = extract_stage_info_from_semantic_model_file(semantic_model_file)
        
        if not all([db, schema, stage]):
            return None
        
        file_name = semantic_model_file.split('/')[-1]
        
        # Create a regular table (not temporary) with AUTOINCREMENT for ordering
        table_name = f"YAML_TEMP_{abs(hash(semantic_model_file)) % 10000}"
        
        try:
            # Create table with row number for ordering
            _session.sql(f"""
                CREATE OR REPLACE TABLE {table_name} (
                    row_num INTEGER AUTOINCREMENT,
                    line_content STRING
                )
            """).collect()
            
            # Copy file content
            _session.sql(f"""
                COPY INTO {table_name} (line_content)
                FROM @{db}.{schema}.{stage}/{file_name}
                FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = NONE FIELD_OPTIONALLY_ENCLOSED_BY = NONE)
                ON_ERROR = 'CONTINUE'
            """).collect()
            
            # Read content using ROW_NUMBER() for ordering
            result = _session.sql(f"""
                SELECT LISTAGG(line_content, '\\n') WITHIN GROUP (ORDER BY row_num) as file_content
                FROM {table_name}
                WHERE line_content IS NOT NULL
            """).collect()
            
            if result and result[0]['FILE_CONTENT']:
                import yaml
                yaml_content = yaml.safe_load(result[0]['FILE_CONTENT'])
                
                # Clean up
                _session.sql(f"DROP TABLE IF EXISTS {table_name}").collect()
                
                return yaml_content
            else:
                # Clean up
                _session.sql(f"DROP TABLE IF EXISTS {table_name}").collect()
                return None
                
        except Exception as e:
            # Clean up on error
            try:
                _session.sql(f"DROP TABLE IF EXISTS {table_name}").collect()
            except:
                pass
            raise e
        
    except Exception as e:
        st.warning(f"Could not read YAML from stage {semantic_model_file}: {e}")
        return None

def extract_tables_from_yaml(yaml_content):
    """Extract table references from YAML content (semantic view or semantic model)."""
    tables = []
    
    if not yaml_content:
        return tables
    
    # Method 1: semantic_model format
    if "semantic_model" in yaml_content:
        semantic_model = yaml_content["semantic_model"]
        if isinstance(semantic_model, dict) and "tables" in semantic_model:
            tables_data = semantic_model["tables"]
            if isinstance(tables_data, list):
                for table in tables_data:
                    if isinstance(table, dict):
                        db = table.get("database") or table.get("db")
                        schema = table.get("schema") or table.get("schema_name")
                        tbl = table.get("table") or table.get("table_name") or table.get("name")
                        
                        if db and schema and tbl:
                            tables.append(f"{db}.{schema}.{tbl}")
    
    # Method 2: Standard semantic view format
    elif "tables" in yaml_content:
        tables_data = yaml_content["tables"]
        if isinstance(tables_data, list):
            for table in tables_data:
                if isinstance(table, dict) and "base_table" in table:
                    base = table["base_table"]
                    db = base.get("database")
                    schema = base.get("schema")
                    tbl = base.get("table")
                    
                    if db and schema and tbl:
                        tables.append(f"{db}.{schema}.{tbl}")
    
    # Method 3: Recursive search
    def find_tables(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.lower() in ['table', 'base_table', 'source_table'] and isinstance(value, dict):
                    db = value.get("database") or value.get("db")
                    schema = value.get("schema") or value.get("schema_name")
                    tbl = value.get("table") or value.get("table_name") or value.get("name")
                    
                    if db and schema and tbl:
                        tables.append(f"{db}.{schema}.{tbl}")
                elif isinstance(value, (dict, list)):
                    find_tables(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    find_tables(item)
    
    find_tables(yaml_content)
    
    # Remove duplicates
    return list(set(tables))

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
            Snowflake Intelligence & Cortex Access Checker
        </h1>
        <p style='font-size: 1.2rem; color: #888; margin-bottom: 0.5rem;'>
            Intelligent Permission Management for Cortex AI Agents
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Role Analysis")
        st.markdown("Validate role permissions for Cortex readiness")
    with col2:
        st.markdown("### Auto-Generate SQL")
        st.markdown("Create least-privilege scripts instantly")
    with col3:
        st.markdown("### Deep Scanning")
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
                                                
                                                st.success(f"✅ Remediation executed successfully! ({statement_count} statements)")
                                                
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
                                                st.error(f"❌ Error executing SQL: {str(e)}")
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
            if agent_name and database and schema:
                # Use enhanced SQL-based parsing
                with st.spinner("Parsing agent with SQL..."):
                    parsed_resources = parse_agent_tools_with_sql(session, database, schema, agent_name)
                
                if parsed_resources and (parsed_resources['semantic_views'] or parsed_resources['semantic_model_files'] or parsed_resources['search_services'] or parsed_resources['procedures']):
                    # Extract what we found
                    semantic_views = parsed_resources['semantic_views']
                    semantic_model_files = parsed_resources['semantic_model_files']
                    search_services = parsed_resources['search_services']
                    procedures = parsed_resources['procedures']
                    # Convert lists to sets for efficient adding
                    databases = set(parsed_resources['databases'])
                    schemas = set(parsed_resources['schemas'])
                    
                    # Process semantic views and semantic model files to get base tables
                    all_tables = []
                    semantic_views_data = []
                    semantic_model_stages = set()
                    
                    # Process semantic views
                    if semantic_views:
                        st.write(f"Processing {len(semantic_views)} semantic views...")
                        for view_name in semantic_views:
                            yaml_content_str = get_semantic_view_yaml(session, view_name)
                            # Parse YAML string to dictionary
                            yaml_content = None
                            if yaml_content_str:
                                try:
                                    import yaml
                                    yaml_content = yaml.safe_load(yaml_content_str)
                                except:
                                    pass
                            tables = extract_tables_from_yaml(yaml_content) if yaml_content else []
                            
                            if tables:
                                all_tables.extend(tables)
                                st.success(f"[OK] {view_name}: Found {len(tables)} tables")
                            
                            semantic_views_data.append({
                                'view': view_name,
                                'yaml': yaml_content,
                                'tables': tables
                            })
                    
                    # Process semantic model files from stages
                    if semantic_model_files:
                        st.write(f"Processing {len(semantic_model_files)} semantic model files...")
                        for model_file in semantic_model_files:
                            # Extract stage info for permissions
                            db, sch, stage = extract_stage_info_from_semantic_model_file(model_file)
                            if db and sch and stage:
                                semantic_model_stages.add(f"{db}.{sch}.{stage}")
                                databases.add(db)
                                schemas.add(f"{db}.{sch}")
                            
                            # Read and parse YAML
                            yaml_content = read_yaml_from_stage(session, model_file)
                            tables = extract_tables_from_yaml(yaml_content) if yaml_content else []
                            
                            if tables:
                                all_tables.extend(tables)
                                st.success(f"[OK] {model_file}: Found {len(tables)} tables")
                            
                            semantic_views_data.append({
                                'view': model_file,
                                'yaml': yaml_content,
                                'tables': tables
                            })
                    
                    # Add databases and schemas from discovered tables
                    for table in all_tables:
                        parts = table.split('.')
                        if len(parts) >= 2:
                            databases.add(parts[0])
                            schemas.add(f"{parts[0]}.{parts[1]}")
                    
                    # Display parsed information
                    st.markdown("---")
                    st.markdown("### Discovered Resources")
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("Semantic Views", len(semantic_views))
                    col2.metric("Model Files", len(semantic_model_files))
                    col3.metric("Search Services", len(search_services))
                    col4.metric("Procedures", len(procedures))
                    col5.metric("Base Tables", len(set(all_tables)))
                    
                    # Show details
                    if semantic_views:
                        with st.expander("Semantic Views"):
                            for view in semantic_views:
                                st.write(f"- {view}")
                    
                    if semantic_model_files:
                        with st.expander("Semantic Model Files"):
                            for file in semantic_model_files:
                                st.write(f"- {file}")
                    
                    if search_services:
                        with st.expander("Search Services"):
                            for service in search_services:
                                st.write(f"- {service}")
                    
                    if procedures:
                        with st.expander("Procedures"):
                            for proc in procedures:
                                st.write(f"- {proc}")
                    
                    if all_tables:
                        with st.expander(f"Base Tables ({len(set(all_tables))})"):
                            for table in sorted(set(all_tables)):
                                st.write(f"- {table}")
                    
                    # Generate comprehensive SQL script
                    st.markdown("---")
                    st.markdown("### Generated Permission Script")
                    
                    # Build comprehensive semantic_views_data structure
                    comprehensive_views_data = []
                    for view_data in semantic_views_data:
                        comprehensive_views_data.append({
                            'view': view_data['view'],
                            'tables': view_data['tables']
                        })
                    
                    # Create tools structure for SQL generation
                    tools_for_sql = []
                    for view in semantic_views:
                        tools_for_sql.append({'type': 'cortex_analyst_text_to_sql', 'semantic_model': view})
                    for service in search_services:
                        tools_for_sql.append({'type': 'cortex_search', 'search_service': service})
                    for proc in procedures:
                        tools_for_sql.append({'type': 'generic', 'procedure': proc})
                    
                    # Generate SQL
                    sql_script = generate_agent_permission_sql(
                        agent_name=agent_name,
                        database=database,
                        schema=schema,
                        tools=tools_for_sql,
                        semantic_views_data=comprehensive_views_data,
                        role_name=f"{agent_name}_USER_ROLE"
                    )
                    
                    # Add stage permissions if needed
                    if semantic_model_stages:
                        stage_grants = "\n".join([
                            f"GRANT READ ON STAGE {stage} TO ROLE IDENTIFIER($AGENT_ROLE_NAME);"
                            for stage in sorted(semantic_model_stages)
                        ])
                        # Insert stage grants before warehouse permission
                        sql_script = sql_script.replace(
                            "-- Warehouse permission",
                            f"-- Stage permissions for semantic model files\n{stage_grants}\n\n-- Warehouse permission"
                        )
                    
                    # Summary
                    st.info(f"""
**Agent:** {agent_name}  
**Location:** {database}.{schema}  
**Databases:** {len(databases)}  
**Schemas:** {len(schemas)}  
**Semantic Views:** {len(semantic_views)}  
**Semantic Model Files:** {len(semantic_model_files)}  
**Base Tables:** {len(set(all_tables))}  
**Search Services:** {len(search_services)}  
**Procedures:** {len(procedures)}
                    """)
                    
                    # Display SQL
                    st.code(sql_script, language="sql")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        st.download_button(
                            label="Download SQL Script",
                            data=sql_script,
                            file_name=f"{agent_name}_permissions.sql",
                            mime="text/plain",
                            use_container_width=True
                        )
                    with col2:
                        exec_key = f"exec_agent_{agent_name}"
                        if st.button("Execute SQL", key=f"btn_{exec_key}", type="primary", use_container_width=True):
                            st.session_state[exec_key] = True
                    with col3:
                        if st.button("Help", use_container_width=True, type="secondary"):
                            st.info("**To execute SQL:**\n\n1. Review the generated SQL above\n2. Click 'Execute SQL' to run directly\n3. Or download and run in SQL Worksheet\n\n**Note:** Requires SECURITYADMIN or higher privileges")
                    
                    st.caption("Note: Review and adjust variables before executing")
                    
                    # Show execution results below buttons (prevents scroll to top)
                    if st.session_state.get(exec_key, False):
                        with st.spinner("Executing SQL script..."):
                            try:
                                # Count statements for feedback
                                statement_count = len([s for s in sql_script.split(';') if s.strip() and not s.strip().startswith('--')])
                                
                                # Execute the entire script as a multi-statement SQL
                                # This preserves variable context (SET statements work)
                                result = session.sql(sql_script).collect()
                                
                                st.success(f"✅ SQL script executed successfully! ({statement_count} statements)")
                                
                                # Show what was created/granted
                                st.markdown("**Actions completed:**")
                                st.markdown(f"- ✓ Role created: `{agent_name}_USER_ROLE`")
                                st.markdown(f"- ✓ Agent usage granted: `{database}.{schema}.{agent_name}`")
                                if semantic_views:
                                    st.markdown(f"- ✓ Semantic view permissions: {len(semantic_views)} views")
                                if all_tables:
                                    st.markdown(f"- ✓ Base table permissions: {len(set(all_tables))} tables")
                                if search_services:
                                    st.markdown(f"- ✓ Search service permissions: {len(search_services)} services")
                                if procedures:
                                    st.markdown(f"- ✓ Procedure permissions: {len(procedures)} procedures")
                                st.markdown(f"- ✓ Database/Schema usage: {len(databases)} databases, {len(schemas)} schemas")
                                st.markdown(f"- ✓ Warehouse usage granted")
                                
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
                                st.error(f"❌ Error executing SQL: {str(e)}")
                                st.info("**Common issues:**\n- Need SECURITYADMIN or ACCOUNTADMIN role\n- Some objects may already exist\n- Insufficient privileges on databases/schemas")
                                with st.expander("View Error Details"):
                                    st.code(str(e))
                                st.session_state[exec_key] = False
                else:
                    st.error("No tools found for this agent or agent does not exist")
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
    **Snowflake Intelligence & Cortex Access Checker**
    
    Intelligent permission management for Cortex AI
    
    **Features:**
    - Role readiness validation
    - Least-privilege SQL generation
    - Deep dependency analysis
    - Compatibility checking
    """)
    st.sidebar.markdown("**Version:** 2.0.0")
    st.sidebar.caption("Built for Snowflake Cortex")

if __name__ == "__main__":
    main()
