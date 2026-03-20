import gradio as gr
import cv2
import pickle
import numpy as np
from deepface import DeepFace
from scipy.spatial.distance import cosine
from datetime import datetime
import pandas as pd
import pytz
import os
import sys

# --- Force UTF-8 for Windows Console ---
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
SESSION_FILE = "session.txt"
USERS_DIR = "Users"

# --- 1. User Authentication Check ---
if not os.path.exists(SESSION_FILE):
    print("🔴 ERROR: No active session. Please run login.py first.")
    sys.exit()

with open(SESSION_FILE, "r") as f:
    CURRENT_USER = f.read().strip()

print(f"[INFO] Current User: {CURRENT_USER}")

# --- Path Setup ---
USER_FOLDER = os.path.join(USERS_DIR, CURRENT_USER)
BASE_IMAGES_FOLDER = os.path.join(USER_FOLDER, "Student_Images")
DB_FILE = os.path.join(USER_FOLDER, "face_database.pkl")
ATTENDANCE_DIR = os.path.join(USER_FOLDER, "Attendance_Sheets")
SUBJECTS_FILE = os.path.join(USER_FOLDER, "subject.txt")

if not os.path.exists(ATTENDANCE_DIR):
    os.makedirs(ATTENDANCE_DIR)

# --- 2. Load Face Database ---
print("[INFO] Loading known face database...")
known_embeddings = np.array([])
known_names = []

try:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'rb') as f:
            database = pickle.load(f)
        known_embeddings = np.array([data["embedding"] for data in database])
        known_names = [data["name"] for data in database]
        print(f"[OK] Face database loaded: {len(known_names)} faces.")
    else:
        print("[WARNING] Database file not found.")
except Exception as e:
    print(f"[ERROR] Loading database: {e}")

# --- 3. HELPER FUNCTIONS ---

def get_subjects():
    """Reads subjects from subject.txt. Creates default if missing."""
    defaults = ["Mathematics", "Physics", "Computer Science", "English", "History"]
    
    if not os.path.exists(SUBJECTS_FILE):
        try:
            with open(SUBJECTS_FILE, "w") as f:
                f.write("\n".join(defaults))
            return defaults
        except Exception as e:
            print(f"Error creating subject file: {e}")
            return defaults
    
    try:
        with open(SUBJECTS_FILE, "r") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines if lines else defaults
    except Exception:
        return defaults

def get_all_students_from_images():
    """Scans images to build Master List."""
    students = []
    if not os.path.exists(BASE_IMAGES_FOLDER):
        return pd.DataFrame(columns=["Roll", "Name", "Year"])

    for root, dirs, files in os.walk(BASE_IMAGES_FOLDER):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Parse Filename
                name_parts = os.path.splitext(file)[0].split('_')
                if len(name_parts) >= 3:
                    roll, year = name_parts[0], name_parts[-1]
                    name = " ".join(name_parts[1:-1])
                else:
                    name = os.path.splitext(file)[0]
                    roll = "00"
                    year = "Unknown"

                # CRITICAL: Convert to String to match Excel
                roll = str(roll).strip()
                name = name.strip()
                year = str(year).strip()

                if not any(s['Name'] == name and s['Roll'] == roll for s in students):
                    students.append({"Roll": roll, "Name": name, "Year": year})

    df = pd.DataFrame(students)
    if not df.empty and "Roll" in df.columns:
        df = df.sort_values(by="Roll")
    return df

def initialize_subject_excel(subject):
    """Loads/Creates Excel and adds Today's Date column."""
    file_path = os.path.join(ATTENDANCE_DIR, f"{subject}.xlsx")
    master_df = get_all_students_from_images()
    
    if master_df.empty:
        return None, "❌ No students found in images."

    if os.path.exists(file_path):
        try:
            # FIX: Force 'Roll' AND 'Year' to be strings during load
            df = pd.read_excel(file_path, dtype={'Roll': str, 'Year': str})
            
            # Extra Safety: Explicitly convert columns to string (handles mixed types)
            df['Roll'] = df['Roll'].astype(str)
            df['Year'] = df['Year'].astype(str)
            df.columns = df.columns.astype(str)
            
            # Now the merge will work because both are strings
            df = pd.merge(master_df, df, on=["Roll", "Name", "Year"], how="left")
        except Exception as e:
            return None, f"Error reading Excel: {e}"
    else:
        df = master_df.copy()
        df["Total Present"] = 0

    IST = pytz.timezone('Asia/Kolkata')
    today_str = datetime.now(IST).strftime('%Y-%m-%d')
    
    if today_str not in df.columns:
        df[today_str] = "" 
        
    df.fillna("", inplace=True)
    return df, f"✅ Sheet Loaded: {subject}"

