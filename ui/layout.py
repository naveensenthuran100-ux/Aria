"""
Aria v2 — Layout & Shell Component
==================================
Handles the left side navigation rail.
"""

import streamlit as st
import ui.copy as C


def render_sidebar():
    """Renders the side rail navigation in the sidebar."""
    current_page = st.session_state.get("page", "home")
    if current_page in ["welcome", "registration", "login"]:
        # Completely hide the sidebar when on setup pages
        st.markdown(
            '<style>[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }</style>',
            unsafe_allow_html=True
        )
        return

    with st.sidebar:
        # App logo/title
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:32px;margin-top:12px;">'
            f'<div class="aria-logo">✦</div>'
            f'<div>'
            f'<h1 style="font-size:1.2rem;font-weight:800;color:var(--text-primary);letter-spacing:-0.03em;margin:0;line-height:1;">Aria</h1>'
            f'<p style="font-size:0.65rem;color:var(--text-muted);font-weight:600;margin:2px 0 0;">Wellness Monitor</p>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        nav_items = [
            ("home", "⊞", "Dashboard"),
            ("monitoring", "◉", "Monitoring"),
            ("chat", "✧", "Chat"),
            ("history", "◷", "History"),
            ("settings", "⎈", "Settings")
        ]

        # Use an empty container to apply some vertical spacing
        st.write("") 
        
        current_page = st.session_state.get("page", "home")
        if current_page == "dashboard":
            current_page = "home"

        for page_id, icon, label in nav_items:
            # We use a standard Streamlit button but style it using CSS in theme.py
            is_active = (current_page == page_id)
            btn_class = "sidebar-nav-active" if is_active else "sidebar-nav-item"
            
            # Using ghost buttons for inactive, standard for active, but really we'll over-ride .stButton inside sidebar
            # To do this cleanly, we can inject a class using a wrapper or just rely on CSS
            # Easiest way in Streamlit is to use a container and markdown
            st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=f"nav_{page_id}", use_container_width=True):
                if not is_active:
                    st.session_state.page = page_id
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Bottom section: user status
        st.markdown('<div style="flex-grow:1;min-height:50px;"></div>', unsafe_allow_html=True)
        active_user = st.session_state.get("active_user")
        if active_user:
            st.markdown(
                f'<div style="margin-top:auto;padding-top:20px;border-top:1px solid var(--border);">'
                f'<p style="font-size:0.65rem;color:var(--text-muted);font-weight:600;margin:0;">ACTIVE PROFILE</p>'
                f'<p style="font-size:0.85rem;color:var(--text-primary);font-weight:700;margin:2px 0 0;">{active_user}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
