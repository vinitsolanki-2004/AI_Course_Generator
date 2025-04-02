import streamlit as st
import json
import requests
from services.search import search_youtube_videos
from services.get_env import GROQ_API_KEY, GOOGLE_API_KEY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListItem, ListFlowable, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
import urllib.request

def generate_course_with_groq(topic, search_content, include_videos=False):
    """Generate a course using Groq API."""
    
    # Format instructions for JSON structure
    format_instructions = """
    {
        "course_title": "string",
        "description": "string",
        "learning_objectives": ["string", "string", ...],
        "introduction": "string",
        "main_topics": [
            {
                "title": "string",
                "content": "string",
                "subtopics": [
                    {
                        "title": "string",
                        "content": "string",
                        "examples": ["string", "string", ...],
                        "video_search_query": "string"
                    },
                    ...
                ],
                "video_search_query": "string"
            },
            ...
        ],
        "summary": "string",
        "key_takeaways": ["string", "string", ...]
    }
    """
    
    video_instruction = """
    For each topic and subtopic, please include a "video_search_query" field containing an optimized search query for finding 
    relevant instructional videos on YouTube. Make this query specific and include the most important keywords.
    """ if include_videos else ""
    
    # Course generation template
    COURSE_GENERATION_TEMPLATE = f"""
    You are an expert educational content creator. Your task is to create a comprehensive course on the topic: {topic}.

    Here is some additional information from Google Search:
    {search_content}

    Please create a structured course with the following components:
    1. Course Title
    2. Description (1-2 paragraphs)
    3. Learning Objectives (3-5 bullet points)
    4. Introduction (3-4 paragraphs)
    5. Main Topics (3-5 topics with subtopics)
       - For each topic, provide:
         - Title
         - Content (2-3 paragraphs)
         - Subtopics (5 - 6 per topic)
           - For each subtopic, provide:
             - Title
             - Content (1-2 paragraphs)
             - Examples (if applicable)
    6. Summary (1 paragraph)
    7. Key Takeaways (3-5 bullet points)
    
    {video_instruction}

    Format your response as a JSON object with the following structure:
    {format_instructions}

    Make sure the content is educational, accurate, and engaging.
    """
    
    try:
        # Set up Groq API request
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-70b-8192",  # Using Llama 3 70B model
            "messages": [
                {"role": "system", "content": "You are an expert educational content creator."},
                {"role": "user", "content": COURSE_GENERATION_TEMPLATE}
            ],
            "temperature": 0.7,
            "max_tokens": 8000,
            "top_p": 0.9
        }
        
        # Make API request
        with st.spinner("Generating course content..."):
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
        
        # Process the response
        if response.status_code == 200:
            response_data = response.json()
            course_content = response_data["choices"][0]["message"]["content"]
            
            # Extract JSON content (handle potential issues with JSON formatting)
            try:
                # Try to find JSON object in the response
                json_start = course_content.find("{")
                json_end = course_content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_content = course_content[json_start:json_end]
                    course_data = json.loads(json_content)
                else:
                    # If no JSON object found, try to parse the entire response
                    course_data = json.loads(course_content)
                
                # Fetch YouTube videos if requested
                if include_videos and GOOGLE_API_KEY:
                    st.info("Fetching YouTube videos for topics and subtopics...")
                    progress_bar = st.progress(0)
                    
                    # Track progress for progress bar
                    total_items = len(course_data.get("main_topics", []))
                    current_item = 0
                    
                    # Fetch videos for main topics
                    for topic in course_data.get("main_topics", []):
                        if "video_search_query" in topic:
                            topic["videos"] = search_youtube_videos(topic["video_search_query"])
                        else:
                            # If no specific query provided, use the topic title
                            topic["videos"] = search_youtube_videos(f"{course_data['course_title']} {topic['title']} tutorial")
                        
                        # Fetch videos for subtopics
                        for subtopic in topic.get("subtopics", []):
                            if "video_search_query" in subtopic:
                                subtopic["videos"] = search_youtube_videos(subtopic["video_search_query"])
                            else:
                                # If no specific query provided, use the subtopic title
                                subtopic["videos"] = search_youtube_videos(f"{topic['title']} {subtopic['title']} tutorial")
                        
                        # Update progress
                        current_item += 1
                        progress_bar.progress(current_item / total_items)
                    
                    progress_bar.empty()
                    st.success("YouTube videos added to course content!")
                
                return course_data
            except json.JSONDecodeError:
                st.warning("Failed to parse JSON response. Returning raw text.")
                return {"error": "JSON parsing failed", "raw_content": course_content}
        else:
            st.error(f"Error: Received status code {response.status_code} from Groq API")
            return {"error": f"API error: {response.status_code}", "details": response.text}
    
    except Exception as e:
        st.error(f"Error generating course: {e}")
        return {"error": str(e)}
    