# --- 4. GLOBAL STATE ---
current_df = None
current_subject = ""
stop_stream = False

# --- 5. CORE LOGIC ---

def get_dropdown_lists():
    """Returns (List of Absent Students, List of Present Students) for dropdowns."""
    global current_df
    if current_df is None: return [], []
    
    IST = pytz.timezone('Asia/Kolkata')
    today_str = datetime.now(IST).strftime('%Y-%m-%d')

    if today_str not in current_df.columns: return [], []

    present_mask = current_df[today_str] == "Present"
    present_list = current_df[present_mask]['Name'].tolist()
    
    absent_mask = current_df[today_str] != "Present"
    absent_list = current_df[absent_mask]['Name'].tolist()
    
    return absent_list, present_list

def start_attendance(subject_choice):
    global current_df, current_subject, stop_stream
    
    if not subject_choice:
        yield None, pd.DataFrame(), "⚠️ Select a subject first.", gr.update(), gr.update()
        return

    stop_stream = False
    current_subject = subject_choice
    
    # Init DataFrame
    current_df, msg = initialize_subject_excel(subject_choice)
    if current_df is None:
        yield None, pd.DataFrame(), msg, gr.update(), gr.update()
        return

    IST = pytz.timezone('Asia/Kolkata')
    today_str = datetime.now(IST).strftime('%Y-%m-%d')
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        yield None, current_df, "❌ Error: Webcam failed.", gr.update(), gr.update()
        return

    print("📷 Camera Started. Waiting for faces...")

    while not stop_stream:
        ret, frame = cap.read()
        if not ret: break
        
        try:
            faces = DeepFace.extract_faces(frame, detector_backend='opencv', enforce_detection=False)
            
            for face in faces:
                if face['confidence'] > 0:
                    x, y, w, h = face['facial_area']['x'], face['facial_area']['y'], face['facial_area']['w'], face['facial_area']['h']
                    
                    detected_name = "Unknown"
                    if len(known_embeddings) > 0:
                        face_crop = frame[y:y+h, x:x+w]
                        vec = DeepFace.represent(face_crop, model_name="VGG-Face", enforce_detection=False)[0]["embedding"]
                        dists = [cosine(vec, k) for k in known_embeddings]
                        if dists:
                            idx = np.argmin(dists)
                            if dists[idx] < 0.55:
                                detected_name = known_names[idx]
                    
                    color = (0, 255, 0) if detected_name != "Unknown" else (0, 0, 255)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(frame, detected_name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    
                    if detected_name != "Unknown":
                        clean_detected = detected_name.strip().lower()
                        
                        def check_match(excel_name):
                            excel_name = str(excel_name).strip().lower()
                            return (clean_detected in excel_name) or (excel_name in clean_detected)

                        mask = current_df['Name'].apply(check_match)
                        
                        if mask.any():
                            if not (current_df.loc[mask, today_str] == "Present").all():
                                print(f"✅ MATCH FOUND! Marking {detected_name} as Present.")
                                current_df.loc[mask, today_str] = "Present"

            view_cols = ["Roll", "Name", "Year", today_str]
            detected_df = current_df[current_df[today_str] == "Present"][view_cols]
            
            yield cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), detected_df, f"📷 Live: {subject_choice}", gr.update(), gr.update()
            
        except Exception as e:
            pass

    cap.release()
    
    view_cols = ["Roll", "Name", "Year", today_str]
    final_view = current_df[current_df[today_str] == "Present"][view_cols] if current_df is not None else pd.DataFrame()
    
    absent_list, present_list = get_dropdown_lists()
    
    yield None, final_view, "🛑 Camera Stopped.", gr.Dropdown(choices=absent_list), gr.Dropdown(choices=present_list)

def stop_camera_action():
    global stop_stream
    stop_stream = True
    return "🛑 Stopping Camera..."

def save_attendance_action():
    global current_df, current_subject
    if current_df is None or current_subject == "":
        return "⚠️ No data to save."

    metadata_cols = ["Roll", "Name", "Year", "Total Present"]
    date_cols = [c for c in current_df.columns if c not in metadata_cols]

    current_df["Total Present"] = (current_df[date_cols] == "Present").sum(axis=1)
    
    save_path = os.path.join(ATTENDANCE_DIR, f"{current_subject}.xlsx")
    
    try:
        current_df.to_excel(save_path, index=False)
        return f"✅ Saved {current_subject}.xlsx!"
    except PermissionError:
        return "❌ ERROR: Excel file is OPEN! Close it and try saving again."
    except Exception as e:
        return f"❌ Save Failed: {e}"

