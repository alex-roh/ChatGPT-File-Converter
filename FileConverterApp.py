import customtkinter
from tkinter import filedialog, messagebox, StringVar, OptionMenu
from FileHandler import FileHandler

class FileConverterApp:

    # Constants
    TITLE = "Send Content/Prompt to ChatGPT Turbo 3.5"
    APPEARANCE_MODE = "dark"
    DEFAULT_COLOR_THEME = "green"
    FILE_TYPES = [("Text files", "*.txt")]
    DEFAULT_OUTPUT_FORMAT = ".txt"
    DEFAULT_LANGUAGE = "English"

    # Singleton
    _instance = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = FileConverterApp()
        return cls._instance
    
    def __init__(self):

        # Singleton
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        # Set up the GUI
        customtkinter.set_appearance_mode(self.APPEARANCE_MODE)
        customtkinter.set_default_color_theme(self.DEFAULT_COLOR_THEME)
        self.app = customtkinter.CTk()
        self.app.title(self.TITLE)
        self.output_format = StringVar(value=self.DEFAULT_OUTPUT_FORMAT)
        self.file_language = StringVar(value=self.DEFAULT_LANGUAGE)
        self.gpt_model = StringVar(value="gpt-3.5-turbo")

        # Set up the FileHandler
        self.file_handler = FileHandler()
        self.file_handler.attach(self)

        # Init variables
        self.num_chunks = 0
        self.processed_chunks = 0

        # Init
        self.init_ui()
        self.__initialized = True

    def init_ui(self):
        frame = customtkinter.CTkFrame(master=self.app)
        frame.pack()
        self.init_ui_components(frame)

    def init_ui_components(self, frame):
        self.set_default_bt, self.default_label = self._init_component(frame, "Set Default Content Directory", self.file_handler.set_default_dir, "No default directory set")
        self.open_prompt_bt, self.prompt_label = self._init_component(frame, "Open Prompt File", self.file_handler.open_prompt_file, "No prompt file selected")

        self.language_dropdown = OptionMenu(frame, self.file_language, "English", "Korean")
        self.language_dropdown.pack()
        self.select_model_dropdown = OptionMenu(frame, self.gpt_model, *self.file_handler.models)
        self.select_model_dropdown.pack()

        self.open_content_bt, self.content_label = self._init_component(frame, "Open Content File", self.file_handler.open_content_file, "No content file selected") 
        
        self.run_bt, self.run_label = self._init_component(frame, "RUN", lambda: self.file_handler.run_file_converter(
            self.file_language.get(), self.gpt_model.get(), self.output_format.get()), "Not replied yet")
        
        self.output_format_label = customtkinter.CTkLabel(frame, text="Select Output Format:")
        self.output_format_label.pack()
        self.output_format_dropdown = OptionMenu(frame, self.output_format, ".txt", ".md", ".csv")
        self.output_format_dropdown.pack()

    def _init_component(self, frame, button_text, button_command, label_text):
        button = customtkinter.CTkButton(frame, text=button_text, command=button_command)
        button.pack()
        label = customtkinter.CTkLabel(frame, text=label_text, wraplength=350)
        label.pack()
        return button, label
    
    def run(self):
        self.update_periodically()
        self.app.mainloop()

    # Observer methods
    def update(self, event, **kwargs):
        update_mapping = {
            "request_directory": self._update_directory,
            "request_prompt_file": lambda **kwargs: self._update_file("Open Prompt File", **kwargs),
            "request_content_file": lambda **kwargs: self._update_file("Open Content File", **kwargs),
            "update_default_label": lambda **kwargs: self._set_label_text(self.default_label, kwargs.get("default_dir")),
            "update_prompt_label": lambda **kwargs: self._set_label_text(self.prompt_label, kwargs.get("filepath")),
            "update_content_label": lambda **kwargs: self._set_label_text(self.content_label, kwargs.get("filepath")),
            "update_run_label": lambda **kwargs: self._set_label_text(self.run_label, f"{kwargs.get('run_count')} requests completed"),
            "reset_labels": self._reset_labels,
            "set_num_chunks": lambda **kwargs: self._set_num_chunks(kwargs.get('num_chunks')),
            "set_processed_chunks": lambda **kwargs: self._set_processed_chunks(kwargs.get('processed_chunks')),
            "show_error": lambda **kwargs: self._show_error(kwargs.get("message")),
            "one_thread_processing_complete": lambda **kwargs: self._set_label_text(self.run_label, f"{kwargs.get('run_count')} requests completed")
        }
        return update_mapping.get(event, lambda **kwargs: None)(**kwargs)
    
    def update_periodically(self):
        if self.processed_chunks == self.num_chunks == 0:
            self._set_label_text(self.run_label, f"Waiting for the chunks to be processed...")
        elif self.num_chunks > 0 and self.processed_chunks == 0:
            self._set_label_text(self.run_label, f"Sending {self.num_chunks} chunks to GPT-3.5 Turbo...")
        elif self.processed_chunks > 0:
            self._set_label_text(self.run_label, f"Finished {self.processed_chunks} chunks out of {self.num_chunks} chunks")
        elif self.processed_chunks == self.num_chunks:
            self._set_label_text(self.run_label, f"Completed the classification!")

        # Periodic update (100ms)
        self.app.after(100, self.update_periodically)
    
    # Updated methods based on events to make it more modular
    def _update_directory(self, **kwargs):
        return filedialog.askdirectory(title="Select a Directory")

    def _update_file(self, title, **kwargs):
        return filedialog.askopenfilename(title=title, filetypes=self.FILE_TYPES, initialdir=kwargs.get("initialdir"))

    def _set_label_text(self, label, text):
        label.configure(text=text)

    def _set_num_chunks(self, num_chunks):
        self.num_chunks = num_chunks

    def _set_processed_chunks(self, processed_chunks):
        self.processed_chunks = processed_chunks

    def _show_error(self, message):
        messagebox.showerror("Error", message)

    def _reset_labels(self, **kwargs):
        self.run_label.configure(text="Not replied yet")



if __name__ == "__main__":
    chat_gpt_app = FileConverterApp.get_instance()
    chat_gpt_app.run()