# Sunny-Side-Burrow-School
group 3 WebSys IT32S2

A modern Django-based school enrollment and school web system.

Key Features

**Role-Based Access Control**: Secure multi-role login and registration for Administrators, Teachers, and Students.
**Smart Scheduling System**: Automated, conflict-free class schedule generation with grade-specific time constraints and standardized recess periods.
**Teacher Dashboard**: Tools for teachers to apply for subject/advisory roles (with strict overlap validation) and view their assigned sections, student rosters, and schedules.
**Student Enrollment & Finance**: Online enrollment tracking, tuition fee management, and an intelligent **OCR Payment Scanner** for automated receipt verification via Reference IDs.
**AI Assistance**: Built-in AI tools powered by Google Gemini and Anthropic Claude specifically designed to assist teachers.
**Administrator Portal**: Comprehensive dashboard to manage school years, subjects, approve enrollments, track financial collections, and manage user accounts.
**Support Ticketing System**: Integrated concern ticketing for students and teachers to seamlessly communicate with the administration.

STEPS FOR INSTALLATION

1. Download the Zipfile
2. Extract it for your computer
3. Open your terminal or command prompt and navigate into the extracted folder
4. Setup a Virtual Environment

python -m venv .venv

5. Activate the environment so that packages install correctly

.venv\Scripts\activate

6. Install Project Dependecies

pip install -r requirements.txt

7. Configure the Environment Variables (The project requires a `.env` file to securely store passwords and API keys)
  
    1. In the root directory (where `manage.py` is), create a new file named exactly `.env`.
    2. Open the `.env` file and paste the following configuration, replacing the placeholders with your actual keys:

    ```ini
    DJANGO_SECRET_KEY=generate-a-long-random-secret-key-here
    DEBUG=True
    ALLOWED_HOSTS=127.0.0.1,localhost

    Setup For GMail:
    
    EMAIL_HOST=smtp.gmail.com
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=587
    EMAIL_USE_TLS=True
    EMAIL_USE_SSL=False
    EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
    EMAIL_HOST_USER=your_email@gmail.com
    EMAIL_HOST_PASSWORD=your_16_character_app_password
    DEFAULT_FROM_EMAIL=your_email@gmail.com

    AI API Keys:

    GEMINI_API_KEY=your_gemini_api_key_here
    ANTHROPIC_API_KEY=your_anthropic_api_key_here

6. Initialize the Database

python manage.py migrate

8. Create an Admin Account

python manage.py createsuperuser

9. Run the Server

python manage.py runserver and open it to `http://127.0.0.1:8000`



