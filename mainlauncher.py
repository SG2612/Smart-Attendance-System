# launch_final.py (Auto-Open Hub + Auto-Open Apps + Emoji Safe)

import gradio as gr
import subprocess
import sys
import os
import webbrowser
import threading
import re

# --- Configuration (Matches your uploaded files) ---
APPS = {
    "add_students": "add_students.py",
    "encode": "encode_face.py",
    "attendance": "attendance_app.py"
}

PYTHON_EXECUTABLE = sys.executable

def launch_and_monitor(script_name):
    script_path = os.path.join(os.getcwd(), script_name)
    if not os.path.exists(script_path):
        return f"❌ Error: Could not find '{script_name}'."

    print(f"🚀 Launching {script_name}...")

    # --- Robust Subprocess (Fixes Emoji Crashes & Output buffering) ---
    if os.name == 'nt': # Windows
        process = subprocess.Popen(
            [PYTHON_EXECUTABLE, "-u", script_path], # -u for unbuffered output
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',   # <--- Critical Fix for Emojis
            errors='replace',   # <--- Prevents crashing on unknown characters
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else: # Mac/Linux
        process = subprocess.Popen(
            [PYTHON_EXECUTABLE, "-u", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

    # Thread to monitor output and open the sub-app browser
    def monitor_output(proc):
        url_found = False
        while True:
            line = proc.stdout.readline()
            if not line: break
            
            # Print sub-app output to this console so you can see progress
            print(f"[{script_name}] {line.strip()}")

            # Look for the URL in the sub-app's output
            if "Running on local URL:" in line and not url_found:
                match = re.search(r'(http://127.0.0.1:\d+)', line)
                if match:
                    real_url = match.group(1)
                    print(f"✅ URL Found: {real_url}. Opening browser...")
                    webbrowser.open(real_url) # Open the sub-app tab
                    url_found = True
    
    threading.Thread(target=monitor_output, args=(process,), daemon=True).start()

    return f"✅ Launched {script_name}! Check your taskbar/browser."

# --- Button Functions ---
def open_add_students(): return launch_and_monitor(APPS["add_students"])
def open_encode(): return launch_and_monitor(APPS["encode"])
def open_attendance(): return launch_and_monitor(APPS["attendance"])

# --- Gradio UI ---
with gr.Blocks(theme=gr.themes.Soft(), title="Attendance Hub") as launcher_iface:
    gr.Markdown("# 🚀 Attendance System Hub")
    gr.Markdown("Click a button below. The system will auto-detect the port and open the browser for you.")

    with gr.Row():
        btn_add = gr.Button("1. ➕ Add Students", variant="secondary")
        btn_encode = gr.Button("2. 🔄 Update Database", variant="secondary")
        btn_attend = gr.Button("3. ▶️ Take Attendance", variant="primary")

    status = gr.Textbox(label="Status", interactive=False)

    btn_add.click(fn=open_add_students, outputs=status)
    btn_encode.click(fn=open_encode, outputs=status)
    btn_attend.click(fn=open_attendance, outputs=status)

if __name__ == "__main__":
    print("[INFO] Launching Main Hub...")
    # Fix: Removed specific port so it finds a free one if 7860 is taken
    # Fix: Added inbrowser=True so the Main Hub opens automatically
    launcher_iface.launch(server_name="127.0.0.1", inbrowser=True)