"""
FinGuard Dashboard - Main Page
Real-time fraud detection monitoring with integrated simulator
"""

import streamlit as st
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.database import get_db
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="FinGuard - Fraud Detection Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .high-risk {
        color: #d62728;
        font-weight: bold;
    }
    .medium-risk {
        color: #ff7f0e;
        font-weight: bold;
    }
    .low-risk {
        color: #2ca02c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'db' not in st.session_state:
    try:
        st.session_state.db = get_db()
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        st.stop()

# Header
st.markdown('<p class="main-header">🛡️ FinGuard - Behavioral Fraud Detection</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🛡️ FinGuard")
    st.markdown("*Zero-Cost AI Fraud Detection*")
    st.markdown("---")
    
    st.markdown("### System Status")
    
    # System health checks
    try:
        db_check = st.session_state.db is not None
        st.success("✅ LanceDB Connected")
    except:
        st.error("❌ LanceDB Error")
    
    try:
        import ollama
        ollama.list()
        st.success("✅ Ollama LLM Active")
    except:
        st.warning("⚠️  Ollama Not Running")
    
    try:
        from sentence_transformers import SentenceTransformer
        st.success("✅ Embeddings Ready")
    except:
        st.error("❌ Embeddings Error")
    
    st.markdown("---")
    st.markdown("### Quick Stats")
    
    # Get stats
    try:
        stats = st.session_state.db.get_statistics()
        
        st.metric("Total Transactions", stats['total_transactions'])
        st.metric("Flagged", stats['flagged_count'], 
                 delta=f"{stats['flagged_count']} high risk",
                 delta_color="inverse")
        st.metric("Avg Fraud Score", f"{stats['avg_fraud_score']:.1f}/100")
    except Exception as e:
        st.error(f"Stats error: {e}")
        stats = {
            'total_transactions': 0,
            'flagged_count': 0,
            'avg_fraud_score': 0,
            'high_risk_count': 0
        }

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔍 Transactions", "📈 Analytics", "⚙️ System"])

with tab1:
    st.markdown("## System Overview")
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Transactions",
            value=stats['total_transactions'],
            delta=f"+{stats['total_transactions']}" if stats['total_transactions'] > 0 else "0"
        )
    
    with col2:
        st.metric(
            label="High Risk Detected",
            value=stats['high_risk_count'],
            delta=f"{stats['flagged_count']} flagged",
            delta_color="inverse"
        )
    
    with col3:
        detection_rate = (stats['flagged_count'] / max(stats['total_transactions'], 1)) * 100
        st.metric(
            label="Detection Rate",
            value=f"{detection_rate:.1f}%"
        )
    
    with col4:
        st.metric(
            label="Avg Fraud Score",
            value=f"{stats['avg_fraud_score']:.1f}/100"
        )
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Risk Distribution")
        
        try:
            df = st.session_state.db.get_all_transactions()
            
            if len(df) > 0 and 'risk_level' in df.columns:
                risk_counts = df['risk_level'].value_counts()
                
                colors = {'High': '#d62728', 'Medium': '#ff7f0e', 'Low': '#2ca02c'}
                color_list = [colors.get(level, '#999999') for level in risk_counts.index]
                
                fig = go.Figure(data=[go.Pie(
                    labels=risk_counts.index,
                    values=risk_counts.values,
                    marker=dict(colors=color_list),
                    hole=0.4
                )])
                
                fig.update_layout(
                    showlegend=True,
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No transaction data available yet. Go to System tab and click 'Run Sample Transactions'!")
                
        except Exception as e:
            st.error(f"Error loading risk distribution: {e}")
    
    with col2:
        st.markdown("### Fraud Score Timeline")
        
        try:
            if len(df) > 0 and 'fraud_score' in df.columns:
                df_clean = df[df['fraud_score'].notna()].copy()
                
                if len(df_clean) > 0:
                    df_clean['timestamp_dt'] = pd.to_datetime(df_clean['timestamp'])
                    df_sorted = df_clean.sort_values('timestamp_dt')
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=df_sorted['timestamp_dt'],
                        y=df_sorted['fraud_score'],
                        mode='lines+markers',
                        name='Fraud Score',
                        line=dict(color='#1f77b4', width=2),
                        marker=dict(size=6)
                    ))
                    
                    # Add threshold line
                    fig.add_hline(y=75, line_dash="dash", line_color="red", 
                                 annotation_text="High Risk Threshold")
                    
                    fig.update_layout(
                        xaxis_title="Time",
                        yaxis_title="Fraud Score",
                        height=300,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📈 No fraud score data available yet")
            else:
                st.info("📈 No fraud score data available yet. Process some transactions first!")
                
        except Exception as e:
            st.error(f"Error loading timeline: {e}")
    
    # Recent high-risk transactions
    st.markdown("### 🚨 Recent High-Risk Transactions")
    
    try:
        flagged = st.session_state.db.get_flagged_transactions(limit=10)
        
        if len(flagged) > 0:
            display_df = flagged[[
                'transaction_id', 'amount', 'merchant_category',
                'fraud_score', 'risk_level', 'timestamp'
            ]].copy()
            
            display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:.2f}")
            display_df['fraud_score'] = display_df['fraud_score'].fillna(0).apply(lambda x: f"{x:.0f}")
            
            st.dataframe(display_df, use_container_width=True, height=250)
        else:
            st.info("✅ No high-risk transactions detected")
    except Exception as e:
        st.error(f"Error loading flagged transactions: {e}")

