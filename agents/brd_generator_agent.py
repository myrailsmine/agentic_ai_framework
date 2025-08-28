"""
Enhanced BRD Generator Agent
Specialized agent for Business Requirements Document generation with modern chat interface
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from datetime import datetime
from agents.agent_registry import BaseAgent
from utils.document_processor import process_document, render_content_with_images
from utils.ai_processor import generate_enhanced_brd
from utils.export_utils import export_to_word_docx, export_to_pdf, export_to_excel, export_to_json

class BRDGeneratorAgent(BaseAgent):
    """Enhanced BRD Generator Agent with integrated chat and modern interface"""
    
    def run(self):
        """Main execution method with integrated chat interface"""
        # Agent header with status
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"## {self.config.icon} {self.config.name}")
            st.markdown(f"*{self.config.description}*")
        with col2:
            status_color = "🟢" if self.config.status == "active" else "🔴"
            st.markdown(f"**Status:** {status_color} {self.config.status.title()}")
        
        # Main interface with tabs for different functions
        tab1, tab2, tab3 = st.tabs(["💬 Chat & Analysis", "🚀 Document Processing", "📊 Results & Export"])
        
        with tab1:
            self.render_chat_interface()
        
        with tab2:
            self.render_document_processing()
        
        with tab3:
            self.render_results_export()
    
    def render_chat_interface(self):
        """Enhanced chat interface with document context"""
        st.subheader("Chat with BRD Generator")
        
        # Show document status if available
        session_data = self.get_session_data()
        if session_data.get('document_name'):
            st.info(f"📄 Working with: **{session_data['document_name']}**")
            
            # Quick document insights
            if session_data.get('document_analysis'):
                analysis = session_data['document_analysis']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Document Type", analysis.get('document_type', 'Unknown'))
                with col2:
                    st.metric("Formulas Found", len(session_data.get('extracted_formulas', [])))
                with col3:
                    st.metric("Math Complexity", analysis.get('mathematical_complexity', 'Unknown'))
        
        # Chat history
        conversation = self.get_conversation_history()
        
        # Display recent messages
        for message in conversation[-10:]:  # Show last 10 messages
            with st.chat_message(message['role']):
                st.markdown(message['content'])
        
        # Chat input
        if prompt := st.chat_input("Ask about BRD generation, document analysis, or regulatory compliance..."):
            # Add user message
            self.add_to_conversation('user', prompt)
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your request..."):
                    response = self.process_input(prompt)
                st.markdown(response)
                self.add_to_conversation('assistant', response)
        
        # Quick action buttons
        if len(conversation) == 0:  # Show only for new conversations
            st.markdown("### Quick Start")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Explain BRD Process", type="secondary", use_container_width=True):
                    response = self.explain_brd_process()
                    self.add_to_conversation('user', 'Explain the BRD generation process')
                    self.add_to_conversation('assistant', response)
                    st.rerun()
            
            with col2:
                if st.button("Regulatory Frameworks", type="secondary", use_container_width=True):
                    response = self.explain_regulatory_frameworks()
                    self.add_to_conversation('user', 'What regulatory frameworks do you support?')
                    self.add_to_conversation('assistant', response)
                    st.rerun()
            
            with col3:
                if st.button("Upload Document", type="secondary", use_container_width=True):
                    st.info("Go to the 'Document Processing' tab to upload and analyze your regulatory documents.")
    
    def render_document_processing(self):
        """Document upload and processing interface"""
        st.subheader("Document Analysis & Processing")
        
        # File upload section
        uploaded_file = st.file_uploader(
            "Upload Regulatory Document",
            type=['pdf', 'docx', 'txt'],
            help="Upload Basel documents, regulatory frameworks, or compliance documents for analysis"
        )
        
        if uploaded_file:
            # Processing options
            with st.expander("Analysis Options", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    extract_images = st.checkbox("Extract Images", value=True)
                    extract_formulas = st.checkbox("Extract Mathematical Formulas", value=True)
                
                with col2:
                    regulatory_focus = st.checkbox("Regulatory Framework Detection", value=True)
                    advanced_analysis = st.checkbox("Advanced Intelligence Analysis", value=True)
            
            # Process document button
            if st.button("Analyze Document", type="primary", use_container_width=True):
                with st.spinner("Processing document with AI analysis..."):
                    try:
                        document_text, extracted_images, extracted_formulas, document_analysis = process_document(
                            uploaded_file, extract_images, extract_formulas
                        )
                        
                        # Store results in session
                        session_data = self.get_session_data()
                        session_data.update({
                            'document_text': document_text,
                            'extracted_images': extracted_images,
                            'extracted_formulas': extracted_formulas,
                            'document_analysis': document_analysis,
                            'document_name': uploaded_file.name,
                            'processed_at': datetime.now()
                        })
                        self.update_session_data(session_data)
                        
                        st.success("Document analysis completed successfully!")
                        
                        # Add to conversation
                        self.add_to_conversation('system', f"Processed document: {uploaded_file.name}")
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error processing document: {str(e)}")
        
        # Show analysis results if available
        session_data = self.get_session_data()
        if session_data.get('document_analysis'):
            self.display_document_analysis(session_data)
    
    def render_results_export(self):
        """Results display and export interface"""
        st.subheader("BRD Generation & Export")
        
        session_data = self.get_session_data()
        
        if not session_data.get('document_text'):
            st.warning("Please process a document first in the 'Document Processing' tab.")
            return
        
        # BRD generation section
        if not session_data.get('brd_content'):
            st.markdown("### Generate BRD")
            
            # Generation options
            col1, col2 = st.columns(2)
            with col1:
                template_type = st.selectbox(
                    "BRD Template",
                    ["Regulatory Compliance", "Standard Enterprise", "Technical Integration"]
                )
                quality_level = st.selectbox(
                    "Quality Level", 
                    ["Enterprise", "Premium", "Standard"]
                )
            
            with col2:
                compliance_focus = st.selectbox(
                    "Compliance Focus",
                    ["Basel III", "SOX", "GDPR", "General Regulatory"]
                )
                include_formulas = st.checkbox("Include Mathematical Analysis", value=True)
            
            # Generate BRD button
            if st.button("Generate Comprehensive BRD", type="primary", use_container_width=True):
                with st.spinner("Generating comprehensive BRD with AI intelligence..."):
                    try:
                        result = generate_enhanced_brd(
                            session_data['document_text'],
                            session_data.get('extracted_images', {}),
                            session_data.get('extracted_formulas', []),
                            session_data['document_analysis']
                        )
                        
                        # Store results
                        session_data.update({
                            'brd_content': result['brd_content'],
                            'quality_scores': result['quality_scores'],
                            'compliance_checks': result['compliance_checks'],
                            'generated_at': datetime.now(),
                            'template_type': template_type,
                            'quality_level': quality_level,
                            'compliance_focus': compliance_focus
                        })
                        self.update_session_data(session_data)
                        
                        st.success("BRD generated successfully!")
                        st.balloons()
                        
                        # Add to conversation
                        self.add_to_conversation('system', 'Generated comprehensive BRD document')
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error generating BRD: {str(e)}")
        
        # Display BRD results and export options
        if session_data.get('brd_content'):
            self.display_brd_results(session_data)
    
    def display_document_analysis(self, session_data: Dict[str, Any]):
        """Display document analysis results"""
        st.markdown("### Analysis Results")
        
        analysis = session_data['document_analysis']
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Document Type", analysis.get('document_type', 'Unknown'))
        with col2:
            st.metric("Math Complexity", analysis.get('mathematical_complexity', 'Unknown'))
        with col3:
            st.metric("Formulas", len(session_data.get('extracted_formulas', [])))
        with col4:
            st.metric("Frameworks", len(analysis.get('regulatory_framework', [])))
        
        # Detected frameworks
        if analysis.get('regulatory_framework'):
            st.markdown("**Detected Regulatory Frameworks:**")
            for framework in analysis['regulatory_framework']:
                st.markdown(f"- {framework.upper()}")
        
        # Formula analysis
        if session_data.get('extracted_formulas'):
            with st.expander("Mathematical Content Analysis"):
                formulas = session_data['extracted_formulas']
                
                # Group formulas by type
                formula_types = {}
                for formula in formulas:
                    if isinstance(formula, dict):
                        ftype = formula.get('type', 'unknown')
                        if ftype not in formula_types:
                            formula_types[ftype] = 0
                        formula_types[ftype] += 1
                
                for ftype, count in formula_types.items():
                    st.write(f"**{ftype.replace('_', ' ').title()}**: {count} instances")
    
    def display_brd_results(self, session_data: Dict[str, Any]):
        """Display BRD results with export options"""
        st.markdown("### Generated BRD")
        
        # Quality overview
        quality_scores = session_data.get('quality_scores', {})
        if quality_scores:
            avg_quality = sum(quality_scores.values()) / len(quality_scores)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Overall Quality", f"{avg_quality:.1f}%")
            with col2:
                st.metric("Sections", len(quality_scores))
            with col3:
                high_quality = len([s for s in quality_scores.values() if s >= 80])
                st.metric("High Quality Sections", f"{high_quality}/{len(quality_scores)}")
            with col4:
                if session_data.get('generated_at'):
                    st.metric("Generated", session_data['generated_at'].strftime("%H:%M"))
        
        # Export options
        st.markdown("### Export BRD")
        col1, col2, col3, col4 = st.columns(4)
        
        brd_content = session_data.get('brd_content', {})
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        with col1:
            if st.button("Export Word", use_container_width=True):
                try:
                    word_doc = export_to_word_docx(brd_content)
                    st.download_button(
                        "Download DOCX",
                        word_doc.getvalue(),
                        f"BRD_{timestamp}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Export error: {str(e)}")
        
        with col2:
            if st.button("Export PDF", use_container_width=True):
                try:
                    pdf_doc = export_to_pdf(brd_content)
                    st.download_button(
                        "Download PDF",
                        pdf_doc.getvalue(),
                        f"BRD_{timestamp}.pdf",
                        "application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Export error: {str(e)}")
        
        with col3:
            if st.button("Export Excel", use_container_width=True):
                try:
                    excel_doc = export_to_excel(brd_content)
                    st.download_button(
                        "Download XLSX",
                        excel_doc.getvalue(),
                        f"BRD_{timestamp}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Export error: {str(e)}")
        
        with col4:
            if st.button("Export JSON", use_container_width=True):
                try:
                    json_content = export_to_json(brd_content)
                    st.download_button(
                        "Download JSON",
                        json_content,
                        f"BRD_{timestamp}.json",
                        "application/json",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Export error: {str(e)}")
        
        # BRD content preview
        if st.checkbox("Show BRD Content Preview"):
            with st.expander("BRD Sections (First 3)", expanded=True):
                for i, (section_name, content) in enumerate(list(brd_content.items())[:3]):
                    st.markdown(f"**{section_name}**")
                    
                    if isinstance(content, pd.DataFrame):
                        st.dataframe(content, use_container_width=True)
                    elif isinstance(content, dict):
                        for subsection, subcontent in content.items():
                            st.markdown(f"*{subsection}*")
                            if isinstance(subcontent, pd.DataFrame):
                                st.dataframe(subcontent, use_container_width=True)
                            else:
                                preview = str(subcontent)[:300] + "..." if len(str(subcontent)) > 300 else str(subcontent)
                                st.text(preview)
                    else:
                        preview = str(content)[:300] + "..." if len(str(content)) > 300 else str(content)
                        st.text(preview)
                    
                    st.markdown("---")
    
    def process_input(self, user_input: str) -> str:
        """Enhanced input processing with document context"""
        session_data = self.get_session_data()
        user_input_lower = user_input.lower()
        
        # Context-aware responses based on current state
        if 'upload' in user_input_lower or 'document' in user_input_lower:
            return self.handle_document_questions(session_data)
        elif 'generate' in user_input_lower or 'create' in user_input_lower or 'brd' in user_input_lower:
            return self.handle_generation_questions(session_data)
        elif 'formula' in user_input_lower or 'mathematical' in user_input_lower:
            return self.handle_formula_questions(session_data)
        elif 'export' in user_input_lower or 'download' in user_input_lower:
            return self.handle_export_questions(session_data)
        elif 'quality' in user_input_lower or 'score' in user_input_lower:
            return self.handle_quality_questions(session_data)
        elif any(word in user_input_lower for word in ['regulatory', 'compliance', 'basel', 'sox', 'gdpr']):
            return self.handle_regulatory_questions(session_data)
        else:
            return self.handle_general_questions(user_input)
    
    def handle_document_questions(self, session_data: Dict[str, Any]) -> str:
        """Handle document-related questions"""
        if session_data.get('document_analysis'):
            doc_name = session_data.get('document_name', 'your document')
            analysis = session_data['document_analysis']
            
            return f"""I've analyzed **{doc_name}** and found:

