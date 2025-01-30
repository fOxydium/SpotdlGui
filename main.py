import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import requests
import json
import webbrowser
import threading
import os
import signal

current_version = "v1.1"
owner = "fOxydium"
repo = "SpotdlGui"

# Flag to manage download process
download_running = False
process = None
window = None  # Declare window globally

def open_link(latest_version):
    url = f"https://github.com/fOxydium/SpotdlGui/releases/tag/{latest_version}"
    webbrowser.open(url)

def check_for_updates():
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            release_info = response.json()
            latest_version = release_info["tag_name"]

            if compare_versions(latest_version, current_version):
                notify_user(latest_version)
            else:
                messagebox.showinfo("Up to date!", "No Update Needed.")
        else:
            print("Error fetching release information.")
            messagebox.showerror("Error", f"An error occurred: Failed to fetch release information")
    except Exception as e:
        print(f"Error occurred: {e}")

def compare_versions(latest_version, current_version):
    return latest_version != current_version

def notify_user(latest_version):
    notification_window = tk.Tk()
    notification_window.title("Update Available")

    label = tk.Label(notification_window, text="A new version is available!")
    label.pack(pady=10)

    button = tk.Button(notification_window, text=f"Go to {latest_version} Release", command=lambda: open_link(latest_version))
    button.pack(pady=10)

def browse_directory():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        output_dir_entry.delete(0, tk.END)
        output_dir_entry.insert(0, folder_selected)

def stop_download():
    global download_running
    global process
    if download_running and process:
        try:
            # Terminate the running process
            os.kill(process.pid, signal.SIGTERM)
            process = None
            download_running = False
            update_button("Start Download")
            messagebox.showinfo("Download Stopped", "The download has been stopped.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop the download: {str(e)}")

def update_button(label):
    run_button.config(text=label, command=start_or_stop_download)

def start_or_stop_download():
    if download_running:
        stop_download()
    else:
        download_thread = threading.Thread(target=run_spotdl)
        download_thread.start()

def run_spotdl():
    global download_running
    global process

    url = url_entry.get()
    output_dir = output_dir_entry.get()

    if not url:
        messagebox.showwarning("Input Error", "Please provide a valid Spotify URL.")
        return

    audio_format = format_var.get()
    threadcount = thread_var.get()
    output_dir = f'"{output_dir}"'

    command = f"spotdl {url} --output {output_dir} --format {audio_format} --threads {threadcount}"

    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        download_running = True
        update_button("Stop Download")

        # Start separate threads to handle stdout and stderr
        threading.Thread(target=read_output, args=(process.stdout,)).start()
        threading.Thread(target=read_output, args=(process.stderr, True)).start()

        # Wait for the process to complete
        process.wait()

        download_running = False
        update_button("Start Download")
        messagebox.showinfo("Success", "Download completed successfully!")

    except subprocess.CalledProcessError as e:
        download_running = False
        update_button("Start Download")
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
    except Exception as e:
        download_running = False
        update_button("Start Download")
        messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

def read_output(output_stream, is_error=False):
    """Reads output from a subprocess stream and updates the GUI in real-time."""
    while download_running:
        output_line = output_stream.readline()
        if output_line == '' and process.poll() is not None:
            break
        if output_line:
            update_output(output_line, is_error)

def update_output(output, is_error=False):
    """Update the GUI Text widget with output or errors"""
    output_text.config(state=tk.NORMAL)  # Enable editing the Text widget
    if is_error:
        output_text.insert(tk.END, f"ERROR: {output}\n", "error")  # Highlight error output
    else:
        output_text.insert(tk.END, output)  # Normal output
    output_text.yview(tk.END)  # Scroll to the end to show the latest output
    output_text.config(state=tk.DISABLED)  # Disable editing after updating

def create_gui():
    global window
    window = tk.Tk()
    window.title("SpotDL GUI Frontend")

    window.protocol("WM_DELETE_WINDOW", on_closing)  # Handle window close event

    url_label = tk.Label(window, text="Spotify URL:")
    url_label.pack(pady=5)
    global url_entry
    url_entry = tk.Entry(window, width=40)
    url_entry.pack(pady=5)

    output_dir_label = tk.Label(window, text="Output Directory:")
    output_dir_label.pack(pady=5)

    global output_dir_entry
    output_dir_entry = tk.Entry(window, width=40)
    output_dir_entry.pack(pady=5)

    browse_button = tk.Button(window, text="Browse...", command=browse_directory)
    browse_button.pack(pady=5)

    format_label = tk.Label(window, text="Choose Audio Format:")
    format_label.pack(pady=5)

    global format_var
    format_var = tk.StringVar(value="mp3")  # Default value

    format_mp3 = tk.Radiobutton(window, text="MP3", variable=format_var, value="mp3")
    format_mp3.pack()
    format_m4a = tk.Radiobutton(window, text="M4A", variable=format_var, value="m4a")
    format_m4a.pack()
    format_flac = tk.Radiobutton(window, text="FLAC", variable=format_var, value="flac")
    format_flac.pack()
    format_wav = tk.Radiobutton(window, text="WAV", variable=format_var, value="wav")
    format_wav.pack()

    global thread_var
    thread_label = tk.Label(window, text="Download Threads:")
    thread_label.pack(pady=5)
    thread_var = tk.IntVar(value=1)

    thread_entry = tk.Entry(window, textvariable=thread_var)
    thread_entry.pack()

    global run_button
    run_button = tk.Button(window, text="Start Download", command=start_or_stop_download)
    run_button.pack(pady=20)

    update_button = tk.Button(window, text="Check For Updates", command=check_for_updates)
    update_button.pack(pady=20)

    # Text widget to display output from the download process
    global output_text
    output_text = tk.Text(window, width=80, height=20, wrap=tk.WORD, state=tk.DISABLED)
    output_text.pack(pady=10)

    window.mainloop()

def on_closing():
    global download_running
    if download_running:
        stop_download()  # Attempt to stop the download before closing
    window.quit()

if __name__ == "__main__":
    create_gui()
