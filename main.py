"""
AI Agent Framework - Main Application
Integrated modern chat interface with specialized agents
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Optional
import sys
import os

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.agent_config import configure_app, init_session_state, AGENT_CONFIGS
from agents.brd_generator_agent import BRDGeneratorAgent
from agents.database_chat_agent import DatabaseChatAgent
from utils.logger import setup_logger

# Configure the app
configure_app()

# Custom CSS for modern dark theme
st.markdown("""
<style>
    /* Global dark theme */
    .main {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    .stApp {
        background-color: #1a1a1a;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #2d2d2d;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Agent selection styling */
    .agent-card {
        background-color: #2d2d2d;
        border: 1px solid #3d3d3d;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .agent-card:hover {
        background-color: #3d3d3d;
        border-color: #4d4d4d;
        transform: translateY(-2px);
    }
    
    .agent-card.selected {
        background-color: #3d3d3d;
        border-color: #00d4ff;
        border-width: 2px;
    }
    
    .agent-header {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }
    
    .agent-icon {
        font-size: 24px;
        margin-right: 12px;
    }
    
    .agent-name {
        font-size: 16px;
        font-weight: 600;
        color: #ffffff;
        margin: 0;
    }
    
    .agent-description {
        font-size: 14px;
        color: #888;
        margin: 0;
        line-height: 1.4;
    }
    
    .agent-status {
        margin-left: auto;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .status-active {
        background-color: #10b981;
        color: white;
    }
    
    .status-inactive {
        background-color: #6b7280;
        color: white;
    }
    
    /* Chat interface styling */
    .welcome-screen {
        text-align: center;
        padding: 80px 40px;
    }
    
    .welcome-icon {
        font-size: 64px;
        margin-bottom: 24px;
        opacity: 0.6;
    }
    
    .welcome-title {
        font-size: 32px;
        font-weight: 300;
        color: #ffffff;
        margin: 0 0 16px 0;
    }
    
    .welcome-subtitle {
        font-size: 16px;
        color: #888;
        margin: 0 0 32px 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #2d2d2d;
        border-radius: 8px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #888;
        border-radius: 6px;
        padding: 8px 16px;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #00d4ff;
        color: #1a1a1a;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #2d2d2d;
        border: 1px solid #3d3d3d;
        color: #ffffff;
        border-radius: 8px;
        padding: 8px 16px;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #3d3d3d;
        border-color: #4d4d4d;
    }
    
    /* Form styling */
    .stTextInput > div > div > input {
        background-color: #2d2d2d;
        border: 1px solid #3d3d3d;
        color: #ffffff;
        border-radius: 8px;
    }
    
    .stTextArea > div > div > textarea {
        background-color: #2d2d2d;
        border: 1px solid #3d3d3d;
        color: #ffffff;
        border-radius: 8px;
    }
    
    .stSelectbox > div > div > div {
        background-color: #2d2d2d;
        border: 1px solid #3d3d3d;
        color: #ffffff;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

class AgentManager:
    def __init__(self):
        self.agents = {}
        self.load_agents()
    
    def load_agents(self):
        """Load available agents"""
        try:
            # Load BRD Generator Agent
            if 'brd_generator' in AGENT_CONFIGS:
                self.agents['brd_generator'] = BRDGeneratorAgent(AGENT_CONFIGS['brd_generator'])
            
            # Load Database Chat Agent
            if 'database_chat' in AGENT_CONFIGS:
                self.agents['database_chat'] = DatabaseChatAgent(AGENT_CONFIGS['database_chat'])
                
            logger = setup_logger()
            logger.info(f"Loaded {len(self.agents)} agents")
            
        except Exception as e:
            st.error(f"Error loading agents: {e}")
    
    def get_agent(self, agent_id: str):
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> Dict[str, Dict]:
        """List all available agents"""
        return {
            agent_id: {
                'name': agent.config.name,
                'description': agent.config.description,
                'icon': agent.config.icon,
                'color': agent.config.color,
                'status': agent.config.status
            }
            for agent_id, agent in self.agents.items()
        }

def render_sidebar():
    """Render the sidebar with agent selection"""
    with st.sidebar:
        st.markdown("### AI Agent Framework")
        
        # New chat button
        if st.button("New Chat", key="new_chat", use_container_width=True):
            # Clear all agent sessions
            keys_to_remove = [key for key in st.session_state.keys() 
                            if key.startswith('agent_') or key.startswith('conversation_')]
            for key in keys_to_remove:
                del st.session_state[key]
            st.session_state.selected_agent = None
            st.rerun()
        
        st.markdown("---")
        
        # Agent selection
        st.markdown("### Available Agents")
        
        agent_manager = st.session_state.get('agent_manager')
        if not agent_manager:
            st.error("Agent manager not initialized")
            return None
        
        agents = agent_manager.list_agents()
        selected_agent_id = st.session_state.get('selected_agent')
        
        for agent_id, agent_info in agents.items():
            # Create agent card
            is_selected = selected_agent_id == agent_id
            card_class = "agent-card selected" if is_selected else "agent-card"
            
            # Agent selection button
            if st.button(
                f"{agent_info['icon']} {agent_info['name']}", 
                key=f"select_{agent_id}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state.selected_agent = agent_id
                st.rerun()
            
            # Show agent description
            st.caption(agent_info['description'])
            st.markdown("---")
        
        # Agent management
        st.markdown("### Agent Management")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Reset All", key="reset_all"):
                st.session_state.clear()
                init_session_state()
                st.rerun()
        
        with col2:
            if st.button("Refresh", key="refresh"):
                st.session_state.agent_manager = AgentManager()
                st.rerun()
        
        return selected_agent_id

def render_welcome_screen():
    """Render welcome screen when no agent is selected"""
    st.markdown('''
    <div class="welcome-screen">
        <div class="welcome-icon">🤖</div>
        <h1 class="welcome-title">AI Agent Framework</h1>
        <p class="welcome-subtitle">Select a specialized agent to begin your session</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Show agent previews
    st.markdown("### Available Agents")
    
    agent_manager = st.session_state.get('agent_manager')
    if agent_manager:
        agents = agent_manager.list_agents()
        
        cols = st.columns(len(agents))
        for idx, (agent_id, agent_info) in enumerate(agents.items()):
            with cols[idx]:
                st.markdown(f"""
                **{agent_info['icon']} {agent_info['name']}**
                
                {agent_info['description']}
                
                Status: {agent_info['status'].title()}
                """)
                
                if st.button(f"Select {agent_info['name']}", key=f"preview_{agent_id}"):
                    st.session_state.selected_agent = agent_id
                    st.rerun()

def main():
    """Main application function"""
    try:
        # Initialize session state
        init_session_state()
        
        # Initialize agent manager
        if 'agent_manager' not in st.session_state:
            st.session_state.agent_manager = AgentManager()
        
        # Render sidebar and get selected agent
        selected_agent_id = render_sidebar()
        
        # Main content area
        if selected_agent_id:
            agent_manager = st.session_state.agent_manager
            selected_agent = agent_manager.get_agent(selected_agent_id)
            
            if selected_agent:
                # Store current agent
                st.session_state.current_agent = selected_agent
                
                # Run the selected agent
                selected_agent.run()
            else:
                st.error(f"Agent '{selected_agent_id}' not found")
        else:
            # Show welcome screen
            render_welcome_screen()
    
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.error("Please refresh the page and try again.")

if __name__ == "__main__":
    main()
