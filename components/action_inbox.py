"""Action inbox component."""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.actions import ActionManager
from src.models import ActionStatus


def render_action_inbox(action_manager: ActionManager, owner: str) -> None:
    """
    Render action inbox showing pending actions for the owner.
    
    Args:
        action_manager: ActionManager instance
        owner: Owner name
    """
    st.markdown("### 📬 내 작업함")
    
    # Get statistics
    stats = action_manager.get_action_stats(owner)
    
    # Display stats
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("전체", stats['total'])
    with col2:
        st.metric("해야 할 일", stats['todo'], delta=None)
    with col3:
        st.metric("진행 중", stats['doing'], delta=None)
    with col4:
        st.metric("완료", stats['done'], delta=None)
    with col5:
        st.metric("⚠️ 지연", stats['overdue'], delta=None)
    
    # Get pending actions
    pending_actions = action_manager.get_pending_actions(owner)
    
    if len(pending_actions) == 0:
        st.info("✅ 대기 중인 조치가 없습니다.")
        return
    
    # Show pending actions table
    st.markdown("#### 대기 중인 조치")
    
    # Prepare display dataframe
    display_df = pending_actions.copy()
    display_df['due_date_dt'] = pd.to_datetime(display_df['due_date'])
    display_df['days_remaining'] = (display_df['due_date_dt'] - datetime.now()).dt.days
    
    # Sort by due date
    display_df = display_df.sort_values('due_date_dt')
    
    # Display table
    for idx, row in display_df.iterrows():
        with st.expander(f"🎯 {row['id']} - {row['category']} ({row['status']})"):
            col_a, col_b = st.columns([3, 1])
            
            with col_a:
                st.markdown(f"**설명:** {row['description']}")
                if row['site_id']:
                    st.markdown(f"**국소:** {row['site_id']}")
                st.markdown(f"**생성일:** {row['created_at'][:10]}")
                st.markdown(f"**마감일:** {row['due_date'][:10]} ({row['days_remaining']}일 남음)")
            
            with col_b:
                # Status update
                status_options = {
                    "해야 할 일": ActionStatus.TODO.value,
                    "진행 중": ActionStatus.DOING.value,
                    "완료": ActionStatus.DONE.value
                }
                status_labels = list(status_options.keys())
                status_values = list(status_options.values())
                current_index = status_values.index(row['status'])
                
                new_status_label = st.selectbox(
                    "상태 변경",
                    options=status_labels,
                    index=current_index,
                    key=f"status_{row['id']}"
                )
                new_status = status_options[new_status_label]
                
                if st.button("업데이트", key=f"update_{row['id']}"):
                    if action_manager.update_action_status(row['id'], ActionStatus(new_status)):
                        st.success(f"상태 업데이트: {new_status}")
                        st.rerun()


def render_compact_action_inbox(action_manager: ActionManager, owner: str) -> None:
    """
    Render compact action inbox for sidebar or top bar.
    
    Args:
        action_manager: ActionManager instance
        owner: Owner name
    """
    stats = action_manager.get_action_stats(owner)
    
    st.markdown(f"**📬 작업:** {stats['todo']} 대기 | {stats['doing']} 진행 | {stats['overdue']} ⚠️")
    
    if stats['overdue'] > 0:
        st.warning(f"⚠️ {stats['overdue']}건의 조치가 지연되었습니다.")

