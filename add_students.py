# add_students_app.py (Version 2.1 with Year Subfolders)

import gradio as gr
import os
import shutil
import re # Import regular expressions for cleaning filenames
import sys
# --- Constants ---
#BASE_IMAGES_FOLDER = "Student_Images" # Base folder for all student images

# --- Ensure Base Folder Exists ---
#if not os.path.exists(BASE_IMAGES_FOLDER):
#    os.makedirs(BASE_IMAGES_FOLDER)
#    print(f"Created base folder: {BASE_IMAGES_FOLDER}")

# --- DYNAMIC USER CONFIGURATION ---
sys.stdout.reconfigure(encoding='utf-8')

SESSION_FILE = "session.txt"
USERS_DIR = "Users"

# Read the current user from the session file
if not os.path.exists(SESSION_FILE):
    print("🔴 ERROR: No active session. Please run login.py first.")
    sys.exit()

with open(SESSION_FILE, "r") as f:
    CURRENT_USER = f.read().strip()

print(f"[INFO] Current User: {CURRENT_USER}")

# Define User-Specific Paths
USER_FOLDER = os.path.join(USERS_DIR, CURRENT_USER)
BASE_IMAGES_FOLDER = os.path.join(USER_FOLDER, "Student_Images")
DB_FILE = os.path.join(USER_FOLDER, "face_database.pkl")
MODEL_NAME = "VGG-Face"

# Ensure the user's image folder exists
if not os.path.exists(BASE_IMAGES_FOLDER):
    os.makedirs(BASE_IMAGES_FOLDER)
# ----------------------------------

# --- Helper Function to Sanitize Filenames ---
def sanitize_filename(name):
    """Removes characters that are problematic in filenames."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name

# --- Function to Save and Rename Uploaded Image ---
def save_and_rename_student_image(uploaded_file, student_name, roll_number, admission_year):
    # --- Input Validation ---
    if uploaded_file is None:
        return "❌ Error: Please upload an image file."
    if not student_name:
        return "❌ Error: Please enter the student's name."
    if not roll_number:
        return "❌ Error: Please enter the roll number."
    if not admission_year or not admission_year.isdigit() or len(admission_year) != 4:
        return "❌ Error: Please enter a valid 4-digit admission year."

    try:
        # --- Create Year-Specific Subfolder ---
        #year_folder_path = os.path.join(BASE_IMAGES_FOLDER, admission_year)
        #os.makedirs(year_folder_path, exist_ok=True) # Creates the folder if it doesn't exist

        # --- Construct the New Filename ---
        s_name = sanitize_filename(student_name)
        s_roll = sanitize_filename(roll_number)

        original_filename = os.path.basename(uploaded_file.name)
        _, file_extension = os.path.splitext(original_filename)
        file_extension = file_extension.lower()

        # New filename no longer needs the year, as it's in the folder name
        new_filename = f"{s_roll}_{s_name}_{admission_year}{file_extension}"
        # Destination path is now INSIDE the year folder
        destination_path = os.path.join(BASE_IMAGES_FOLDER, new_filename)

        # --- Save the File ---
        shutil.copyfile(uploaded_file.name, destination_path)
        print(f"📸 Saved and renamed: {destination_path}")

        return (f"✅ Success! Image saved as '{new_filename}' inside the Student_Images folder.")

    except Exception as e:
        error_message = f"❌ Error saving file: {e}"
        print(error_message)
        return error_message

# --- Gradio UI ---
with gr.Blocks(theme=gr.themes.Soft(), title="Add Students") as iface_add_students:
    gr.Markdown("# ➕ Add New Student Photo")
    gr.Markdown("Enter details and upload **one** photo. It will be saved in a folder named after the admission year.")

    with gr.Row():
        student_name_input = gr.Textbox(label="Student Full Name")
        roll_number_input = gr.Textbox(label="Roll Number")
        admission_year_input = gr.Textbox(label="Admission Year (e.g., 2024)") # Used for folder name

    image_upload = gr.File(
        label="Upload Student Photo",
        file_count="single",
        file_types=["image"]
    )
    upload_button = gr.Button("Save New Student Image", variant="primary")
    upload_status = gr.Textbox(label="Status", interactive=False)
    gr.Markdown("⚠️ **After saving, you MUST run `encode_faces.py` again and RESTART the main attendance application.**")

    upload_button.click(
        fn=save_and_rename_student_image,
        inputs=[image_upload, student_name_input, roll_number_input, admission_year_input],
        outputs=[upload_status]
    )

print("[INFO] Launching Add Students UI...")
iface_add_students.launch()