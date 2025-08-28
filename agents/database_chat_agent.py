"""
Database Chat Agent
Specialized agent for Oracle database interactions via natural language
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from agents.agent_registry import BaseAgent
import re
import json

# Oracle database imports
try:
    import cx_Oracle
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False
    st.warning("cx_Oracle not available. Install it for full database functionality.")

class OracleConnector:
    """Oracle database connector class"""
    
    def __init__(self, host: str, user: str, password: str, port: int = 1521, service_name: str = ""):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.service_name = service_name
        self.connection = None
        
    def get_dsn(self) -> str:
        """Get Oracle connection DSN"""
        if self.service_name:
            return cx_Oracle.makedsn(self.host, self.port, service_name=self.service_name)
        else:
            return f"{self.host}:{self.port}"
    
    def test_connection(self) -> bool:
        """Test Oracle database connection"""
        if not ORACLE_AVAILABLE:
            return False
            
        try:
            dsn = self.get_dsn()
            connection = cx_Oracle.connect(self.user, self.password, dsn)
            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            return result[0] == 1
        except Exception as e:
            st.error(f"Connection test failed: {str(e)}")
            return False
    
    def connect(self) -> bool:
        """Establish Oracle connection"""
        if not ORACLE_AVAILABLE:
            return False
            
        try:
            dsn = self.get_dsn()
            self.connection = cx_Oracle.connect(self.user, self.password, dsn)
            return True
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
            return False
    
    def execute_query(self, query: str) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
        """Execute SQL query and return results"""
        if not self.connection:
            return False, None, "No active connection"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                df = pd.DataFrame(rows, columns=columns)
                cursor.close()
                return True, df, None
            else:
                # For non-SELECT queries
                self.connection.commit()
                cursor.close()
                return True, None, "Query executed successfully"
                
        except Exception as e:
            error_msg = f"Query execution error: {str(e)}"
            return False, None, error_msg
    
    def get_table_list(self) -> List[str]:
        """Get list of tables in the current schema"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM user_tables 
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return tables
        except Exception as e:
            st.error(f"Error getting table list: {str(e)}")
            return []
    
    def get_table_columns(self, table_name: str) -> pd.DataFrame:
        """Get column information for a table"""
        if not self.connection:
            return pd.DataFrame()
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT column_name, data_type, nullable, data_default
                FROM user_tab_columns 
                WHERE table_name = :table_name
                ORDER BY column_id
            """, table_name=table_name.upper())
            
            columns_data = cursor.fetchall()
            cursor.close()
            
            return pd.DataFrame(columns_data, 
                              columns=['Column', 'Data Type', 'Nullable', 'Default'])
        except Exception as e:
            st.error(f"Error getting table columns: {str(e)}")
            return pd.DataFrame()
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get row count for a table"""
        if not self.connection:
            return 0
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            st.error(f"Error getting row count: {str(e)}")
            return 0
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

