import streamlit as st
import os
from services.get_env import GOOGLE_API_KEY, GOOGLE_CSE_ID, GROQ_API_KEY
from services.search import google_search
from services.generate import generate_course_with_groq, generate_quiz_with_groq, generate_pdf, generate_quiz_pdf
from services.save import save_course_to_file, save_quiz_to_file


def display_course_generator():
    st.markdown("Generate comprehensive, structured courses on any topic using AI")
    
    # Sidebar for API keys and settings
    with st.sidebar:
        st.header("Settings")
        
        # API Key inputs
        api_key_tab, about_tab = st.tabs(["API Keys", "About"])
        
        with api_key_tab:
            input_groq_api_key = st.text_input("Groq API Key", value=GROQ_API_KEY or "", type="password")
            input_google_api_key = st.text_input("Google API Key (Required for YouTube & Search)", value=GOOGLE_API_KEY or "", type="password")
            input_google_cse_id = st.text_input("Google Custom Search Engine ID (For Search)", value=GOOGLE_CSE_ID or "", type="password")
            
            if st.button("Save API Keys"):
                # Create .env file with the API keys
                with open(".env", "w") as f:
                    f.write(f"GROQ_API_KEY={input_groq_api_key}\n")
                    f.write(f"GOOGLE_API_KEY={input_google_api_key}\n")
                    f.write(f"GOOGLE_CSE_ID={input_google_cse_id}\n")
                st.success("API keys saved successfully!")
        
        with about_tab:
            st.markdown("""
            ## About this App
            
            This app generates educational courses on any topic using:
            
            - **Groq API** with Llama 3 70B model for course content generation
            - Optional **Google Search** integration for additional context
            - Optional **YouTube** integration for relevant videos
            - **PDF export** functionality for offline reading
            - **Quiz generation** to test your knowledge
            
            The generated courses have a structured format including:
            - Course title and description
            - Learning objectives
            - Main topics with subtopics
            - Examples
            - Embedded YouTube videos
            - Summary and key takeaways
            - Optional quiz with multiple-choice questions
            
            Created using Streamlit, this app provides a user-friendly interface for course generation.
            """)
    
    # Main content
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        topic = st.text_input("Enter a Course Topic", placeholder="e.g., Machine Learning, Digital Marketing, Poetry Writing")
    
    with col2:
        use_search = st.checkbox("Use Google Search", value=False)
        if use_search:
            num_results = st.slider("Number of search results", min_value=1, max_value=10, value=3)
    
    with col3:
        include_videos = st.checkbox("Include YouTube Videos", value=False)
    
    # Advanced options
    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider("Temperature (creativity)", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
            max_tokens = st.slider("Max Tokens", min_value=1000, max_value=8000, value=4000, step=500)
            videos_per_topic = st.slider("Videos per topic", min_value=1, max_value=5, value=2)
        with col2:
            generate_quiz = st.checkbox("Generate Quiz", value=False)
            if generate_quiz:
                quiz_count = st.slider("Number of Quiz Questions", min_value=3, max_value=10, value=7)
    
    # Generate course
    if st.button("Generate Course", type="primary", disabled=not (topic and input_groq_api_key)):
        if not topic:
            st.warning("Please enter a topic")
        elif not input_groq_api_key:
            st.warning("Please enter your Groq API key in the sidebar")
        elif include_videos and not input_google_api_key:
            st.warning("YouTube integration requires a Google API key. Please enter it in the sidebar or disable YouTube integration.")
        else:
            # Get search content if requested
            search_content = ""
            if use_search and input_google_api_key and input_google_cse_id:
                with st.spinner(f"Searching Google for information about '{topic}'..."):
                    search_content = google_search(topic, num_results)
                st.success("Search completed")
            elif use_search:
                st.warning("Google search requested but API keys are missing. Proceeding without search.")
            
            # Generate the course
            with st.spinner(f"Generating course on '{topic}'..."):
                course_data = generate_course_with_groq(topic, search_content, include_videos)
            
            if "error" in course_data:
                st.error(f"Error generating course: {course_data.get('error')}")
                if "raw_content" in course_data:
                    st.text_area("Raw response:", course_data["raw_content"], height=300)
            else:
                # Save course to session state
                st.session_state.course_data = course_data
                
                # Save course to file
                filename = save_course_to_file(course_data, topic)
                
                # Generate quiz if requested
                if generate_quiz:
                    with st.spinner("Generating quiz questions..."):
                        quiz_data = generate_quiz_with_groq(course_data, quiz_count)
                    
                    if "error" in quiz_data:
                        st.error(f"Error generating quiz: {quiz_data.get('error')}")
                    else:
                        st.session_state.quiz_data = quiz_data
                        quiz_filename = save_quiz_to_file(quiz_data, topic)
                        st.success(f"Quiz generated with {len(quiz_data.get('questions', []))} questions!")
                
                # Switch to course view tab
                st.session_state.current_view = "course_view"
                st.rerun()

def display_course_content(course_data):
    if course_data is None:
        st.info("No course has been generated yet. Please go to the Course Generator tab first.")
        return
    
    # Display course content with nice formatting
    st.header(course_data.get("course_title", "Course"))
    
    # Generate PDF button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Generate PDF"):
            with st.spinner("Generating PDF..."):
                pdf_buffer = generate_pdf(course_data, course_data.get("course_title", "course"))
                pdf_filename = f"{course_data.get('course_title', 'course').replace(' ', '_').lower()}_course.pdf"
                
                st.download_button(
                    label="Download PDF",
                    data=pdf_buffer,
                    file_name=pdf_filename,
                    mime="application/pdf",
                )
    
    with col2:
        if st.session_state.quiz_data is None:
            if st.button("Generate Quiz"):
                with st.spinner("Generating quiz questions..."):
                    quiz_data = generate_quiz_with_groq(course_data, 7)  # Default to 7 questions
                
                if "error" in quiz_data:
                    st.error(f"Error generating quiz: {quiz_data.get('error')}")
                else:
                    st.session_state.quiz_data = quiz_data
                    quiz_filename = save_quiz_to_file(quiz_data, course_data.get("course_title", "course"))
                    st.success("Quiz generated successfully!")
                    st.session_state.current_view = "quiz_view"
                    st.rerun()
        else:
            if st.button("Go to Quiz"):
                st.session_state.current_view = "quiz_view"
                st.rerun()
    
    st.subheader("Description")
    st.write(course_data.get("description", ""))
    
    st.subheader("Learning Objectives")
    for obj in course_data.get("learning_objectives", []):
        st.markdown(f"- {obj}")
    
    st.subheader("Introduction")
    st.write(course_data.get("introduction", ""))
    
    st.subheader("Main Topics")
    for i, topic in enumerate(course_data.get("main_topics", []), 1):
        with st.expander(f"{i}. {topic.get('title', 'Topic')}"):
            st.write(topic.get("content", ""))
            
            # Display topic videos if available
            if "videos" in topic and topic["videos"]:
                st.subheader("Topic Videos")
                display_youtube_videos(topic["videos"])
            
            # Display subtopics
            for j, subtopic in enumerate(topic.get("subtopics", []), 1):
                st.markdown(f"**{i}.{j} {subtopic.get('title', 'Subtopic')}**")
                st.write(subtopic.get("content", ""))
                
                # Display examples
                examples = subtopic.get("examples", [])
                if examples:
                    st.markdown("**Examples:**")
                    for example in examples:
                        st.markdown(f"- {example}")
                
                # Display subtopic videos if available
                if "videos" in subtopic and subtopic["videos"]:
                    st.markdown("**Related Videos:**")
                    display_youtube_videos(subtopic["videos"])
    
    st.subheader("Summary")
    st.write(course_data.get("summary", ""))
    
    st.subheader("Key Takeaways")
    for takeaway in course_data.get("key_takeaways", []):
        st.markdown(f"- {takeaway}")

def display_quiz_tab():
    if st.session_state.quiz_data is None:
        st.info("No quiz has been generated yet.")
        
        if st.session_state.course_data is not None:
            if st.button("Generate Quiz Now"):
                with st.spinner("Generating quiz questions..."):
                    quiz_data = generate_quiz_with_groq(st.session_state.course_data, 7)  # Default to 7 questions
                
                if "error" in quiz_data:
                    st.error(f"Error generating quiz: {quiz_data.get('error')}")
                else:
                    st.session_state.quiz_data = quiz_data
                    quiz_filename = save_quiz_to_file(quiz_data, st.session_state.course_data.get("course_title", "course"))
                    st.success("Quiz generated successfully!")
                    st.rerun()
        else:
            st.write("Please generate a course first before creating a quiz.")
    else:
        # Offer option to download quiz PDF
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Download Quiz PDF"):
                with st.spinner("Generating Quiz PDF..."):
                    pdf_buffer = generate_quiz_pdf(st.session_state.quiz_data, "quiz")
                    pdf_filename = f"quiz_{st.session_state.course_data.get('course_title', 'course').replace(' ', '_').lower()}.pdf"
                    
                    st.download_button(
                        label="Download PDF",
                        data=pdf_buffer,
                        file_name=pdf_filename,
                        mime="application/pdf",
                    )
        
        with col2:
            if st.button("Generate New Quiz"):
                if st.session_state.course_data is not None:
                    with st.spinner("Generating new quiz questions..."):
                        quiz_data = generate_quiz_with_groq(st.session_state.course_data, 7)
                    
                    if "error" in quiz_data:
                        st.error(f"Error generating quiz: {quiz_data.get('error')}")
                    else:
                        st.session_state.quiz_data = quiz_data
                        st.session_state.user_answers = [-1] * len(quiz_data.get("questions", []))
                        st.session_state.quiz_submitted = False
                        st.success("New quiz generated!")
                        st.rerun()
                else:
                    st.error("No course data available to generate a quiz.")
        
        # Display the quiz
        display_quiz(st.session_state.quiz_data)

def display_youtube_videos(videos):
    """Display YouTube videos in the Streamlit app."""
    if not videos:
        st.info("No videos available for this topic")
        return
    
    cols = st.columns(min(3, len(videos)))
    for i, video in enumerate(videos):
        with cols[i % len(cols)]:
            st.image(video["thumbnail"], use_container_width=True)
            st.markdown(f"**[{video['title']}]({video['url']})**")
            st.caption(f"By {video['channel']}")
            st.markdown(f"[Watch on YouTube]({video['url']})")

def display_quiz(quiz_data):
    """Display the quiz in the Streamlit app and allow users to take it."""
    st.header(quiz_data.get("quiz_title", "Quiz"))
    st.write(quiz_data.get("quiz_description", ""))
    
    # Initialize user answers in session state if they don't exist
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = [-1] * len(quiz_data.get("questions", []))
    
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    
    # Display each question
    for i, question in enumerate(quiz_data.get("questions", [])):
        st.subheader(f"Question {i+1}")
        st.write(question.get("question", ""))
        
        # Display options as radio buttons
        options = question.get("options", [])
        user_choice = st.radio(
            f"Select your answer for Question {i+1}:",
            options,
            index=st.session_state.user_answers[i] if st.session_state.user_answers[i] >= 0 else 0,
            key=f"q{i}"
        )
        
        # Store the selected option index
        st.session_state.user_answers[i] = options.index(user_choice) if user_choice in options else -1
        
        st.markdown("---")
    
    # Submit button
    if st.button("Submit Quiz", type="primary"):
        st.session_state.quiz_submitted = True
    
    # Show results if submitted
    if st.session_state.quiz_submitted:
        display_quiz_results(quiz_data, st.session_state.user_answers)

def display_quiz_results(quiz_data, user_answers):
    """Display the results of the quiz."""
    questions = quiz_data.get("questions", [])
    correct_count = 0
    
    st.header("Quiz Results")
    
    for i, (question, user_answer) in enumerate(zip(questions, user_answers)):
        correct_answer = question.get("correct_answer", 0)
        is_correct = user_answer == correct_answer
        
        if is_correct:
            correct_count += 1
            st.success(f"Question {i+1}: Correct ✓")
        else:
            st.error(f"Question {i+1}: Incorrect ✗")
        
        st.write(question.get("question", ""))
        st.write(f"Your answer: {question.get('options', [])[user_answer] if 0 <= user_answer < len(question.get('options', [])) else 'Not answered'}")
        st.write(f"Correct answer: {question.get('options', [])[correct_answer] if 0 <= correct_answer < len(question.get('options', [])) else 'Unknown'}")
        st.write(f"Explanation: {question.get('explanation', '')}")
        st.markdown("---")
    
    # Calculate score
    score_percentage = (correct_count / len(questions)) * 100 if questions else 0
    
    # Display overall score with color coding
    if score_percentage >= 80:
        st.success(f"Your Score: {correct_count}/{len(questions)} ({score_percentage:.1f}%)")
    elif score_percentage >= 60:
        st.warning(f"Your Score: {correct_count}/{len(questions)} ({score_percentage:.1f}%)")
    else:
        st.error(f"Your Score: {correct_count}/{len(questions)} ({score_percentage:.1f}%)")
    
    # Add retry button
    if st.button("Retry Quiz"):
        st.session_state.user_answers = [-1] * len(questions)
        st.session_state.quiz_submitted = False
        st.rerun()