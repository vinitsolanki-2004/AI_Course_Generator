import streamlit as st
from services.display import display_course_content, display_course_generator, display_quiz_tab

def main():
    st.set_page_config(page_title="Course Generator", page_icon="📚", layout="wide")
    
    # Initialize session state variables if they don't exist
    if "course_data" not in st.session_state:
        st.session_state.course_data = None
    
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = None
    
    if "current_view" not in st.session_state:
        st.session_state.current_view = "course_generator"  # Options: course_generator, course_view, quiz_view
    
    st.title("🎓 Educational Course Generator")
    
    # Navigation tabs
    tabs = ["Course Generator", "Course View", "Quiz"]
    selected_tab = st.radio("Navigation", tabs, horizontal=True, 
                         index=0 if st.session_state.current_view == "course_generator" else 
                                1 if st.session_state.current_view == "course_view" else 2)
    
    if selected_tab == "Course Generator":
        st.session_state.current_view = "course_generator"
        display_course_generator()
    elif selected_tab == "Course View" and st.session_state.course_data is not None:
        st.session_state.current_view = "course_view"
        display_course_content(st.session_state.course_data)
    elif selected_tab == "Quiz":
        st.session_state.current_view = "quiz_view"
        display_quiz_tab()
    else:
        st.info("Please generate a course first before viewing it or taking a quiz.")

if __name__ == "__main__":
    main()