with tab2:
    st.markdown("## Transaction Monitor")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_filter = st.selectbox(
            "Filter by Risk Level",
            ["All", "High", "Medium", "Low"]
        )
    
    with col2:
        limit = st.slider("Number of transactions", 10, 100, 50)
    
    with col3:
        flagged_only = st.checkbox("Show flagged only")
    
    st.markdown("---")
    
    # Get and display transactions
    try:
        df = st.session_state.db.get_all_transactions()
        
        if len(df) > 0:
            # Apply filters
            if flagged_only:
                df = df[df['is_flagged'] == True]
            
            if risk_filter != "All":
                df = df[df['risk_level'] == risk_filter]
            
            # Sort by timestamp
            df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp_dt', ascending=False).head(limit)
            
            # Display table
            display_df = df[[
                'transaction_id', 'amount', 'merchant_category',
                'device_type', 'fraud_score', 'risk_level', 'is_flagged', 'timestamp'
            ]].copy()
            
            # Format columns
            display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:.2f}")
            display_df['fraud_score'] = display_df['fraud_score'].fillna(0).apply(lambda x: f"{x:.0f}")
            
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("📦 No transactions available. Go to System tab and click 'Run Sample Transactions' to get started!")
            
    except Exception as e:
        st.error(f"Error loading transactions: {e}")

