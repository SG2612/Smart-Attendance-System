# encode_face.py (Version 4.0 - Flat Folder Structure)

import gradio as gr
from deepface import DeepFace
import os
import pickle
import sys

# --- CRITICAL FIX: Force UTF-8 encoding ---
sys.stdout.reconfigure(encoding='utf-8')

# --- DYNAMIC USER CONFIGURATION ---
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
OUTPUT_DB_FILE = os.path.join(USER_FOLDER, "face_database.pkl")
MODEL_NAME = "VGG-Face"

# Ensure the user's image folder exists
if not os.path.exists(BASE_IMAGES_FOLDER):
    os.makedirs(BASE_IMAGES_FOLDER)

# --- Function to Run Encoding ---
def run_encoding():
    """
    Scans the 'Student_Images' folder (flat structure), encodes all found
    images, and saves the results to face_database.pkl.
    """
    database = []
    processed_count = 0
    error_count = 0
    status_message = "[INFO] Initializing... This may take a moment.\n"

    if not os.path.exists(BASE_IMAGES_FOLDER):
        return f"❌ Error: The folder '{BASE_IMAGES_FOLDER}' was not found."

    status_message += f"[INFO] Scanning images in '{BASE_IMAGES_FOLDER}'...\n"

    # Iterate through files in the base folder
    files = os.listdir(BASE_IMAGES_FOLDER)
    
    if not files:
         status_message += f"[WARNING] No files found in {BASE_IMAGES_FOLDER}.\n"

    for filename in files:
        # Skip directories, process only files
        image_path = os.path.join(BASE_IMAGES_FOLDER, filename)
        if not os.path.isfile(image_path):
            continue

        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            # Use the filename (without extension) as the student name
            # Example: "Souvik_Gorai.jpg" -> "Souvik Gorai"
            student_name = os.path.splitext(filename)[0].replace("_", " ")
            
            status_message += f"  Encoding '{filename}' as '{student_name}'...\n"

            try:
                # Encode the face
                embedding_objs = DeepFace.represent(
                    img_path=image_path,
                    model_name=MODEL_NAME,
                    enforce_detection=True # Ensure a face is actually there
                )
                
                # Add to database
                database.append({
                    "name": student_name, 
                    "embedding": embedding_objs[0]["embedding"]
                })
                processed_count += 1
                status_message += f"    ✅ Encoded.\n"
            except Exception as e:
                status_message += f"    [WARNING] Failed: {e}\n"
                error_count += 1

    # --- Save Results ---
    if database:
        status_message += f"\n[INFO] Saving database ({processed_count} faces) to '{OUTPUT_DB_FILE}'...\n"
        with open(OUTPUT_DB_FILE, 'wb') as f:
            pickle.dump(database, f)
        status_message += "✅✅ Face database updated successfully.\n\n**IMPORTANT:** Please RESTART the 'Take Attendance' app to use the new data."
    else:
        status_message += "\n[INFO] No faces were successfully encoded. Database not updated."
        
    if error_count > 0:
        status_message += f"\n⚠️ Encountered {error_count} error(s)."
        
    print(status_message)
    return status_message

# --- Gradio UI ---
with gr.Blocks(theme=gr.themes.Soft(), title="Encode Face") as iface_encode:
    gr.Markdown("# 🔄 Update Face Database")
    gr.Markdown(
        f"Click the button to scan **{BASE_IMAGES_FOLDER}** and update the database. "
        "Ensure your images are named correctly (e.g., 'Student Name.jpg')."
    )

    update_button = gr.Button("📊 Update Face Database", variant="primary")
    status_output = gr.Textbox(label="Encoding Status", lines=15, interactive=False)

    update_button.click(
        fn=run_encoding,
        inputs=[],
        outputs=[status_output]
    )

if __name__ == "__main__":
    print("[INFO] Launching Face Encoding UI...")
    iface_encode.launch()