class DatabaseChatAgent(BaseAgent):
    """Agent specialized in database interactions and SQL query generation"""
    
    def __init__(self, config):
        super().__init__(config)
        self.oracle_connector = None
        self.connection_status = "disconnected"
        self.query_history = []
    
    def run(self):
        """Main execution method for Database Chat Agent"""
        # Agent header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"## {self.config.icon} {self.config.name}")
            st.markdown(f"*{self.config.description}*")
        with col2:
            status_color = "🟢" if self.connection_status == "connected" else "🔴"
            st.markdown(f"**Status:** {status_color} {self.connection_status.title()}")
        
        # Create tabs for different functionalities
        tab1, tab2, tab3, tab4 = st.tabs([
            "💬 Database Chat", 
            "🔌 Connection Setup", 
            "📊 Schema Explorer", 
            "📈 Query History"
        ])
        
        with tab1:
            self.render_chat_interface()
        
        with tab2:
            self.render_connection_interface()
        
        with tab3:
            self.render_schema_explorer()
        
        with tab4:
            self.render_query_history()
    
    def render_chat_interface(self):
        """Render chat interface for database interactions"""
        st.subheader("Chat with Database")
        
        # Connection status indicator
        if self.connection_status == "connected":
            st.success("Connected to Oracle database")
        else:
            st.warning("Please configure database connection first")
            st.info("Go to the **Connection Setup** tab to configure your Oracle database connection.")
        
        # Chat history
        conversation = self.get_conversation_history()
        
        # Display recent messages
        for message in conversation[-10:]:
            with st.chat_message(message['role']):
                st.markdown(message['content'])
        
        # Chat input
        if prompt := st.chat_input("Ask about your database in natural language..."):
            # Add user message
            self.add_to_conversation('user', prompt)
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                if self.connection_status == "connected":
                    with st.spinner("Processing your database query..."):
                        response = self.process_input(prompt)
                else:
                    response = "I need to connect to a database first. Please configure the connection in the Connection Setup tab."
                
                st.markdown(response)
                self.add_to_conversation('assistant', response)
        
        # Quick query suggestions for connected databases
        if self.connection_status == "connected":
            st.markdown("### Quick Queries")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Show Tables", use_container_width=True):
                    response = self.execute_quick_query("show_tables")
                    self.add_to_conversation('user', 'Show all tables')
                    self.add_to_conversation('assistant', response)
                    st.rerun()
            
            with col2:
                if st.button("Table Sizes", use_container_width=True):
                    response = self.execute_quick_query("table_sizes")
                    self.add_to_conversation('user', 'Show table row counts')
                    self.add_to_conversation('assistant', response)
                    st.rerun()
            
            with col3:
                if st.button("Database Info", use_container_width=True):
                    response = self.execute_quick_query("db_info")
                    self.add_to_conversation('user', 'Show database information')
                    self.add_to_conversation('assistant', response)
                    st.rerun()
    
    def render_connection_interface(self):
        """Render database connection interface"""
        st.subheader("Oracle Database Connection")
        
        if not ORACLE_AVAILABLE:
            st.error("cx_Oracle package is not installed. Please install it to use Oracle database features.")
            st.code("pip install cx_Oracle")
            return
        
        # Connection form
        with st.form("oracle_connection"):
            st.markdown("### Connection Details")
            
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Host/Server", value="localhost", help="Database server hostname or IP")
                port = st.number_input("Port", value=1521, min_value=1, max_value=65535)
                service_name = st.text_input("Service Name", value="ORCL", help="Oracle service name")
            
            with col2:
                username = st.text_input("Username", help="Database username")
                password = st.text_input("Password", type="password", help="Database password")
                schema = st.text_input("Default Schema", value=username, help="Default schema to use")
            
            # Test and connect buttons
            col1, col2 = st.columns(2)
            with col1:
                test_connection = st.form_submit_button("Test Connection", type="secondary")
            with col2:
                connect_button = st.form_submit_button("Connect", type="primary")
            
            # Handle connection actions
            if test_connection and username and password:
                with st.spinner("Testing connection..."):
                    connector = OracleConnector(host, username, password, port, service_name)
                    if connector.test_connection():
                        st.success("Connection test successful!")
                    else:
                        st.error("Connection test failed. Please check your credentials.")
            
            if connect_button and username and password:
                with st.spinner("Connecting to database..."):
                    self.oracle_connector = OracleConnector(host, username, password, port, service_name)
                    if self.oracle_connector.connect():
                        self.connection_status = "connected"
                        st.success("Successfully connected to Oracle database!")
                        
                        # Store connection info in session
                        session_data = self.get_session_data()
                        session_data.update({
                            'host': host,
                            'username': username,
                            'service_name': service_name,
                            'connected_at': pd.Timestamp.now()
                        })
                        self.update_session_data(session_data)
                        
                        st.rerun()
                    else:
                        st.error("Failed to connect. Please check your credentials and network connectivity.")
        
        # Current connection info
        if self.connection_status == "connected":
            session_data = self.get_session_data()
            st.success("Database Connection Active")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"Host: {session_data.get('host', 'Unknown')}")
                st.info(f"User: {session_data.get('username', 'Unknown')}")
            with col2:
                st.info(f"Service: {session_data.get('service_name', 'Unknown')}")
                connected_time = session_data.get('connected_at')
                if connected_time:
                    st.info(f"Connected: {connected_time.strftime('%H:%M:%S')}")
            
            if st.button("Disconnect", type="secondary"):
                if self.oracle_connector:
                    self.oracle_connector.close()
                self.connection_status = "disconnected"
                self.oracle_connector = None
                st.rerun()
    
    def render_schema_explorer(self):
        """Render schema exploration interface"""
        st.subheader("Database Schema Explorer")
        
        if self.connection_status != "connected":
            st.warning("Connect to database first to explore schema.")
            return
        
        if not self.oracle_connector:
            st.error("No active database connection.")
            return
        
        # Get tables
        tables = self.oracle_connector.get_table_list()
        
        if not tables:
            st.info("No tables found in the current schema.")
            return
        
        # Schema overview
        st.markdown(f"**Found {len(tables)} tables in current schema**")
        
        # Table selector
        selected_table = st.selectbox("Select Table to Explore", [""] + tables)
        
        if selected_table:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"### Table: {selected_table}")
                
                # Get table structure
                columns_df = self.oracle_connector.get_table_columns(selected_table)
                if not columns_df.empty:
                    st.dataframe(columns_df, use_container_width=True)
            
            with col2:
                st.markdown("### Table Actions")
                
                # Row count
                row_count = self.oracle_connector.get_table_row_count(selected_table)
                st.metric("Total Rows", f"{row_count:,}")
                
                # Action buttons
                if st.button("Sample Data", use_container_width=True):
                    success, sample_data, error = self.oracle_connector.execute_query(
                        f"SELECT * FROM {selected_table} WHERE ROWNUM <= 10"
                    )
                    if success and sample_data is not None:
                        st.subheader("Sample Data (First 10 rows)")
                        st.dataframe(sample_data, use_container_width=True)
                    elif error:
                        st.error(f"Error: {error}")
                
                if st.button("Table Structure", use_container_width=True):
                    success, structure, error = self.oracle_connector.execute_query(f"DESCRIBE {selected_table}")
                    if success:
                        st.success("Table structure displayed above")
                    elif error:
                        st.error(f"Error: {error}")
    
    def render_query_history(self):
        """Render query history interface"""
        st.subheader("Query Execution History")
        
        if not self.query_history:
            st.info("No queries executed yet. Start a conversation to see query history.")
            return
        
        # Display query history
        for i, query_info in enumerate(reversed(self.query_history[-20:])):  # Show last 20
            with st.expander(f"Query {len(self.query_history) - i}: {query_info['timestamp']}", expanded=False):
                st.markdown(f"**Original Question:** {query_info['question']}")
                st.code(query_info['sql'], language='sql')
                
                if query_info['success']:
                    st.success("✅ Executed successfully")
                    if query_info.get('row_count'):
                        st.info(f"Returned {query_info['row_count']} rows")
                else:
                    st.error(f"❌ Error: {query_info['error']}")
        
        # Clear history button
        if st.button("Clear Query History", type="secondary"):
            self.query_history = []
            st.rerun()
    
    def process_input(self, user_input: str) -> str:
        """Process user input and generate database response"""
        if self.connection_status != "connected":
            return "I need to connect to a database first. Please configure the connection in the Connection Setup tab."
        
        # Generate SQL from natural language
        sql_query = self.natural_language_to_sql(user_input)
        
        if not sql_query:
            return "I couldn't convert that to a SQL query. Could you be more specific? For example: 'Show me all customers' or 'Count rows in the orders table'."
        
        # Execute the query
        success, results, error = self.oracle_connector.execute_query(sql_query)
        
        # Log query execution
        query_info = {
            'question': user_input,
            'sql': sql_query,
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'success': success,
            'error': error,
            'row_count': len(results) if results is not None else 0
        }
        self.query_history.append(query_info)
        
        if success:
            if results is not None and not results.empty:
                # Display results
                response = f"**Query executed successfully:**\n```sql\n{sql_query}\n```\n\n"
                response += f"**Results ({len(results)} rows):**"
                
                # Show results in Streamlit (this will display above the chat)
                st.dataframe(results, use_container_width=True)
                
                return response
            else:
                return f"**Query executed successfully:**\n```sql\n{sql_query}\n```\n\nQuery completed (no data returned)."
        else:
            return f"**Query failed:**\n```sql\n{sql_query}\n```\n\n**Error:** {error}"
    
    def natural_language_to_sql(self, user_input: str) -> Optional[str]:
        """Convert natural language to SQL query"""
        user_input_lower = user_input.lower()
        
        # Get available tables
        if not self.oracle_connector:
            return None
            
        tables = self.oracle_connector.get_table_list()
        
        # Basic patterns for SQL generation
        if any(word in user_input_lower for word in ['show', 'list', 'display']) and 'table' in user_input_lower:
            return "SELECT table_name FROM user_tables ORDER BY table_name"
        
        # Find table name in user input
        mentioned_table = None
        for table in tables:
            if table.lower() in user_input_lower:
                mentioned_table = table
                break
        
        if mentioned_table:
            if any(word in user_input_lower for word in ['count', 'how many', 'total']):
                return f"SELECT COUNT(*) as total_rows FROM {mentioned_table}"
            
            elif any(word in user_input_lower for word in ['show', 'display', 'list', 'all']):
                if any(word in user_input_lower for word in ['first', 'top', '10', 'sample']):
                    return f"SELECT * FROM {mentioned_table} WHERE ROWNUM <= 10"
                else:
                    return f"SELECT * FROM {mentioned_table}"
            
            elif 'describe' in user_input_lower or 'structure' in user_input_lower:
                return f"SELECT column_name, data_type, nullable FROM user_tab_columns WHERE table_name = '{mentioned_table}' ORDER BY column_id"
        
        # Generic queries
        if 'tables' in user_input_lower and any(word in user_input_lower for word in ['show', 'list']):
            return "SELECT table_name FROM user_tables ORDER BY table_name"
        
        # If we can't generate a query, return None
        return None
    
    def execute_quick_query(self, query_type: str) -> str:
        """Execute predefined quick queries"""
        if not self.oracle_connector:
            return "No database connection available."
        
        if query_type == "show_tables":
            success, results, error = self.oracle_connector.execute_query(
                "SELECT table_name FROM user_tables ORDER BY table_name"
            )
            if success and results is not None:
                table_list = '\n'.join([f"- {row[0]}" for _, row in results.iterrows()])
                return f"**Available tables:**\n{table_list}"
        
        elif query_type == "table_sizes":
            tables = self.oracle_connector.get_table_list()
            result = "**Table row counts:**\n"
            for table in tables[:10]:  # Show first 10 tables
                count = self.oracle_connector.get_table_row_count(table)
                result += f"- {table}: {count:,} rows\n"
            return result
        
        elif query_type == "db_info":
            success, results, error = self.oracle_connector.execute_query(
                "SELECT * FROM v$version WHERE ROWNUM = 1"
            )
            if success and results is not None:
                version_info = results.iloc[0, 0] if not results.empty else "Unknown"
                return f"**Database Information:**\nVersion: {version_info}"
        
        return "Query execution failed."
    
    def run(self):
        """Main execution method for Database Chat Agent"""
        self.render_header()
        self.render_capabilities()
        
        # Create tabs for different functionalities
        tab1, tab2, tab3, tab4 = st.tabs([
            "💬 Database Chat", 
            "🔌 Connection", 
            "📊 Schema Explorer", 
            "📈 Query History"
        ])
        
        with tab1:
            self.render_chat_interface()
        
        with tab2:
            self.render_connection_interface()
        
        with tab3:
            self.render_schema_explorer()
        
        with tab4:
            self.render_query_history()
    
    def render_chat_interface(self):
        """Render chat interface for database interactions"""
        st.subheader("Chat with Database")
        st.markdown("Ask questions about your data in natural language. I'll convert them to SQL and execute the queries.")
        
        # Connection status indicator
        status_color = "green" if self.connection_status == "connected" else "red"
        st.markdown(f"**Connection Status:** :{status_color}[{self.connection_status.upper()}]")
        
        if self.connection_status != "connected":
            st.warning("Please configure database connection in the Connection tab first.")
        
        # Render conversation history
        self.render_conversation()
        
        # Render chat input
        self.render_chat_input()
        
        # Quick query suggestions
        if self.connection_status == "connected":
            st.markdown("### Quick Query Suggestions")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Show all tables", key="show_tables"):
                    response = self.execute_quick_query("show_tables")
                    self.add_to_conversation('user', 'Show all tables')
                    self.add_to_conversation('agent', response)
                    st.rerun()
            
            with col2:
                if st.button("Table row counts", key="table_counts"):
                    response = self.execute_quick_query("table_counts")
                    self.add_to_conversation('user', 'Show table row counts')
                    self.add_to_conversation('agent', response)
                    st.rerun()
            
            with col3:
                if st.button("Recent data", key="recent_data"):
                    response = self.execute_quick_query("recent_data")
                    self.add_to_conversation('user', 'Show recent data')
                    self.add_to_conversation('agent', response)
                    st.rerun()
    
    def render_connection_interface(self):
        """Render database connection interface"""
        st.subheader("Database Connection Configuration")
        
        # Connection form
        with st.form("db_connection"):
            col1, col2 = st.columns(2)
            
            with col1:
                host = st.text_input("Host", value="localhost")
                port = st.number_input("Port", value=1521, min_value=1, max_value=65535)
                service_name = st.text_input("Service Name", value="ORCL")
            
            with col2:
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                schema = st.text_input("Default Schema", value=username)
            
            # Connection options
            st.subheader("Connection Options")
            col1, col2 = st.columns(2)
            
            with col1:
                use_ssl = st.checkbox("Use SSL", value=False)
                connection_timeout = st.number_input("Timeout (seconds)", value=30, min_value=5, max_value=300)
            
            with col2:
                pool_size = st.number_input("Connection Pool Size", value=5, min_value=1, max_value=20)
                auto_commit = st.checkbox("Auto Commit", value=False)
            
            submitted = st.form_submit_button("Connect to Database", type="primary")
            
            if submitted:
                if username and password:
                    with st.spinner("Connecting to database..."):
                        success = self.test_database_connection({
                            'host': host,
                            'port': port,
                            'service_name': service_name,
                            'username': username,
                            'password': password,
                            'schema': schema,
                            'use_ssl': use_ssl,
                            'timeout': connection_timeout,
                            'pool_size': pool_size,
                            'auto_commit': auto_commit
                        })
                        
                        if success:
                            st.success("Successfully connected to Oracle database!")
                            self.connection_status = "connected"
                            st.rerun()
                        else:
                            st.error("Failed to connect to database. Please check your credentials.")
                else:
                    st.error("Please provide username and password.")
        
        # Current connection status
        if self.connection_status == "connected":
            st.success("Database connection is active")
            
            if st.button("Disconnect", type="secondary"):
                self.connection_status = "disconnected"
                st.rerun()
        
        # Connection testing
        st.subheader("Connection Testing")
        if st.button("Test Connection", key="test_conn"):
            with st.spinner("Testing connection..."):
                if self.connection_status == "connected":
                    st.success("Connection is active and responding")
                else:
                    st.error("No active connection")
    
    def render_schema_explorer(self):
        """Render schema exploration interface"""
        st.subheader("Database Schema Explorer")
        
        if self.connection_status != "connected":
            st.warning("Connect to database first to explore schema.")
            return
        
        # Schema overview
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Tables", self.get_table_count())
        with col2:
            st.metric("Views", self.get_view_count())
        with col3:
            st.metric("Procedures", self.get_procedure_count())
        with col4:
            st.metric("Functions", self.get_function_count())
        
        # Table browser
        st.subheader("Table Browser")
        
        # Get table list
        tables = self.get_table_list()
        
        if tables:
            selected_table = st.selectbox("Select Table", [""] + tables)
            
            if selected_table:
                # Table details
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Table:** {selected_table}")
                    
                    # Get column information
                    columns_info = self.get_table_columns(selected_table)
                    if columns_info:
                        st.dataframe(columns_info)
                
                with col2:
                    st.write("**Actions**")
                    
                    if st.button("Sample Data", key=f"sample_{selected_table}"):
                        sample_data = self.get_sample_data(selected_table)
                        if sample_data is not None:
                            st.dataframe(sample_data)
                    
                    if st.button("Table Stats", key=f"stats_{selected_table}"):
                        stats = self.get_table_statistics(selected_table)
                        st.write(stats)
        else:
            st.info("No tables found in the current schema.")
    
    def render_query_history(self):
        """Render query history interface"""
        st.subheader("Query History")
        
        if not self.query_history:
            st.info("No queries executed yet.")
            return
        
        # Query history table
        history_df = pd.DataFrame(self.query_history)
        st.dataframe(history_df, use_container_width=True)
        
        # Query details
        if st.selectbox("Select Query to View Details", [""] + [f"Query {i+1}" for i in range(len(self.query_history))]):
            query_index = int(st.selectbox("Select Query to View Details", [""] + [f"Query {i+1}" for i in range(len(self.query_history))]).split()[-1]) - 1
            query_details = self.query_history[query_index]
            
            st.subheader("Query Details")
            st.code(query_details.get('sql', ''), language='sql')
            
            if query_details.get('results') is not None:
                st.subheader("Results")
                st.dataframe(query_details['results'])
    
    def process_input(self, user_input: str) -> str:
        """Process user input and generate appropriate response"""
        if self.connection_status != "connected":
            return "I need to connect to a database first. Please configure the connection in the Connection tab."
        
        user_input_lower = user_input.lower()
        
        # Intent detection
        if any(keyword in user_input_lower for keyword in ['show', 'list', 'display']):
            return self.handle_display_requests(user_input)
        elif any(keyword in user_input_lower for keyword in ['count', 'how many', 'total']):
            return self.handle_count_requests(user_input)
        elif any(keyword in user_input_lower for keyword in ['find', 'search', 'where', 'filter']):
            return self.handle_search_requests(user_input)
        elif any(keyword in user_input_lower for keyword in ['join', 'combine', 'merge']):
            return self.handle_join_requests(user_input)
        elif any(keyword in user_input_lower for keyword in ['average', 'sum', 'max', 'min', 'avg']):
            return self.handle_aggregation_requests(user_input)
        else:
            return self.handle_general_query(user_input)
    
    def handle_display_requests(self, user_input: str) -> str:
        """Handle requests to display/show data"""
        if 'tables' in user_input.lower():
            tables = self.get_table_list()
            if tables:
                return f"Available tables:\n" + "\n".join([f"- {table}" for table in tables])
            else:
                return "No tables found in the current schema."
        
        # Try to identify table name in the input
        table_name = self.extract_table_name(user_input)
        if table_name:
            sample_data = self.get_sample_data(table_name, limit=10)
            if sample_data is not None:
                return f"Here are the first 10 rows from {table_name}:\n\n{sample_data.to_string()}"
            else:
                return f"Could not retrieve data from table '{table_name}'. Please check if the table exists."
        
        return "I need more specific information. Which table would you like me to show?"
    
    def handle_count_requests(self, user_input: str) -> str:
        """Handle count/total requests"""
        table_name = self.extract_table_name(user_input)
        if table_name:
            count = self.get_table_row_count(table_name)
            if count is not None:
                return f"Table '{table_name}' contains {count:,} rows."
            else:
                return f"Could not get row count for table '{table_name}'."
        
        return "Please specify which table you'd like me to count."
    
    def handle_search_requests(self, user_input: str) -> str:
        """Handle search/filter requests"""
        # This would require more sophisticated NLP to parse conditions
        return "I can help with search queries. Please provide more details about what you're looking for and in which table."
    
    def handle_join_requests(self, user_input: str) -> str:
        """Handle join requests"""
        return "I can help create JOIN queries. Please specify which tables you'd like to combine and the relationship between them."
    
    def handle_aggregation_requests(self, user_input: str) -> str:
        """Handle aggregation requests (sum, count, average, etc.)"""
        return "I can help with aggregation queries (SUM, COUNT, AVG, MAX, MIN). Please specify the column and table you'd like to analyze."
    
    def handle_general_query(self, user_input: str) -> str:
        """Handle general database queries"""
        # This would use more sophisticated NLP to generate SQL
        sql_query = self.natural_language_to_sql(user_input)
        
        if sql_query:
            try:
                results = self.execute_sql_query(sql_query)
                if results is not None:
                    self.query_history.append({
                        'query': user_input,
                        'sql': sql_query,
                        'timestamp': pd.Timestamp.now(),
                        'results': results,
                        'status': 'success'
                    })
                    return f"Query executed successfully. Found {len(results)} rows.\n\nSQL: {sql_query}\n\nResults:\n{results.to_string()}"
                else:
                    return f"Query executed but returned no results.\n\nSQL: {sql_query}"
            except Exception as e:
                return f"Error executing query: {str(e)}\n\nSQL: {sql_query}"
        else:
            return "I couldn't convert that to a SQL query. Could you be more specific?"
    
    # Mock database methods (in real implementation, these would use actual database connections)
    def test_database_connection(self, config: Dict[str, Any]) -> bool:
        """Test database connection (mock implementation)"""
        # In real implementation, this would use cx_Oracle or similar
        return True  # Simulate successful connection
    
    def get_table_count(self) -> int:
        """Get number of tables (mock)"""
        return 15
    
    def get_view_count(self) -> int:
        """Get number of views (mock)"""
        return 8
    
    def get_procedure_count(self) -> int:
        """Get number of procedures (mock)"""
        return 12
    
    def get_function_count(self) -> int:
        """Get number of functions (mock)"""
        return 5
    
    def get_table_list(self) -> List[str]:
        """Get list of tables (mock)"""
        return ['CUSTOMERS', 'ORDERS', 'PRODUCTS', 'EMPLOYEES', 'DEPARTMENTS', 'SALES', 'INVENTORY']
    
    def get_table_columns(self, table_name: str) -> pd.DataFrame:
        """Get table column information (mock)"""
        # Mock column data
        mock_columns = {
            'CUSTOMERS': [
                {'Column': 'CUSTOMER_ID', 'Type': 'NUMBER', 'Nullable': 'NO', 'Primary Key': 'YES'},
                {'Column': 'CUSTOMER_NAME', 'Type': 'VARCHAR2(100)', 'Nullable': 'NO', 'Primary Key': 'NO'},
                {'Column': 'EMAIL', 'Type': 'VARCHAR2(255)', 'Nullable': 'YES', 'Primary Key': 'NO'},
                {'Column': 'CREATED_DATE', 'Type': 'DATE', 'Nullable': 'NO', 'Primary Key': 'NO'}
            ],
            'ORDERS': [
                {'Column': 'ORDER_ID', 'Type': 'NUMBER', 'Nullable': 'NO', 'Primary Key': 'YES'},
                {'Column': 'CUSTOMER_ID', 'Type': 'NUMBER', 'Nullable': 'NO', 'Primary Key': 'NO'},
                {'Column': 'ORDER_DATE', 'Type': 'DATE', 'Nullable': 'NO', 'Primary Key': 'NO'},
                {'Column': 'TOTAL_AMOUNT', 'Type': 'NUMBER(10,2)', 'Nullable': 'NO', 'Primary Key': 'NO'}
            ]
        }
        
        columns_data = mock_columns.get(table_name, [
            {'Column': 'ID', 'Type': 'NUMBER', 'Nullable': 'NO', 'Primary Key': 'YES'},
            {'Column': 'NAME', 'Type': 'VARCHAR2(100)', 'Nullable': 'NO', 'Primary Key': 'NO'}
        ])
        
        return pd.DataFrame(columns_data)
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Get sample data from table (mock)"""
        # Mock sample data
        mock_data = {
            'CUSTOMERS': pd.DataFrame({
                'CUSTOMER_ID': [1, 2, 3, 4, 5],
                'CUSTOMER_NAME': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson'],
                'EMAIL': ['john@email.com', 'jane@email.com', 'bob@email.com', 'alice@email.com', 'charlie@email.com'],
                'CREATED_DATE': pd.date_range('2023-01-01', periods=5)
            }),
            'ORDERS': pd.DataFrame({
                'ORDER_ID': [101, 102, 103, 104, 105],
                'CUSTOMER_ID': [1, 2, 1, 3, 2],
                'ORDER_DATE': pd.date_range('2023-06-01', periods=5),
                'TOTAL_AMOUNT': [250.00, 175.50, 320.75, 89.99, 445.25]
            })
        }
        
        if table_name in mock_data:
            return mock_data[table_name].head(limit)
        else:
            # Generic mock data
            return pd.DataFrame({
                'ID': range(1, limit + 1),
                'VALUE': [f'Sample {i}' for i in range(1, limit + 1)]
            })
    
    def get_table_statistics(self, table_name: str) -> str:
        """Get table statistics (mock)"""
        return f"""Table Statistics for {table_name}:
- Row Count: 1,247
- Last Updated: 2024-01-15
- Size: 2.5 MB
- Indexes: 3
- Constraints: 2"""
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get table row count (mock)"""
        mock_counts = {
            'CUSTOMERS': 1247,
            'ORDERS': 5638,
            'PRODUCTS': 892,
            'EMPLOYEES': 156,
            'DEPARTMENTS': 12
        }
        return mock_counts.get(table_name, 100)
    
    def extract_table_name(self, user_input: str) -> str:
        """Extract table name from user input"""
        # Simple pattern matching for table names
        tables = self.get_table_list()
        user_input_upper = user_input.upper()
        
        for table in tables:
            if table in user_input_upper:
                return table
        
        return None
    
    def natural_language_to_sql(self, user_input: str) -> str:
        """Convert natural language to SQL (simplified implementation)"""
        user_input_lower = user_input.lower()
        
        # Basic pattern matching for SQL generation
        if 'all' in user_input_lower and 'from' in user_input_lower:
            table_name = self.extract_table_name(user_input)
            if table_name:
                return f"SELECT * FROM {table_name}"
        
        elif 'count' in user_input_lower:
            table_name = self.extract_table_name(user_input)
            if table_name:
                return f"SELECT COUNT(*) FROM {table_name}"
        
        elif any(word in user_input_lower for word in ['top', 'first', 'limit']):
            table_name = self.extract_table_name(user_input)
            if table_name:
                # Extract number
                numbers = re.findall(r'\d+', user_input)
                limit = numbers[0] if numbers else '10'
                return f"SELECT * FROM {table_name} WHERE ROWNUM <= {limit}"
        
        # More sophisticated NLP would be implemented here
        return None
    
    def execute_sql_query(self, sql_query: str) -> pd.DataFrame:
        """Execute SQL query (mock implementation)"""
        # In real implementation, this would execute actual SQL
        # For now, return mock results based on query type
        
        if 'COUNT(*)' in sql_query.upper():
            return pd.DataFrame({'COUNT': [1247]})
        
        elif 'SELECT *' in sql_query.upper():
            table_name = None
            words = sql_query.upper().split()
            if 'FROM' in words:
                from_index = words.index('FROM')
                if from_index + 1 < len(words):
                    table_name = words[from_index + 1]
            
            if table_name:
                return self.get_sample_data(table_name, 10)
        
        # Default response
        return pd.DataFrame({'Result': ['Mock query executed successfully']})
    
    def execute_quick_query(self, query_type: str) -> str:
        """Execute predefined quick queries"""
        if query_type == "show_tables":
            tables = self.get_table_list()
            return f"Database contains {len(tables)} tables:\n" + "\n".join([f"• {table}" for table in tables])
        
        elif query_type == "table_counts":
            tables = self.get_table_list()
            result = "Table row counts:\n"
            for table in tables[:5]:  # Show first 5 tables
                count = self.get_table_row_count(table)
                result += f"• {table}: {count:,} rows\n"
            return result
        
        elif query_type == "recent_data":
            return "Most recent data updates:\n• ORDERS: 2024-01-15 14:30\n• CUSTOMERS: 2024-01-15 09:15\n• PRODUCTS: 2024-01-14 16:45"
        
        return "Query type not recognized."
            