def refresh_lists():
    """Manual trigger to update dropdowns."""
    absent, present = get_dropdown_lists()
    return gr.Dropdown(choices=absent, value=None), gr.Dropdown(choices=present, value=None)

def refresh_subjects_ui():
    """Reloads subjects from file."""
    subs = get_subjects()
    return gr.Dropdown(choices=subs, value=None)

# --- MANUAL CONTROLS ---

def manual_entry(student_name):
    global current_df
    if current_df is None: return pd.DataFrame(), "⚠️ Load a subject first.", gr.update(), gr.update()
    if not student_name: return pd.DataFrame(), "⚠️ Select a student.", gr.update(), gr.update()

    IST = pytz.timezone('Asia/Kolkata')
    today_str = datetime.now(IST).strftime('%Y-%m-%d')
    
    current_df.loc[current_df['Name'] == student_name, today_str] = "Present"
    
    view_cols = ["Roll", "Name", "Year", today_str]
    detected_df = current_df[current_df[today_str] == "Present"][view_cols]
    
    absent_list, present_list = get_dropdown_lists()
    
    return detected_df, f"✅ Marked '{student_name}' Present.", gr.Dropdown(choices=absent_list, value=None), gr.Dropdown(choices=present_list, value=None)

def delete_student(student_name):
    global current_df
    if current_df is None: return pd.DataFrame(), "⚠️ Load a subject first.", gr.update(), gr.update()
    if not student_name: return pd.DataFrame(), "⚠️ Select a student.", gr.update(), gr.update()

    IST = pytz.timezone('Asia/Kolkata')
    today_str = datetime.now(IST).strftime('%Y-%m-%d')

    current_df.loc[current_df['Name'] == student_name, today_str] = ""
    
    view_cols = ["Roll", "Name", "Year", today_str]
    detected_df = current_df[current_df[today_str] == "Present"][view_cols]
    
    absent_list, present_list = get_dropdown_lists()
    
    return detected_df, f"🗑️ Unmarked '{student_name}'.", gr.Dropdown(choices=absent_list, value=None), gr.Dropdown(choices=present_list, value=None)

# --- 6. GRADIO UI ---
with gr.Blocks(theme=gr.themes.Soft(), title="Attendance System") as app:
    gr.Markdown(f"# 📚 Smart Attendance Register (User: {CURRENT_USER})")
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Row():
                subject_drop = gr.Dropdown(
                    choices=get_subjects(), 
                    label="1. Select Subject", 
                    allow_custom_value=True,
                    scale=4
                )
                refresh_sub_btn = gr.Button("🔄", scale=1, min_width=10)

            start_btn = gr.Button("2. ▶️ Start Camera", variant="primary")
            
            with gr.Row():
                stop_btn = gr.Button("3. 🛑 Stop Camera", variant="secondary")
                save_btn = gr.Button("4. 💾 Save Excel", variant="primary")
            
            status_txt = gr.Textbox(label="System Status", interactive=False)

            gr.Markdown("### 🛠️ Manual Corrections")
            refresh_btn = gr.Button("🔄 Refresh Student Lists")
            
            with gr.Tab("Manual Entry"):
                manual_drop = gr.Dropdown(label="Mark Absent Student as Present", choices=[], interactive=True)
                manual_btn = gr.Button("Mark Present")
            
            with gr.Tab("Delete Attendance"):
                del_drop = gr.Dropdown(label="Unmark Present Student", choices=[], interactive=True)
                del_btn = gr.Button("Unmark (Remove)", variant="stop")

        with gr.Column(scale=2):
            camera_view = gr.Image(label="Live Feed")
            gr.Markdown("### 📋 Detected Students (Present Only)")
            data_view = gr.Dataframe(label="Live Register", interactive=False)

    # --- Event Linking ---
    start_event = start_btn.click(
        fn=start_attendance,
        inputs=[subject_drop],
        outputs=[camera_view, data_view, status_txt, manual_drop, del_drop]
    )

    stop_btn.click(fn=stop_camera_action, inputs=None, outputs=status_txt)
    save_btn.click(fn=save_attendance_action, inputs=None, outputs=status_txt)
    
    manual_btn.click(fn=manual_entry, inputs=[manual_drop], outputs=[data_view, status_txt, manual_drop, del_drop])
    del_btn.click(fn=delete_student, inputs=[del_drop], outputs=[data_view, status_txt, manual_drop, del_drop])
    
    refresh_btn.click(fn=refresh_lists, inputs=None, outputs=[manual_drop, del_drop])
    refresh_sub_btn.click(fn=refresh_subjects_ui, inputs=None, outputs=subject_drop)

if __name__ == "__main__":
    app.queue().launch()