**Document Intelligence:**
- Type: {analysis.get('document_type', 'Unknown')}
- Mathematical Complexity: {analysis.get('mathematical_complexity', 'Unknown')}
- Regulatory Frameworks: {', '.join(analysis.get('regulatory_framework', ['None detected']))}
- Extracted Formulas: {len(session_data.get('extracted_formulas', []))}
- Tables Detected: {analysis.get('table_count', 0)}

The document is ready for BRD generation. Would you like me to create a comprehensive Business Requirements Document?"""
        else:
            return """To analyze a document:

1. Go to the **Document Processing** tab
2. Upload your PDF, DOCX, or TXT file
3. Configure analysis options (formula extraction, regulatory detection)
4. Click **Analyze Document**

I can process regulatory documents like Basel frameworks, SOX compliance documents, GDPR guidelines, and more. I'll extract mathematical formulas, detect regulatory frameworks, and prepare comprehensive analysis for BRD generation."""
    
    def handle_generation_questions(self, session_data: Dict[str, Any]) -> str:
        """Handle BRD generation questions"""
        if session_data.get('brd_content'):
            return f"""Your BRD has been generated successfully!

**Quality Overview:**
- Overall Quality: {sum(session_data.get('quality_scores', {}).values()) / len(session_data.get('quality_scores', {1})):.1f}%
- Sections: {len(session_data.get('quality_scores', {}))}
- Generated: {session_data.get('generated_at', datetime.now()).strftime('%Y-%m-%d %H:%M')}

You can export it in multiple formats from the **Results & Export** tab."""
            
        elif session_data.get('document_text'):
            return """Your document is ready for BRD generation!

**Available Options:**
- Template Types: Regulatory Compliance, Standard Enterprise, Technical Integration
- Quality Levels: Enterprise, Premium, Standard
- Compliance Focus: Basel III, SOX, GDPR, General Regulatory

Go to the **Results & Export** tab and click **Generate Comprehensive BRD** to create your Business Requirements Document."""
        else:
            return """To generate a BRD, I need a document to analyze first.

**Process:**
1. Upload a regulatory document in the **Document Processing** tab
2. Let me analyze it for regulatory frameworks and mathematical content
3. I'll then generate a comprehensive BRD with:
   - Executive Summary with regulatory focus
   - Detailed requirements mapping
   - Mathematical formula integration
   - Compliance verification
   - Quality assessment"""
    
    def handle_formula_questions(self, session_data: Dict[str, Any]) -> str:
        """Handle mathematical formula questions"""
        formulas = session_data.get('extracted_formulas', [])
        
        if formulas:
            # Analyze formula types
            formula_types = {}
            high_conf_count = 0
            
            for formula in formulas:
                if isinstance(formula, dict):
                    ftype = formula.get('type', 'unknown')
                    formula_types[ftype] = formula_types.get(ftype, 0) + 1
                    if formula.get('confidence', 0) > 0.7:
                        high_conf_count += 1
            
            type_summary = '\n'.join([f"- {ftype.replace('_', ' ').title()}: {count}" for ftype, count in formula_types.items()])
            
            return f"""**Mathematical Content Analysis:**

Found {len(formulas)} mathematical elements:

{type_summary}

**High Confidence Formulas:** {high_conf_count}
**Complexity Level:** {session_data.get('document_analysis', {}).get('mathematical_complexity', 'Unknown')}

These formulas include Basel risk calculations, correlation parameters, and regulatory compliance equations that will be integrated into your BRD for comprehensive regulatory coverage."""
        else:
            return """I haven't detected mathematical formulas yet. 

To extract formulas:
1. Upload a document with mathematical content
2. Enable **Extract Mathematical Formulas** in analysis options
3. I'll identify and categorize:
   - Risk weight formulas
   - Correlation calculations
   - Capital requirement equations
   - Regulatory compliance formulas
   - Statistical expressions

This is particularly useful for Basel documents, risk management frameworks, and quantitative regulatory requirements."""
    
    def handle_export_questions(self, session_data: Dict[str, Any]) -> str:
        """Handle export questions"""
        if session_data.get('brd_content'):
            return """Your BRD is ready for export in multiple formats:

**Available Formats:**
- **Word (DOCX)**: Fully formatted document with tables and structure
- **PDF**: Professional presentation-ready format
- **Excel (XLSX)**: Structured data in spreadsheet format
- **JSON**: Machine-readable data format

All exports include:
- Complete regulatory analysis
- Mathematical formula references
- Quality assessment scores
- Compliance verification

Go to the **Results & Export** tab to download your preferred format."""
        else:
            return """No BRD is available for export yet.

**To export a BRD:**
1. Upload and analyze a document
2. Generate the BRD
3. Choose your export format

I can export in Word, PDF, Excel, and JSON formats, all preserving the regulatory structure and mathematical content."""
    
    def handle_quality_questions(self, session_data: Dict[str, Any]) -> str:
        """Handle quality-related questions"""
        quality_scores = session_data.get('quality_scores', {})
        
        if quality_scores:
            avg_quality = sum(quality_scores.values()) / len(quality_scores)
            high_quality = len([s for s in quality_scores.values() if s >= 80])
            
            return f"""**BRD Quality Assessment:**

- **Overall Quality:** {avg_quality:.1f}%
- **High Quality Sections:** {high_quality}/{len(quality_scores)}
- **Total Sections:** {len(quality_scores)}

**Quality Factors:**
- Content completeness and depth
- Regulatory compliance alignment
- Mathematical accuracy
- Structural integrity
- Stakeholder coverage

Quality scores above 80% indicate enterprise-ready sections. Lower scores suggest areas for enhancement or additional detail."""
        else:
            return """Quality assessment is performed automatically during BRD generation.

**Quality Metrics Include:**
- Completeness scoring
- Regulatory compliance verification
- Mathematical formula validation
- Structural consistency
- Requirement traceability

Once you generate a BRD, I'll provide detailed quality scores and improvement recommendations for each section."""
    
    def handle_regulatory_questions(self, session_data: Dict[str, Any]) -> str:
        """Handle regulatory compliance questions"""
        return """**Supported Regulatory Frameworks:**

**Banking & Finance:**
- Basel III/IV - Capital adequacy and market risk
- Dodd-Frank - US financial system reform
- MiFID II - European investment services
- Solvency II - Insurance regulation

**General Compliance:**
- SOX - Sarbanes-Oxley Act
- GDPR - Data protection regulation
- PCI-DSS - Payment card security
- ISO 27001 - Information security

**Risk Management:**
- Market Risk (MAR standards)
- Credit Risk assessment
- Operational Risk controls
- Liquidity Risk management

I automatically detect these frameworks in your documents and ensure BRDs address all applicable regulatory requirements with proper mathematical risk calculations."""
    
    def handle_general_questions(self, user_input: str) -> str:
        """Handle general questions"""
        return f"""I'm the BRD Generator, specializing in regulatory document analysis and Business Requirements Document creation.

**I can help you with:**
- Document analysis with mathematical formula extraction
- Regulatory framework detection and compliance
- Comprehensive BRD generation
- Quality assessment and export in multiple formats

**Current capabilities:**
- PDF, DOCX, TXT document processing
- Basel III, SOX, GDPR compliance frameworks
- Advanced mathematical content analysis
- Enterprise-grade BRD templates

What would you like to know about these capabilities or how I can help with your specific requirements?"""
    
    def explain_brd_process(self) -> str:
        """Explain the BRD generation process"""
        return """**BRD Generation Process:**

**1. Document Analysis**
- Upload regulatory documents (PDF, DOCX, TXT)
- Extract mathematical formulas and risk calculations
- Detect regulatory frameworks automatically
- Analyze document complexity and structure

**2. Intelligence Processing**
- Identify key regulatory requirements
- Map mathematical relationships
- Assess compliance obligations
- Extract stakeholder information

**3. BRD Generation**
- Generate 14 comprehensive sections
- Include executive summary and background
- Map business and functional requirements
- Integrate mathematical analysis
- Add regulatory compliance matrix

**4. Quality Assurance**
- Score each section for completeness
- Verify regulatory compliance
- Validate mathematical accuracy
- Assess stakeholder coverage

**5. Export & Delivery**
- Multiple format options (Word, PDF, Excel, JSON)
- Professional formatting with regulatory structure
- Quality metrics and improvement recommendations

The entire process leverages AI to ensure your BRD meets enterprise standards and regulatory requirements."""
    
    def explain_regulatory_frameworks(self) -> str:
        """Explain supported regulatory frameworks"""
        return """**Regulatory Framework Support:**

**Banking & Financial Services:**
- Basel III/IV: Capital adequacy, market risk, credit risk
- Dodd-Frank: Volcker Rule, derivatives, stress testing
- MiFID II: Best execution, transaction reporting
- CCAR/DFAST: Capital planning and stress testing
- CRD IV: Capital Requirements Directive

**Data Protection & Privacy:**
- GDPR: EU data protection regulation
- CCPA: California Consumer Privacy Act
- HIPAA: Healthcare data protection

**Corporate Governance:**
- SOX: Sarbanes-Oxley financial reporting
- COSO: Internal control frameworks

**Industry Standards:**
- PCI-DSS: Payment card data security
- ISO 27001: Information security management
- NIST: Cybersecurity frameworks

I automatically detect these frameworks in your documents and ensure BRDs include proper compliance mapping, risk assessments, and mathematical validation requirements."""
