# 🎓 Educational Course Generator

An AI-powered application that generates comprehensive, structured educational courses on any topic along with quizzes and supporting materials.

## 🌟 Features

- **AI-Generated Course Content**: Creates detailed courses using Groq API with Llama 3 70B model
- **Structured Course Format**: Includes title, description, learning objectives, introduction, main topics, subtopics, examples, summary, and key takeaways
- **Google Search Integration**: Enriches content with relevant information from web searches
- **YouTube Video Integration**: Embeds related instructional videos for topics and subtopics
- **Interactive Quiz Generation**: Creates multiple-choice questions to test knowledge
- **PDF Export**: Download courses and quizzes for offline reading
- **Streamlit UI**: User-friendly interface for course generation and interaction

## 📋 Requirements

- Python 3.7+
- Groq API Key
- Google API Key (for YouTube and Search functionality)
- Google Custom Search Engine ID (for Search functionality)

## 🛠️ Installation

1. Clone the repository:
   ```
   git clone https://github.com/vinitsolanki-2004/AI_Course_Generator/
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   GROQ_API_KEY=your_groq_api_key
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_CSE_ID=your_google_custom_search_engine_id
   ```

## 🚀 Usage

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Enter a course topic in the input field
3. Configure options:
   - Toggle Google Search integration for additional context
   - Enable YouTube video integration for visual learning content
   - Adjust advanced settings like temperature and token count
   - Enable quiz generation
4. Click "Generate Course" to create your educational content
5. Navigate between course content and quiz using the tabs
6. Download content as PDF for offline use

## 📊 Advanced Options

- **Temperature**: Controls the creativity/randomness of the generated content (0.0-1.0)
- **Max Tokens**: Limits the length of the generated content
- **Videos Per Topic**: Sets the number of YouTube videos to fetch per topic
- **Quiz Questions**: Configures the number of questions to generate

## 📱 User Interface

The application has three main views:
1. **Course Generator**: Enter topic and configure generation settings
2. **Course View**: Browse the generated course content with expandable topics
3. **Quiz**: Take the generated quiz and see your results

## 🔄 Workflow

1. Enter your topic and configure options
2. The app fetches relevant information from Google (if enabled)
3. The Groq API generates structured course content
4. YouTube videos are fetched and integrated (if enabled)
5. Quiz questions are generated based on course content (if enabled)
6. Course and quiz are saved as JSON files locally
7. PDF export options allow you to save content for offline use

## 🛑 Limitations

- Requires valid API keys for full functionality
- Content quality depends on the AI model's knowledge and limitations
- YouTube integration requires Google API key with YouTube Data API v3 enabled
- Search integration requires Google API key with Custom Search API enabled

## 🧩 Architecture

The application follows a modular design with components for:
- Course generation
- Quiz generation
- PDF export
- User interface
- External API integrations (Groq, Google Search, YouTube)

See the architecture diagram for a visual representation of the system components.


