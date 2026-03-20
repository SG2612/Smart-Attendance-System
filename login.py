# login.py (Simple Launcher)
import gradio as gr
import json
import os
import subprocess
import sys
import time

# --- Constants ---
USERS_FILE = "users.json"
SESSION_FILE = "session.txt"
USERS_DIR = "Users"
LAUNCHER_SCRIPT = "mainlauncher.py"

# --- Setup ---
if not os.path.exists(USERS_DIR): os.makedirs(USERS_DIR)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f: json.dump({}, f)

# --- Functions ---
def register_user(username, password, confirm_password):
    if not username or not password: return "❌ Error: Missing fields."
    if password != confirm_password: return "❌ Error: Passwords do not match."
    
    with open(USERS_FILE, "r") as f: users = json.load(f)
    if username in users: return "❌ Error: Username exists."
    
    users[username] = password
    with open(USERS_FILE, "w") as f: json.dump(users, f)
    
    user_path = os.path.join(USERS_DIR, username)
    os.makedirs(os.path.join(user_path, "Student_Images"), exist_ok=True)
    return f"✅ Registered '{username}'!"

def login_user(username, password):
    with open(USERS_FILE, "r") as f: users = json.load(f)
    
    if username not in users or users[username] != password:
        return "❌ Invalid username or password."
    
    # Save session
    with open(SESSION_FILE, "w") as f: f.write(username)
    
    # Launch Main Launcher in a separate window
    print(f"✅ Login successful. Starting {LAUNCHER_SCRIPT}...")
    if os.name == 'nt':
        subprocess.Popen([sys.executable, LAUNCHER_SCRIPT], creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        subprocess.Popen([sys.executable, LAUNCHER_SCRIPT])

    return "Login Successful! Launching Hub..."

# --- UI ---
with gr.Blocks(theme=gr.themes.Soft(), title="Attendance Login") as app:
    gr.Markdown("# 🔐 Attendance System Login")
    
    with gr.Tabs():
        with gr.TabItem("Log In"):
            login_user_in = gr.Textbox(label="Username")
            login_pass_in = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Log In", variant="primary")
            login_msg = gr.Textbox(label="Status", interactive=False)
            
            # Simple logic: Run login, wait 2 seconds, close this script
            login_btn.click(
                fn=login_user, 
                inputs=[login_user_in, login_pass_in], 
                outputs=login_msg
            ).then(
                fn=lambda: time.sleep(2) or os._exit(0), 
                inputs=None, 
                outputs=None
            )

        with gr.TabItem("Register"):
            reg_user_in = gr.Textbox(label="New Username")
            reg_pass_in = gr.Textbox(label="New Password", type="password")
            reg_conf_in = gr.Textbox(label="Confirm Password", type="password")
            reg_btn = gr.Button("Register User")
            reg_msg = gr.Textbox(label="Status", interactive=False)
            
            reg_btn.click(register_user, inputs=[reg_user_in, reg_pass_in, reg_conf_in], outputs=reg_msg)

if __name__ == "__main__":
    # Open browser for login
    app.launch(server_name="127.0.0.1", server_port=7859, inbrowser=True)