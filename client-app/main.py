import os
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import urllib3

# Suppress only the single InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SpeechTranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Transcription")
        self.root.geometry("800x600")
      
        self.verify_ssl = tk.BooleanVar(value=True)
  
        self.show_password = tk.BooleanVar(value=False)
        
        # Language mapping (matching the API's supported languages)
        self.language_mapping = {
            'English': 'english',
            'Italian': 'italian',
            'German': 'german',
            'French': 'french',
            'Spanish': 'spanish',
            'Dutch': 'dutch',
            'Macedonian': 'macedonian',
            'Portuguese': 'portuguese',
            'Russian': 'russian',
            'Chinese': 'chinese',
            'Japanese': 'japanese',
            'Korean': 'korean',
            'Arabic': 'arabic',
            'Hindi': 'hindi',
            'Turkish': 'turkish',
            'Greek': 'greek',
            'Polish': 'polish',
            'Romanian': 'romanian',
            'Vietnamese': 'vietnamese',
            'Thai': 'thai'
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # API URL input
        ttk.Label(main_frame, text="API URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_url_var = tk.StringVar(value="https://localhost:5003/speech-to-text")
        ttk.Entry(main_frame, textvariable=self.api_url_var, width=50).grid(
            row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        
        # API Key input with show/hide functionality
        ttk.Label(main_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value="")  # Initialize with empty string
        self.api_key_entry = ttk.Entry(
            main_frame, 
            textvariable=self.api_key_var, 
            show="●",  # Use bullet character for masked input
            width=50
        )
        self.api_key_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Show/Hide password checkbox
        self.show_password_cb = ttk.Checkbutton(
            main_frame, 
            text="Show API Key",
            variable=self.show_password,
            command=lambda: self.toggle_api_key_visibility()
        )
        self.show_password_cb.grid(row=1, column=2, sticky=tk.W, pady=5, padx=5)
        
        # SSL Verification checkbox
        self.ssl_verify_cb = ttk.Checkbutton(
            main_frame,
            text="Verify SSL Certificate",
            variable=self.verify_ssl
        )
        self.ssl_verify_cb.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # File selection
        ttk.Label(main_frame, text="Audio File:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.file_path_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.file_path_var, width=50).grid(
            row=3, column=1, sticky=(tk.W, tk.E), pady=5
        )
        ttk.Button(main_frame, text="Browse", command=self.browse_file).grid(
            row=3, column=2, sticky=tk.W, pady=5, padx=5
        )
        
        # Language selection dropdown
        ttk.Label(main_frame, text="Select Language:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.selected_language = tk.StringVar(value="English")  # Default to English
        language_dropdown = ttk.Combobox(
            main_frame, 
            textvariable=self.selected_language,
            values=sorted(list(self.language_mapping.keys())),
            state="readonly",
            width=47
        )
        language_dropdown.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Transcription result
        ttk.Label(main_frame, text="Transcription:").grid(row=5, column=0, sticky=tk.W, pady=5)
        
        # Create a frame for the text widget and scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        
        self.result_text = tk.Text(text_frame, height=15, width=60, wrap=tk.WORD)
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.result_text['yscrollcommand'] = scrollbar.set
        
        # Progress indicator
        self.progress_var = tk.StringVar(value="")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(
            row=7, column=0, columnspan=3, sticky=tk.W, pady=5
        )
        
        # Transcribe button
        self.transcribe_button = ttk.Button(
            main_frame, text="Transcribe", command=self.start_transcription
        )
        self.transcribe_button.grid(row=8, column=0, columnspan=3, pady=10)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def toggle_api_key_visibility(self):
        """Toggle the visibility of the API key"""
        current_show = self.show_password.get()
        self.api_key_entry.configure(show="" if current_show else "●")
        
    def browse_file(self):
        """Handle file selection"""
        filetypes = (
            ('Audio files', '*.wav *.mp3 *.ogg *.flac'),
            ('All files', '*.*')
        )
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.file_path_var.set(filename)
            
    def transcribe_audio(self):
        """Handle the transcription process"""
        try:
            self.progress_var.set("Preparing transcription...")
            audio_path = self.file_path_var.get()
            
            if not audio_path:
                messagebox.showerror("Error", "Please select an audio file")
                return
                
            # Clean and validate API key
            api_key = self.api_key_var.get().strip()
            if not api_key:
                messagebox.showerror("Error", "Please enter your API key")
                return
            
            # Get selected language
            selected_language = self.selected_language.get()
            language_code = self.language_mapping[selected_language]
            
            # Prepare API request
            self.progress_var.set(f"Transcribing in {selected_language}...")
            
            # Ensure file is properly opened and closed
            with open(audio_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                data = {'language': language_code}
                headers = {
                    'X-API-Key': api_key.strip()  # Remove any whitespace
                }
                
                # Make API request with SSL verification setting
                response = requests.post(
                    self.api_url_var.get().strip(),  # Clean URL
                    files=files,
                    data=data,
                    headers=headers,
                    verify=self.verify_ssl.get()
                )
            
            if response.status_code == 200:
                result = response.json()
                self.result_text.delete('1.0', tk.END)
                self.result_text.insert('1.0', result['text'])
                self.progress_var.set("Transcription complete!")
            else:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                self.result_text.delete('1.0', tk.END)
                self.result_text.insert('1.0', error_msg)
                self.progress_var.set("Transcription failed!")
                
        except Exception as e:
            self.progress_var.set("Error during transcription!")
            messagebox.showerror("Error", str(e))
        
        finally:
            self.transcribe_button['state'] = 'normal'
            
    def start_transcription(self):
        """Start transcription in a separate thread"""
        self.transcribe_button['state'] = 'disabled'
        self.result_text.delete('1.0', tk.END)
        threading.Thread(target=self.transcribe_audio, daemon=True).start()

def main():
    root = tk.Tk()
    app = SpeechTranscriptionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