with tab3:
    st.markdown("## Advanced Analytics")
    
    try:
        df = st.session_state.db.get_all_transactions()
        
        if len(df) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Transactions by Merchant Category")
                
                merchant_counts = df['merchant_category'].value_counts()
                
                fig = px.bar(
                    x=merchant_counts.index,
                    y=merchant_counts.values,
                    labels={'x': 'Category', 'y': 'Count'},
                    color=merchant_counts.values,
                    color_continuous_scale='Blues'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### Transactions by Device Type")
                
                device_counts = df['device_type'].value_counts()
                
                fig = px.pie(
                    values=device_counts.values,
                    names=device_counts.index,
                    hole=0.3
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Fraud score heatmap
            st.markdown("### Fraud Activity Heatmap")
            
            if 'fraud_score' in df.columns and 'hour_of_day' in df.columns:
                df_clean = df[df['fraud_score'].notna()]
                
                if len(df_clean) > 0:
                    heatmap_data = df_clean.pivot_table(
                        values='fraud_score',
                        index='day_of_week',
                        columns='hour_of_day',
                        aggfunc='mean'
                    )
                    
                    fig = go.Figure(data=go.Heatmap(
                        z=heatmap_data.values,
                        x=heatmap_data.columns,
                        y=heatmap_data.index,
                        colorscale='Reds',
                        hoverongaps=False
                    ))
                    
                    fig.update_layout(
                        xaxis_title="Hour of Day",
                        yaxis_title="Day of Week",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No data available for analytics. Process some transactions first!")
            
    except Exception as e:
        st.error(f"Error generating analytics: {e}")

with tab4:
    st.markdown("## System Configuration")
    
    st.markdown("### Database Information")
    
    try:
        stats = st.session_state.db.get_statistics()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**LanceDB Status**")
            st.write(f"- Total Transactions: {stats['total_transactions']}")
            st.write(f"- Flagged Transactions: {stats['flagged_count']}")
            st.write(f"- Database Path: `./data/lancedb`")
        
        with col2:
            st.markdown("**Model Information**")
            st.write("- Embedding Model: `all-MiniLM-L6-v2`")
            st.write("- Vector Dimensions: 384")
            st.write("- LLM Model: `mistral:latest`")
    
    except Exception as e:
        st.error(f"Error loading system info: {e}")
    
    st.markdown("---")
    
    st.markdown("### Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Dashboard"):
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Database"):
            if st.checkbox("Confirm deletion"):
                st.warning("This will delete all transaction data!")
    
    st.markdown("---")
    
    # NEW: Transaction Simulator Section
    st.markdown("### 🎯 Transaction Simulator")
    st.write("Process sample transactions to test the fraud detection system in real-time")
    
    if st.button("▶️ Run Sample Transactions", type="primary", use_container_width=True):
        try:
            # Import necessary functions from main.py
            import importlib.util
            
            # Load main.py module dynamically
            main_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'main.py')
            spec = importlib.util.spec_from_file_location("main", main_path)
            main_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_module)
            
            # Get functions
            load_sample_transactions = main_module.load_sample_transactions
            process_transaction = main_module.process_transaction
            
            # Load sample transactions
            samples = load_sample_transactions()
            
            st.info(f"🎬 Starting simulation with {len(samples)} sample transactions...")
            
            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Track results
            results = []
            high_risk_count = 0
            medium_risk_count = 0
            low_risk_count = 0
            
            # Process each transaction
            for i, txn in enumerate(samples):
                status_text.text(f"⚙️ Processing {i+1}/{len(samples)}: {txn['transaction_id']}...")
                
                try:
                    # Process transaction (suppressing print statements)
                    import io
                    import contextlib
                    
                    # Capture stdout to prevent console spam
                    f = io.StringIO()
                    with contextlib.redirect_stdout(f):
                        result = process_transaction(txn)
                    
                    results.append(result)
                    
                    # Count risk levels
                    if result['risk_level'] == 'High':
                        high_risk_count += 1
                    elif result['risk_level'] == 'Medium':
                        medium_risk_count += 1
                    else:
                        low_risk_count += 1
                    
                except Exception as e:
                    st.error(f"❌ Error processing {txn['transaction_id']}: {e}")
                
                # Update progress
                progress_bar.progress((i + 1) / len(samples))
            
            # Clear status
            status_text.empty()
            progress_bar.empty()
            
            # Show success message
            st.success(f"✅ Successfully processed {len(results)}/{len(samples)} transactions!")
            
            # Show summary
            st.markdown("### 📊 Simulation Results")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Processed", len(results))
            
            with col2:
                st.metric("🔴 High Risk", high_risk_count)
            
            with col3:
                st.metric("🟡 Medium Risk", medium_risk_count)
            
            with col4:
                st.metric("🟢 Low Risk", low_risk_count)
            
            # Show high-risk transactions
            if high_risk_count > 0:
                st.markdown("#### 🚨 High Risk Transactions Detected")
                high_risk_results = [r for r in results if r['risk_level'] == 'High']
                
                for result in high_risk_results:
                    with st.expander(f"⚠️ {result['transaction_id']} - Score: {result['fraud_risk_score']}/100"):
                        st.write(f"**Pattern:** {result['behavioral_analysis']['known_fraud_pattern']}")
                        st.write(f"**Reasoning:** {result['reasoning']}")
                        st.write(f"**Recommendations:**")
                        for rec in result['recommendations'][:3]:
                            st.write(f"- {rec}")
            
            # Celebration!
            st.balloons()
            
            # Auto-refresh after 2 seconds to show updated dashboard
            import time
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Simulation failed: {e}")
            st.write("**Troubleshooting:**")
            st.write("1. Make sure Ollama is running: `ollama serve`")
            st.write("2. Check if Mistral model is downloaded: `ollama list`")
            st.write("3. Verify all dependencies are installed: `pip install -r requirements.txt`")
            st.write(f"4. Error details: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "FinGuard v1.0 | Powered by LanceDB + Ollama | Zero-Cost AI Stack<br>"
    "Built with Streamlit, sentence-transformers, and Mistral"
    "</div>",
    unsafe_allow_html=True
)