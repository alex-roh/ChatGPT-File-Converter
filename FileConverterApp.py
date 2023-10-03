import customtkinter
from tkinter import filedialog, messagebox, StringVar, OptionMenu
from FileHandler import FileHandler

class FileConverterApp:

    # Singleton
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(FileConverterApp, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):

        if self.__initialized:
            return
        
        # Set up the GUI
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")
        self.app = customtkinter.CTk()
        self.app.title('Send Content/Prompt to ChatGPT Turbo 16k')
        self.output_format = StringVar(value=".txt")

        # Set up the FileHandler
        self.file_handler = FileHandler()
        self.file_handler.attach(self)

        # Init
        self.init_ui()
        self.__initialized = True

    def init_ui(self):
        frame = customtkinter.CTkFrame(master=self.app)
        frame.pack()
        self.init_ui_components(frame)

    def init_ui_components(self, frame):
        # Set default button / label
        self.set_default_bt = customtkinter.CTkButton(frame, text="Set Default Content Directory", command=self.file_handler.set_default_dir)
        self.set_default_bt.pack()
        self.default_label = customtkinter.CTkLabel(frame, text="No default directory set", wraplength=350)
        self.default_label.pack()

        # Open prompt button / label
        self.open_prompt_bt = customtkinter.CTkButton(frame, text="Open Prompt File", command=self.file_handler.open_prompt_file)
        self.open_prompt_bt.pack()
        self.prompt_label = customtkinter.CTkLabel(frame, text="No prompt file selected", wraplength=350)
        self.prompt_label.pack()

        # Open content button / label
        self.open_content_bt = customtkinter.CTkButton(frame, text="Open Content File", command=self.file_handler.open_content_file)
        self.open_content_bt.pack()
        self.content_label = customtkinter.CTkLabel(frame, text="No content file selected", wraplength=350)
        self.content_label.pack()

        # Set button / chunk label
        self.set_bt = customtkinter.CTkButton(frame, text="SET", command=self.file_handler.set_chunks)
        self.set_bt.pack()
        self.chunk_label = customtkinter.CTkLabel(frame, text="Not set yet", wraplength=350)
        self.chunk_label.pack()

        # Run button / label
        self.run_bt = customtkinter.CTkButton(
            frame, text="RUN", command=lambda: self.file_handler.run_file_converter(self.output_format.get())
            ) # not directly calling the function so that the output format can be passed in
        self.run_bt.pack()
        self.run_label = customtkinter.CTkLabel(frame, text="Not replied yet", wraplength=350)
        self.run_label.pack()

        # Add option to select output format
        self.output_format_label = customtkinter.CTkLabel(frame, text="Select Output Format:")
        self.output_format_label.pack()
        self.output_format_dropdown = OptionMenu(frame, self.output_format, ".txt", ".md", ".csv")
        self.output_format_dropdown.pack()

    def update(self, event, **kwargs):
        if event == "request_directory":
            directory = filedialog.askdirectory(title="Select a Directory")
            return directory  # returning the directory so it can be used in FileHandler

        elif event == "request_prompt_file":
            filepath = filedialog.askopenfilename(
                title="Open Prompt File",
                filetypes=[("Text files", "*.txt")],
                initialdir=kwargs.get("initialdir")
            )
            return filepath

        elif event == "request_content_file":
            filepath = filedialog.askopenfilename(
                title="Open Prompt File",
                filetypes=[("Text files", "*.txt")],
                initialdir=kwargs.get("initialdir")
            )
            return filepath

        elif event == "update_default_label":
            default_dir = kwargs.get("default_dir")
            self.default_label.configure(text=default_dir)

        elif event == "update_prompt_label":
            filepath = kwargs.get("filepath")
            self.prompt_label.configure(text=filepath)

        elif event == "update_content_label":
            filepath = kwargs.get("filepath")
            self.content_label.configure(text=filepath)
        
        elif event == "update_chunk_label":
            chunk_count = kwargs.get("chunk_count")
            self.chunk_label.configure(text=f"{chunk_count} requests generated")
        
        elif event == "update_run_label":
            run_count = kwargs.get("run_count")
            self.run_label.configure(text=f"{run_count} requests completed")

        elif event == "reset_labels":
            self.chunk_label.configure(text="Not set yet")
            self.run_label.configure(text="Not replied yet")
            
        elif event == "show_error":
            message = kwargs.get("message")
            messagebox.showerror("Error", message)

    def run(self):
        self.app.mainloop()


if __name__ == "__main__":
    chat_gpt_app = FileConverterApp()
    chat_gpt_app.run()