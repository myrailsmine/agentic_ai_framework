"""
Agent Framework Configuration
"""

import streamlit as st
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class AgentType(Enum):
    DOCUMENT_PROCESSOR = "document_processor"
    BRD_GENERATOR = "brd_generator"
    DATABASE_CHAT = "database_chat"
    DATA_ANALYST = "data_analyst"
    COMPLIANCE_CHECKER = "compliance_checker"

@dataclass
class AgentCapability:
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]

@dataclass
class AgentConfig:
    id: str
    name: str
    description: str
    type: AgentType
    capabilities: List[AgentCapability]
    icon: str
    color: str
    status: str = "active"
    version: str = "1.0.0"
    dependencies: List[str] = None
    configuration: Dict[str, Any] = None

@dataclass
class User:
    id: str
    name: str
    email: str
    role: str

@dataclass
class ConversationHistory:
    agent_id: str
    user_id: str
    messages: List[Dict[str, Any]]
    created_at: datetime
    last_updated: datetime

# Agent Configurations - Only BRD Generator and Database Chat Agents
AGENT_CONFIGS = {
    "brd_generator": AgentConfig(
        id="brd_generator",
        name="BRD Generator",
        description="Intelligent Business Requirements Document generation from regulatory documents with AI-powered analysis and mathematical formula extraction",
        type=AgentType.BRD_GENERATOR,
        capabilities=[
            AgentCapability(
                name="Document Analysis",
                description="Extract and analyze content from PDF, DOCX, and TXT files with advanced mathematical formula detection",
                input_types=["pdf", "docx", "txt"],
                output_types=["analysis", "formulas", "regulatory_insights"]
            ),
            AgentCapability(
                name="Regulatory Compliance",
                description="Detect and analyze regulatory frameworks like Basel III, SOX, GDPR with compliance assessment",
                input_types=["regulatory_documents"],
                output_types=["compliance_analysis", "framework_detection"]
            ),
            AgentCapability(
                name="BRD Generation",
                description="Generate comprehensive, audit-ready Business Requirements Documents with regulatory focus",
                input_types=["document_analysis", "requirements"],
                output_types=["brd_document", "quality_assessment"]
            ),
            AgentCapability(
                name="Export & Quality Control",
                description="Export BRDs in multiple formats with quality scoring and compliance verification",
                input_types=["brd_content"],
                output_types=["word", "pdf", "excel", "json", "quality_metrics"]
            )
        ],
        icon="📄",
        color="#667eea",
        dependencies=["langchain", "pymupdf", "python-docx", "reportlab"]
    ),
    
    "database_chat": AgentConfig(
        id="database_chat",
        name="Database Assistant",
        description="Natural language interface for Oracle database interactions with intelligent query generation and data analysis capabilities",
        type=AgentType.DATABASE_CHAT,
        capabilities=[
            AgentCapability(
                name="Natural Language to SQL",
                description="Convert natural language questions to optimized SQL queries with safety validation",
                input_types=["natural_language", "business_questions"],
                output_types=["sql_query", "query_explanation"]
            ),
            AgentCapability(
                name="Database Schema Intelligence",
                description="Analyze and understand database schemas, relationships, and data structures automatically",
                input_types=["connection_info"],
                output_types=["schema_analysis", "relationship_mapping", "data_dictionary"]
            ),
            AgentCapability(
                name="Data Analysis & Insights",
                description="Execute queries safely and provide intelligent insights with data visualization",
                input_types=["sql_queries", "data_requests"],
                output_types=["query_results", "data_insights", "visualizations"]
            ),
            AgentCapability(
                name="Query Optimization",
                description="Optimize query performance and provide database administration recommendations",
                input_types=["slow_queries", "performance_issues"],
                output_types=["optimized_queries", "performance_recommendations"]
            )
        ],
        icon="💾",
        color="#10B981",
        dependencies=["cx_oracle", "sqlalchemy", "pandas", "plotly"]
    )
}

def configure_app():
    """Configure Streamlit application for agent framework"""
    st.set_page_config(
        page_title="AI Agent Framework - BRD & Database Specialists",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for agent framework with modern dark theme
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
        
        .css-1d391kg {
            background-color: #2d2d2d;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        .agent-card {
            background: linear-gradient(135deg, #2d2d2d 0%, #3d3d3d 100%);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border-left: 4px solid var(--agent-color);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .agent-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.4);
            background: linear-gradient(135deg, #3d3d3d 0%, #4d4d4d 100%);
        }
        
        .agent-card.selected {
            border-left-color: #00d4ff;
            background: linear-gradient(135deg, #3d3d3d 0%, #4d4d4d 100%);
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        }
        
        .metric-card {
            background: linear-gradient(135deg, #2d2d2d 0%, #3d3d3d 100%);
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            border-left: 4px solid #00d4ff;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #00d4ff;
            margin: 0;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #888;
            margin: 0;
        }
        
        /* Chat interface improvements */
        .chat-message {
            background-color: #2d2d2d;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 3px solid #00d4ff;
        }
        
        /* Button improvements */
        .stButton > button {
            background: linear-gradient(135deg, #00d4ff 0%, #00a8cc 100%);
            color: #1a1a1a;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #00a8cc 0%, #008bb3 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 212, 255, 0.3);
        }
        
        /* Form styling */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            color: #ffffff;
            border-radius: 8px;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #00d4ff;
            box-shadow: 0 0 0 1px #00d4ff;
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
            background: linear-gradient(135deg, #00d4ff 0%, #00a8cc 100%);
            color: #1a1a1a;
        }
        
        /* Success/Error styling */
        .stSuccess {
            background-color: #1a4d3a;
            border-left: 4px solid #10b981;
        }
        
        .stError {
            background-color: #4d1a1a;
            border-left: 4px solid #ef4444;
        }
        
        .stWarning {
            background-color: #4d3a1a;
            border-left: 4px solid #f59e0b;
        }
        
        .stInfo {
            background-color: #1a3a4d;
            border-left: 4px solid #3b82f6;
        }
    </style>
    """, unsafe_allow_html=True)

def init_session_state():
    """Initialize session state for agent framework"""
    defaults = {
        'current_agent': None,
        'agent_history': {},
        'conversation_history': {},
        'user_profile': User('user1', 'Current User', 'user@company.com', 'Business Analyst'),
        'agent_configs': AGENT_CONFIGS,
        'active_conversations': {},
        'shared_context': {},
        'framework_initialized': True
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_agent_config(agent_id: str) -> Optional[AgentConfig]:
    """Get configuration for specific agent"""
    return AGENT_CONFIGS.get(agent_id)

def get_available_agents() -> Dict[str, AgentConfig]:
    """Get all available agent configurations"""
    return {aid: config for aid, config in AGENT_CONFIGS.items() if config.status == "active"}
