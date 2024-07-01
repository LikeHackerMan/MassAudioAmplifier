import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar, Combobox
from threading import Thread, Lock
import pydub

# Lock for thread-safe access to progress bar value
progress_lock = Lock()

amplification_complete = False

# Global list to keep track of threads
threads = []

def amplify_audio(input_folder, output_folder, amplification, bitrate, progress_bar, audio_files, file_extension):
    global amplification_complete
    try:
        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Progress bar
        chunk_size = len(audio_files)
        progress_bar['maximum'] = chunk_size
        progress_bar['value'] = 0

        for file_name in audio_files:
            # Load file
            audio = pydub.AudioSegment.from_file(os.path.join(input_folder, file_name), format=file_extension[1:])

            # Amplify audio
            amplified_audio = audio.apply_gain(amplification)

            # Export amplified audio
            output_file_path = os.path.join(output_folder, file_name)
            # Specify bitrate during export
            amplified_audio.export(output_file_path, format=file_extension[1:], bitrate=bitrate)

            # Update progress bar
            with progress_lock:
                progress_bar['value'] += 1
                root.update_idletasks()

        # Set amplification complete flag to True
        amplification_complete = True

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def select_input_folder():
    input_folder_path = filedialog.askdirectory()
    input_folder_entry.delete(0, tk.END)
    input_folder_entry.insert(0, input_folder_path)

def select_output_folder():
    output_folder_path = filedialog.askdirectory()
    output_folder_entry.delete(0, tk.END)
    output_folder_entry.insert(0, output_folder_path)

def amplify():
    global amplification_complete, threads
    input_folder_path = input_folder_entry.get()
    output_folder = output_folder_entry.get()
    amplification = float(amplification_entry.get())
    bitrate = bitrate_entry.get()
    file_extension = file_extension_combobox.get()

    # Check if input folder is provided
    if not input_folder_path:
        messagebox.showwarning("Input Folder Not Provided", "Please select an input folder.")
        return

    # List of files in the input folder
    allowed_extensions = [file_extension]
    audio_files = [file for file in os.listdir(input_folder_path) if os.path.isfile(os.path.join(input_folder_path, file)) and file.lower().endswith(file_extension)]

    # Check for files are found in the input folder
    if not audio_files:
        messagebox.showwarning("No Audio Files", f"No {file_extension} files found in the selected folder.")
        return

    # Start amplification process in a separate thread
    amplify_thread = Thread(target=perform_amplification, args=(input_folder_path, output_folder, amplification, bitrate, audio_files, file_extension))
    amplify_thread.start()
    threads.append(amplify_thread)

def perform_amplification(input_folder, output_folder, amplification, bitrate, audio_files, file_extension):
    global amplification_complete
    # Start amplification process
    progress_bar = Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate')
    progress_bar.grid(row=6, columnspan=3, pady=10)

    # Calculate chunk size for each thread
    num_threads = os.cpu_count() or 1
    chunk_size = max(1, len(audio_files) // num_threads)
    threads_local = []

    try:
        # Start one thread per chunk
        for i in range(0, len(audio_files), chunk_size):
            thread_files = audio_files[i:i + chunk_size]
            thread = Thread(target=amplify_audio, args=(input_folder, output_folder, amplification, bitrate, progress_bar, thread_files, file_extension))
            thread.start()
            threads_local.append(thread)

        # Wait for threads to yeild
        for thread in threads_local:
            thread.join()

    finally:
        # Clean up threads
        for thread in threads_local:
            if thread.is_alive():
                thread.join()

        # Display "Amplification Complete"
        if amplification_complete:
            messagebox.showinfo("Amplification Complete", "Amplification complete!")
            amplification_complete = False  # Reset the flag

def exit_program():
    global threads
    # Join all threads before exiting
    for thread in threads:
        if thread.is_alive():
            thread.join()
    root.destroy()

# Create GUI
root = tk.Tk()
root.title("Audio Amplifier")

input_folder_label = tk.Label(root, text="Input Folder:")
input_folder_label.grid(row=0, column=0)

input_folder_entry = tk.Entry(root, width=50)
input_folder_entry.grid(row=0, column=1)

input_folder_button = tk.Button(root, text="Browse", command=select_input_folder)
input_folder_button.grid(row=0, column=2)

output_folder_label = tk.Label(root, text="Output Folder:")
output_folder_label.grid(row=1, column=0)

output_folder_entry = tk.Entry(root, width=50)
output_folder_entry.grid(row=1, column=1)

output_folder_button = tk.Button(root, text="Browse", command=select_output_folder)
output_folder_button.grid(row=1, column=2)

amplification_label = tk.Label(root, text="Amplification (dB):")
amplification_label.grid(row=2, column=0)

amplification_entry = tk.Entry(root)
amplification_entry.grid(row=2, column=1)

bitrate_label = tk.Label(root, text="Bitrate (e.g., 192k):")
bitrate_label.grid(row=3, column=0)

bitrate_entry = tk.Entry(root)
bitrate_entry.grid(row=3, column=1)

file_extension_label = tk.Label(root, text="File Extension:")
file_extension_label.grid(row=4, column=0)

file_extension_combobox = Combobox(root, values=['.mp3', '.ogg', '.m4a', '.wav'], state='readonly')
file_extension_combobox.grid(row=4, column=1)
file_extension_combobox.current(0)  # Set default value

amplify_button = tk.Button(root, text="Amplify", command=amplify)
amplify_button.grid(row=5, column=0, columnspan=2, pady=10)

exit_button = tk.Button(root, text="Exit", command=exit_program)
exit_button.grid(row=5, column=2)

root.mainloop()