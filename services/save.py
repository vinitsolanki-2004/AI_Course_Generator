import json

def save_course_to_file(course_data, topic):
    """Save the generated course to a file."""
    # Create a sanitized filename
    filename = f"{topic.replace(' ', '_').lower()}_course.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(course_data, f, indent=2)
    
    return filename

def save_quiz_to_file(quiz_data, topic):
    """Save the generated quiz to a file."""
    # Create a sanitized filename
    filename = f"{topic.replace(' ', '_').lower()}_quiz.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(quiz_data, f, indent=2)
    
    return filename

