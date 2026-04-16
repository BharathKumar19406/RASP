import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from storage.db import SessionLocal
from storage.models import RuntimeEvent

def toggle_flag(event_id, new_status):
    db_local = SessionLocal()
    try:
        ev = db_local.query(RuntimeEvent).filter(RuntimeEvent.id == event_id).first()
        if ev:
            ev.is_flagged = new_status
            db_local.commit()
    finally:
        db_local.close()

def show_dashboard():
    st.subheader("🚨 Security Events & Request Analysis")
    
    db = SessionLocal()
    try:
        events = db.query(RuntimeEvent).order_by(RuntimeEvent.timestamp.desc()).limit(100).all()
    finally:
        db.close()

    if not events:
        st.info("No security events yet.")
        return

    # ==================== TABS ====================
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🔍 Detailed Events", "🎯 Request Sectors", "📈 Adaptation Metrics", "🛡️ SOC Analyst"])
    
    # ==================== TAB 1: OVERVIEW ====================
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Events", len(events))
        with col2:
            high_risk = sum(1 for e in events if e.risk_level == "HIGH")
            st.metric("🚨 High Risk", high_risk)
        with col3:
            adapted = sum(1 for e in events if e.adaptation_triggered)
            st.metric("📈 Adapted", adapted)
        with col4:
            unique_ips = len(set(e.ip_hash for e in events))
            st.metric("Unique IPs", unique_ips)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        # Risk Level Distribution
        with col1:
            df_risk = pd.DataFrame([{
                "Risk": e.risk_level,
                "Count": 1
            } for e in events])
            df_risk_agg = df_risk.groupby("Risk").size().reset_index(name="Count")
            
            risk_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
            df_risk_agg["order"] = df_risk_agg["Risk"].map(risk_order)
            df_risk_agg = df_risk_agg.sort_values("order").drop("order", axis=1)
            
            fig1 = px.bar(df_risk_agg, x="Risk", y="Count", color="Risk",
                         color_discrete_map={"LOW": "#2E8B57", "MEDIUM": "#FFA500", "HIGH": "#DC143C"},
                         title="Risk Level Distribution")
            st.plotly_chart(fig1, width='stretch')
        
        # Attack Types
        with col2:
            df_attacks = pd.DataFrame([{
                "Attack": e.attack_type,
                "Count": 1
            } for e in events])
            df_attacks_agg = df_attacks.groupby("Attack").size().reset_index(name="Count").sort_values("Count", ascending=False).head(10)
            
            fig2 = px.bar(df_attacks_agg, x="Count", y="Attack", orientation="h",
                         title="Top Attack Types", color="Count", color_continuous_scale="Reds")
            st.plotly_chart(fig2, width='stretch')
    
    # ==================== TAB 2: DETAILED EVENTS ====================
    with tab2:
        st.write("### Request Details with Full Context")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_risk = st.multiselect("Risk Level", ["LOW", "MEDIUM", "HIGH"], default=["LOW", "MEDIUM", "HIGH"], key="risk_filter_tab2")
        with col2:
            selected_attacks = st.multiselect("Attack Type", list(set(e.attack_type for e in events)), key="attack_filter_tab2")
        with col3:
            timerange = st.radio("Time Range", ["Last Hour", "Last Day", "All"], horizontal=True, key="time_tab2")
        
        # Filter events
        filtered_events = events
        if timerange == "Last Hour":
            cutoff = datetime.utcnow() - timedelta(hours=1)
            filtered_events = [e for e in filtered_events if e.timestamp >= cutoff]
        elif timerange == "Last Day":
            cutoff = datetime.utcnow() - timedelta(days=1)
            filtered_events = [e for e in filtered_events if e.timestamp >= cutoff]
        
        if selected_risk:
            filtered_events = [e for e in filtered_events if e.risk_level in selected_risk]
        
        if selected_attacks:
            filtered_events = [e for e in filtered_events if e.attack_type in selected_attacks]
        
        # Display detailed events
        for idx, event in enumerate(filtered_events):
            with st.expander(f"📌 {event.timestamp.strftime('%H:%M:%S')} | {event.attack_type} | {event.endpoint[:40]}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**⏱️ Time**")
                    st.write(event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'))
                    st.write("**🔗 Endpoint**")
                    st.code(event.endpoint, language="text")
                    st.write("**🔄 Method**")
                    st.write(event.method)
                
                with col2:
                    st.write("**📊 Risk Level**")
                    risk_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
                    st.write(f"{risk_color.get(event.risk_level, '⚪')} {event.risk_level}")
                    flag_status = "🚩 Flagged" if hasattr(event, 'is_flagged') and event.is_flagged else ""
                    if flag_status:
                        st.write(f"**{flag_status}**")
                    st.write("**🎯 Drift Score**")
                    st.write(f"{event.drift_score:.1f}")
                    st.write("**🔐 Confidence**")
                    st.write(f"{event.attack_confidence:.0%}")
                
                with col3:
                    st.write("**🌐 IP Hash**")
                    st.code(event.ip_hash[:12], language="text")
                    st.write("**📦 Body Size**")
                    st.write(f"{event.body_size} bytes")
                    st.write("**📋 Parameters**")
                    st.write(f"{event.param_count} params")
                
                st.divider()
                
                # Attack Details Section
                st.write("### 🚨 Attack Analysis")
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write("**Category**")
                    category_badges = {
                        "SQL_INJECTION": "🔴",
                        "XSS": "🟠",
                        "PATH_TRAVERSAL": "🟡",
                        "SSRF": "🔵",
                        "COMMAND_INJECTION": "🔴",
                        "XXE": "🟣",
                        "PARAMETER_SPAM": "🟠",
                        "PAYLOAD_FLOODING": "🔴",
                        "BEHAVIORAL_ANOMALY": "⚪"
                    }
                    badge = category_badges.get(event.attack_category, "⚪")
                    st.write(f"{badge} {event.attack_category.replace('_', ' ')}")
                    
                    st.write("**Evidence**")
                    import json
                    evidence = json.loads(event.attack_evidence) if event.attack_evidence else []
                    for ev in evidence:
                        st.write(f"• {ev}")
                
                with col2:
                    st.write("**Description**")
                    st.write(event.attack_description if event.attack_description else "No description available")
                
                st.divider()
                
                # Request Sample
                if event.request_sample:
                    st.write("### 📄 Request Sample")
                    st.code(event.request_sample[:500], language="json")
                
                # Adaptation Info
                if event.adaptation_triggered or event.baseline_before is not None:
                    st.write("### 📈 Baseline Adaptation")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Before", f"{event.baseline_before:.0f}" if event.baseline_before else "N/A")
                    with col2:
                        st.metric("After", f"{event.baseline_after:.0f}" if event.baseline_after else "N/A")
                    with col3:
                        adapted_badge = "✅ Adapted" if event.adaptation_triggered else "⏸️ Not Adapted"
                        st.write(f"**Status**: {adapted_badge}")
    
    # ==================== TAB 3: REQUEST SECTORS ====================
    with tab3:
        st.write("### Request Categorization by Sector")
        
        # Create sector breakdown
        sectors_map = {
            "SQL_INJECTION": "Database Attack",
            "XSS": "Client-Side Attack",
            "PATH_TRAVERSAL": "File System Attack",
            "SSRF": "Network Attack",
            "COMMAND_INJECTION": "System Command Attack",
            "XXE": "XML Attack",
            "PARAMETER_SPAM": "Fuzzing/Enumeration",
            "PAYLOAD_FLOODING": "DoS/Resource Abuse",
            "BEHAVIORAL_ANOMALY": "Behavioral Anomaly"
        }
        
        sector_events = {}
        for event in events:
            sector = sectors_map.get(event.attack_category, "Unknown")
            if sector not in sector_events:
                sector_events[sector] = []
            sector_events[sector].append(event)
        
        # Display sectors in columns
        cols = st.columns(3)
        for idx, (sector, sector_list) in enumerate(sorted(sector_events.items())):
            with cols[idx % 3]:
                st.write(f"### {sector}")
                st.metric("Events", len(sector_list))
                
                high_risk_count = sum(1 for e in sector_list if e.risk_level == "HIGH")
                st.write(f"🔴 High Risk: {high_risk_count}")
                
                avg_confidence = sum(e.attack_confidence for e in sector_list) / len(sector_list)
                st.write(f"📊 Avg Confidence: {avg_confidence:.0%}")
        
        st.divider()
        
        # Sector comparison chart
        sector_df = pd.DataFrame([
            {"Sector": sectors_map.get(e.attack_category, "Unknown"), "Count": 1} for e in events
        ])
        sector_agg = sector_df.groupby("Sector").size().reset_index(name="Count").sort_values("Count", ascending=False)
        
        fig = px.pie(sector_agg, names="Sector", values="Count", title="Events by Request Sector")
        st.plotly_chart(fig, width='stretch')
    
    # ==================== TAB 4: ADAPTATION METRICS ====================
    with tab4:
        st.write("### System Adaptation & Learning Metrics")
        
        # Adaptation Statistics
        adapted_events = [e for e in events if e.adaptation_triggered]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Baselines Adapted", len(adapted_events))
        with col2:
            avg_baseline_change = 0
            if adapted_events:
                changes = [abs(e.baseline_after - e.baseline_before) for e in adapted_events if e.baseline_after and e.baseline_before]
                avg_baseline_change = sum(changes) / len(changes) if changes else 0
            st.metric("Avg Change", f"{avg_baseline_change:.1f} bytes")
        with col3:
            endpoints_adapted = len(set(e.endpoint for e in adapted_events))
            st.metric("Endpoints Adapted", endpoints_adapted)
        with col4:
            last_adapted = adapted_events[0].timestamp if adapted_events else None
            st.metric("Last Adaptation", last_adapted.strftime('%H:%M') if last_adapted else "N/A")
        
        st.divider()
        
        # Adaptation Timeline
        st.write("### Adaptation Timeline")
        adaptation_data = [
            {
                "time": e.timestamp,
                "endpoint": e.endpoint[:30],
                "baseline_change": abs(e.baseline_after - e.baseline_before) if (e.baseline_after and e.baseline_before) else 0,
                "adapted": e.adaptation_triggered
            } for e in events if e.adaptation_triggered and e.baseline_after and e.baseline_before
        ]
        
        if adaptation_data:
            adaptation_timeline = pd.DataFrame(adaptation_data).sort_values("time")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=adaptation_timeline["time"],
                y=adaptation_timeline["baseline_change"],
                mode='markers+lines',
                marker=dict(size=10, color=adaptation_timeline["baseline_change"], colorscale='Viridis'),
                text=adaptation_timeline["endpoint"],
                hovertemplate='<b>%{text}</b><br>Change: %{y:.1f} bytes<extra></extra>'
            ))
            fig.update_layout(title="Baseline Adaptation Changes Over Time", 
                            xaxis_title="Time", yaxis_title="Baseline Change (bytes)")
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No adaptation events recorded yet. System is still learning...")
        
        st.divider()
        
        # Top Adapted Endpoints
        st.write("### Top Endpoints with Most Adaptations")
        adapted_by_endpoint ={}
        for e in adapted_events:
            if e.endpoint not in adapted_by_endpoint:
                adapted_by_endpoint[e.endpoint] = {"count": 0, "avg_change": 0, "changes": []}
            adapted_by_endpoint[e.endpoint]["count"] += 1
            if e.baseline_after and e.baseline_before:
                adapted_by_endpoint[e.endpoint]["changes"].append(abs(e.baseline_after - e.baseline_before))
        
        for endpoint, data in adapted_by_endpoint.items():
            data["avg_change"] = sum(data["changes"]) / len(data["changes"]) if data["changes"] else 0
        
        top_endpoints = sorted(adapted_by_endpoint.items(), key=lambda x: x[1]["count"], reverse=True)[:5]
        
        endpoint_df = pd.DataFrame([
            {
                "Endpoint": endpoint[:50],
                "Adaptations": data["count"],
                "Avg Change": f"{data['avg_change']:.1f} bytes"
            } for endpoint, data in top_endpoints
        ])
        
        st.dataframe(endpoint_df, width='stretch')

    # ==================== TAB 5: SOC ANALYST CONSOLE ====================
    with tab5:
        st.write("### 🛡️ SOC Analyst Console")
        st.write("Triage and manage flagged requests for further investigation.")
        
        flagged_events = [e for e in events if getattr(e, 'is_flagged', False)]
        unflagged_events = [e for e in events if not getattr(e, 'is_flagged', False) and getattr(e, 'risk_level', '') in ["MEDIUM", "HIGH"]]
        
        col_f, col_u = st.columns(2)
        with col_f:
            st.subheader(f"🚩 Flagged for Triage ({len(flagged_events)})")
            for e in flagged_events:
                with st.expander(f"🚩 {e.timestamp.strftime('%H:%M:%S')} | {e.attack_type}", expanded=False):
                    st.write(f"**Endpoint:** {e.endpoint}")
                    st.write(f"**IP:** {e.ip_hash}")
                    st.write(f"**Risk Level:** {e.risk_level}")
                    if st.button("Unflag", key=f"unflag_{e.id}"):
                        toggle_flag(e.id, False)
                        st.rerun()

        with col_u:
            st.subheader(f"⚠️ High/Medium Risk to Review ({len(unflagged_events)})")
            for e in unflagged_events[:20]:
                with st.expander(f"⚠️ {e.timestamp.strftime('%H:%M:%S')} | {e.attack_type}", expanded=False):
                    st.write(f"**Endpoint:** {e.endpoint}")
                    st.write(f"**IP:** {e.ip_hash}")
                    st.write(f"**Risk Level:** {e.risk_level}")
                    if st.button("Flag for Review", key=f"flag_{e.id}"):
                        toggle_flag(e.id, True)
                        st.rerun()
