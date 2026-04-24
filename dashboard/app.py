import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection function
@st.cache_resource
def get_db_connection():
    try:
        db_name = os.getenv("DB_NAME", "github_db")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        
        engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db_name}")
        return engine
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None

def fetch_data(query):
    engine = get_db_connection()
    if engine:
        with engine.connect() as conn:
            return pd.read_sql_query(query, conn)
    return pd.DataFrame()

# Page Config
st.set_page_config(page_title="Portfolio Overview", layout="wide", initial_sidebar_state="collapsed")
st.title("Portfolio Overview")

# Subtle Pipeline Health Footer
pipeline_status_df = fetch_data("SELECT * FROM pipeline_runs ORDER BY run_timestamp DESC LIMIT 1;")
if not pipeline_status_df.empty:
    latest_run = pipeline_status_df.iloc[0]
    time_str = latest_run['run_timestamp'].strftime("%b %d, %Y") if pd.notnull(latest_run['run_timestamp']) else "Unknown"
    st.caption(f"Last updated: {time_str} • {latest_run['repos_processed']} repositories analyzed")

st.divider()

# Get all debug data to power the dashboard
debug_df = fetch_data("SELECT * FROM v_repo_debug ORDER BY final_score DESC;")

if not debug_df.empty:
    # 1. Top 3 Projects (Layer 1)
    st.markdown("### 🎯 Featured Projects")
    
    # Filter for top system projects
    system_repos = debug_df[debug_df['project_type'] == 'system'].head(3)
    
    if len(system_repos) > 0:
        cols = st.columns(len(system_repos))
        for i, (_, repo) in enumerate(system_repos.iterrows()):
            with cols[i]:
                st.markdown(f"#### {repo['name']}")
                
                # Human readable reason
                reason_parts = []
                if repo['activity_score'] > 60: reason_parts.append("strong activity")
                if repo['recency_score'] > 60: reason_parts.append("recent updates")
                if repo['presentation_score'] == 100: reason_parts.append("clear documentation")
                
                if reason_parts:
                    reason = f"System-level project demonstrating {', '.join(reason_parts)}."
                else:
                    reason = "Core system-level project."
                    
                st.info(reason)
                
    st.divider()
    
    # 2. Leaderboard Table
    st.markdown("### 🏆 Complete Portfolio")
    
    # Formatting functions
    def format_type(val):
        if val == 'system': return '🟢 System'
        if val == 'practice': return '🔴 Practice'
        return '⚪ Standard'
        
    def format_recency(days):
        if days < 14: return "Updated recently"
        if days < 45: return "Active within last month"
        if days < 180: return "Active within 6 months"
        return "Stale for several months"
        
    def format_score(score):
        if score >= 80: return f"{score:.0f} (High)"
        if score >= 60: return f"{score:.0f} (Medium)"
        return f"{score:.0f} (Low)"

    table_df = pd.DataFrame({
        'Repository': debug_df['name'],
        'Type': debug_df['project_type'].apply(format_type),
        'Last Updated': debug_df['days_since_push'].apply(format_recency),
        'Score': debug_df['final_score'].apply(format_score)
    })

    event = st.dataframe(
        table_df.head(10), # Only show top 10
        width='stretch', 
        hide_index=True, 
        selection_mode="single-row", 
        on_select="rerun"
    )

    # 3. Explainability Panel (Layer 2 & 3)
    st.divider()
    
    # Auto-select first row if nothing selected
    selected_idx = 0
    if event.selection.rows:
        selected_idx = event.selection.rows[0]

    selected_name = table_df.head(10).iloc[selected_idx]['Repository']
    repo_data = debug_df[debug_df['name'] == selected_name].iloc[0]

    st.markdown(f"### 🔍 Why `{repo_data['name']}` ranks here")
    
    col_narrative, col_empty = st.columns([2, 1])
    
    with col_narrative:
        # Layer 2: Narrative Judgment
        st.markdown("**Strengths:**")
        if repo_data['recency_score'] > 60:
            st.markdown("- Recently updated")
        if repo_data['activity_score'] > 60:
            st.markdown("- Active development")
        if repo_data['presentation_score'] == 100:
            st.markdown("- Excellent presentation and documentation")
        if repo_data['project_type'] == 'system':
            st.markdown("- Classified as a core system-level project")
            
        weaknesses = []
        if repo_data['recency_score'] < 40:
            weaknesses.append("Project has gone stale")
        if repo_data['activity_score'] < 40:
            weaknesses.append("Low overall development activity")
        if repo_data['popularity_score'] < 10:
            weaknesses.append("Low external engagement (stars/forks)")
        if repo_data['project_type'] == 'practice':
            weaknesses.append("Classified as coursework or practice")
            
        if weaknesses:
            st.markdown("**Weaknesses:**")
            for w in weaknesses:
                st.markdown(f"- {w}")
                
        # Layer 3: Engineering Details (Optional Toggle)
        with st.expander("⚙️ Advanced Pipeline Details"):
            st.markdown("For technical reviewers: This ranking is powered by a data pipeline ingesting GitHub APIs and applying weighted adjustments.")
            
            st.markdown(f"**Base Score:** `{repo_data['base_score']:.1f}` → **Adjusted Final:** `{repo_data['final_score']:.1f}`")
            
            st.markdown("**Raw Components:**")
            st.markdown(f"- Recency (50%): `{repo_data['recency_score']:.1f}`")
            st.markdown(f"- Activity (30%): `{repo_data['activity_score']:.1f}`")
            st.markdown(f"- Presentation (10%): `{repo_data['presentation_score']:.1f}`")
            st.markdown(f"- Popularity (10%): `{repo_data['popularity_score']:.1f}`")
            
            adjustment = (repo_data['adjustment_multiplier'] - 1) * 100
            if adjustment != 0:
                sign = "+" if adjustment > 0 else ""
                st.markdown(f"**Project Type Adjustment:** `{sign}{adjustment:.0f}%`")
else:
    st.info("No repository data found.")