def generate_quiz_with_groq(course_data, quiz_count=7):
    """Generate a quiz based on the course content using Groq API."""
    
    # Format instructions for JSON structure
    format_instructions = """
    {
        "quiz_title": "string",
        "quiz_description": "string",
        "questions": [
            {
                "question": "string",
                "options": ["string", "string", "string", "string"],
                "correct_answer": "number (0-3, representing the index of the correct option)",
                "explanation": "string"
            },
            ...
        ]
    }
    """
    
    # Extract main content from course data to help generate relevant questions
    course_content = f"""
    Course Title: {course_data.get('course_title', '')}
    
    Description: {course_data.get('description', '')}
    
    Main Topics:
    """
    
    for topic in course_data.get('main_topics', []):
        course_content += f"\n- {topic.get('title', '')}: {topic.get('content', '')}"
        for subtopic in topic.get('subtopics', []):
            course_content += f"\n  * {subtopic.get('title', '')}: {subtopic.get('content', '')}"
    
    # Quiz generation template
    QUIZ_GENERATION_TEMPLATE = f"""
    You are an expert educational quiz creator. Your task is to create a comprehensive quiz for the following course content:
    
    {course_content}
    
    Please create a quiz with {quiz_count} multiple-choice questions that:
    1. Cover the key concepts from the course
    2. Range from basic to advanced difficulty
    3. Include specific, clear questions
    4. Have 4 answer options per question with only one correct answer
    5. Include brief explanations for why the correct answer is right
    
    Format your response as a JSON object with the following structure:
    {format_instructions}
    
    Make sure the questions test understanding rather than just memorization.
    """
    
    try:
        # Set up Groq API request
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-70b-8192",  # Using Llama 3 70B model
            "messages": [
                {"role": "system", "content": "You are an expert educational assessment creator."},
                {"role": "user", "content": QUIZ_GENERATION_TEMPLATE}
            ],
            "temperature": 0.7,
            "max_tokens": 2500,
            "top_p": 0.9
        }
        
        # Make API request
        with st.spinner("Generating quiz questions..."):
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
        
        # Process the response
        if response.status_code == 200:
            response_data = response.json()
            quiz_content = response_data["choices"][0]["message"]["content"]
            
            # Extract JSON content
            try:
                # Try to find JSON object in the response
                json_start = quiz_content.find("{")
                json_end = quiz_content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_content = quiz_content[json_start:json_end]
                    quiz_data = json.loads(json_content)
                else:
                    # If no JSON object found, try to parse the entire response
                    quiz_data = json.loads(quiz_content)
                
                return quiz_data
            except json.JSONDecodeError:
                st.warning("Failed to parse JSON response for quiz. Returning raw text.")
                return {"error": "JSON parsing failed", "raw_content": quiz_content}
        else:
            st.error(f"Error: Received status code {response.status_code} from Groq API")
            return {"error": f"API error: {response.status_code}", "details": response.text}
    
    except Exception as e:
        st.error(f"Error generating quiz: {e}")
        return {"error": str(e)}
    
