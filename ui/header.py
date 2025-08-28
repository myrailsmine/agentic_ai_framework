"""
Framework Header Component
"""

import streamlit as st

def render_framework_header():
    """Render main framework header"""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Agent Framework</h1>
        <p>Multi-Agent Business Intelligence Platform with specialized AI agents for document processing, database interactions, and business analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Framework status and metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Agents", "2")
    
    with col2:
        st.metric("Total Sessions", len(st.session_state.get('agent_history', {})))
    
    with col3:
        current_agent = st.session_state.get('current_agent')
        if current_agent:
            st.metric("Current Agent", current_agent.config.name)
        else:
            st.metric("Current Agent", "None")
    
    with col4:
        user_profile = st.session_state.get('user_profile')
        if user_profile:
            st.metric("User", user_profile.name)
        else:
            st.metric("User", "Guest")
