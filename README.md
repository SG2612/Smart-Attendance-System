Smart Attendance System 🎓📸
Python, OpenCV, DeepFace, Gradio
An AI-powered, real-time automated face recognition attendance system designed for modern educational environments. Unlike traditional biometric systems that process users one by one, this system accurately detects, identifies, and logs attendance for both single individuals and large groups of students simultaneously in a single image or camera frame.
✨ Features
 * 👥 Group Attendance Detection: Recognizes multiple student faces concurrently within classroom photos or live streams.
 * ⚡ Real-Time Facial Recognition: Utilizes deep learning facial embeddings to ensure high accuracy and low latency.
 * 💻 Interactive Gradio Web Interface: Clean, easy-to-use web UI for camera feeds, image uploads, and dataset management.
 * 📊 Automated Excel Logging: Automatically records student ID, name, date, and exact entry timestamp into organized .xlsx sheets.
 * 🔄 Duplicate Prevention: Prevents double-marking attendance for the same student within a configurable time window.
 * 📁 Dataset Management: Streamlined onboarding flow to enroll new students into the facial database.
🛠️ Tech Stack
 * Core Language: Python
 * Computer Vision: OpenCV
 * Facial Recognition Engine: DeepFace
 * Frontend / Interface: Gradio
 * Data & Export Engine: Pandas, OpenPyXL (Excel integration)
📂 Project Structure
Smart-Attendance-System/
│
├── dataset/                    # Known student face images (stored as ID_Name.jpg)
├── attendance_logs/             # Exported Excel/CSV attendance logs
├── src/
│   ├── face_recognizer.py      # Multi-face detection & extraction logic
│   ├── attendance_manager.py   # Excel logger & timestamp tracker
│   └── utils.py                # Helper functions for image processing
│
├── app.py                      # Main Gradio application interface
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation

🚀 Getting Started
Prerequisites
Ensure you have Python 3.9 or higher installed on your machine.
Installation
 * Clone the Repository
   git clone https://github.com/your-username/Smart-Attendance-System.git
cd Smart-Attendance-System

 * Create and Activate a Virtual Environment
   * Windows:
     python -m venv venv
venv\Scripts\activate

   * Linux/macOS:
     python3 -m venv venv
source venv/bin/activate

 * Install Dependencies
   pip install -r requirements.txt

📸 Adding Student Data
Before running the attendance system, add reference photos of registered students to the dataset/ directory.
 * Naming Convention: StudentID_StudentName.jpg (e.g., 101_JohnDoe.jpg, 102_JaneSmith.jpg)
 * For best results, use clear, well-lit frontal portraits.
🏃 Usage
Launch the Gradio web application by running:
python app.py

Once executed, open your terminal's local web URL (typically [http://127.0.0.1:7860](http://127.0.0.1:7860)).
Modes of Operation:
 * Single User Mode: Scans individual student face via webcam or image upload for instant verification.
 * Group Mode: Upload a full classroom image or capture a wide-angle frame to mark attendance for all detected students at once.
 * Log Viewer: View and download updated Excel attendance reports directly from the web interface.
📄 Example Attendance Output
Log files are stored inside attendance_logs/ formatted as Attendance_YYYY-MM-DD.xlsx:
| Student ID | Student Name | Date | Time | Status |
|---|---|---|---|---|
| 101 | John Doe | 2026-09-07 | 09:15:02 | Present |
| 102 | Jane Smith | 2026-09-07 | 09:15:03 | Present |
| 105 | Alex Turner | 2026-09-07 | 09:15:03 | Present |