def generate_pdf(course_data, topic):
    """Generate a PDF document from the course data."""
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading1_style = styles['Heading1']
    heading2_style = styles['Heading2']
    heading3_style = styles['Heading3']
    normal_style = styles['Normal']
    
    # Create a list to hold the PDF elements
    elements = []
    
    # Add course title
    elements.append(Paragraph(course_data.get("course_title", "Course"), title_style))
    elements.append(Spacer(1, 0.25 * inch))
    
    # Add description
    elements.append(Paragraph("Description", heading1_style))
    elements.append(Paragraph(course_data.get("description", ""), normal_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Add learning objectives
    elements.append(Paragraph("Learning Objectives", heading1_style))
    objectives = []
    for obj in course_data.get("learning_objectives", []):
        objectives.append(ListItem(Paragraph(obj, normal_style)))
    
    if objectives:
        elements.append(ListFlowable(objectives, bulletType='bullet'))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Add introduction
    elements.append(Paragraph("Introduction", heading1_style))
    elements.append(Paragraph(course_data.get("introduction", ""), normal_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Add main topics
    elements.append(Paragraph("Main Topics", heading1_style))
    
    for i, topic in enumerate(course_data.get("main_topics", []), 1):
        # Topic title and content
        elements.append(Paragraph(f"{i}. {topic.get('title', 'Topic')}", heading2_style))
        elements.append(Paragraph(topic.get("content", ""), normal_style))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Add thumbnails for topic videos if available
        if "videos" in topic and topic["videos"]:
            elements.append(Paragraph("Topic Videos:", heading3_style))
            for video in topic["videos"][:2]:  # Limit to 2 videos to save space
                try:
                    # Add video title and URL
                    elements.append(Paragraph(f"- {video['title']}", normal_style))
                    elements.append(Paragraph(f"  Link: {video['url']}", normal_style))
                    
                    # Try to add thumbnail image (with error handling)
                    try:
                        image_data = urllib.request.urlopen(video["thumbnail"]).read()
                        img = Image(BytesIO(image_data), width=2*inch, height=1.5*inch)
                        elements.append(img)
                    except Exception:
                        # Skip image if there's an error
                        pass
                except Exception:
                    # Skip video if there's an error
                    pass
                elements.append(Spacer(1, 0.1 * inch))
        
        # Add subtopics
        for j, subtopic in enumerate(topic.get("subtopics", []), 1):
            elements.append(Paragraph(f"{i}.{j} {subtopic.get('title', 'Subtopic')}", heading3_style))
            elements.append(Paragraph(subtopic.get("content", ""), normal_style))
            
            # Add examples
            examples = subtopic.get("examples", [])
            if examples:
                elements.append(Paragraph("Examples:", heading3_style))
                example_items = []
                for example in examples:
                    example_items.append(ListItem(Paragraph(example, normal_style)))
                
                if example_items:
                    elements.append(ListFlowable(example_items, bulletType='bullet'))
            
            # Add subtopic videos (just links, no thumbnails to save space)
            if "videos" in subtopic and subtopic["videos"]:
                elements.append(Paragraph("Related Videos:", heading3_style))
                for video in subtopic["videos"][:1]:  # Limit to 1 video per subtopic
                    elements.append(Paragraph(f"- {video['title']}: {video['url']}", normal_style))
            
            elements.append(Spacer(1, 0.15 * inch))
    
    # Add summary
    elements.append(Paragraph("Summary", heading1_style))
    elements.append(Paragraph(course_data.get("summary", ""), normal_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Add key takeaways
    elements.append(Paragraph("Key Takeaways", heading1_style))
    takeaways = []
    for takeaway in course_data.get("key_takeaways", []):
        takeaways.append(ListItem(Paragraph(takeaway, normal_style)))
    
    if takeaways:
        elements.append(ListFlowable(takeaways, bulletType='bullet'))
    
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_quiz_pdf(quiz_data, topic):
    """Generate a PDF document from the quiz data."""
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading1_style = styles['Heading1']
    heading2_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create a list to hold the PDF elements
    elements = []
    
    # Add quiz title
    elements.append(Paragraph(quiz_data.get("quiz_title", "Quiz"), title_style))
    elements.append(Spacer(1, 0.25 * inch))
    
    # Add description
    elements.append(Paragraph(quiz_data.get("quiz_description", ""), normal_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Add questions
    for i, question in enumerate(quiz_data.get("questions", []), 1):
        elements.append(Paragraph(f"Question {i}", heading1_style))
        elements.append(Paragraph(question.get("question", ""), normal_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Add options
        elements.append(Paragraph("Options:", heading2_style))
        options = question.get("options", [])
        for j, option in enumerate(options):
            if j == question.get("correct_answer", 0):
                elements.append(Paragraph(f"{chr(65+j)}. {option} (CORRECT)", normal_style))
            else:
                elements.append(Paragraph(f"{chr(65+j)}. {option}", normal_style))
        
        elements.append(Spacer(1, 0.1 * inch))
        
        # Add explanation
        elements.append(Paragraph("Explanation:", heading2_style))
        elements.append(Paragraph(question.get("explanation", ""), normal_style))
        elements.append(Spacer(1, 0.2 * inch))
    
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer