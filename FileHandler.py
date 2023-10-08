import os
import inspect
from GPTHandler import GPTHandler
from Observable import Observable

class FileHandler(Observable):

    def __init__(self):
        
        super().__init__()

        # Set up fields related to file paths
        self.default_dir = None
        self.input_base_name = None
        self.input_path = None

        # Set up fields related to content
        self.prompt_content = None
        self.input_content = None
        self.chunks_content = []
        self.chunk_chars = 0
    
    @staticmethod
    def __clamp(x, min_val, max_val):
        return max(min_val, min(max_val, x))

    @staticmethod
    # Split the content into chunks of {chunk_chars}
    def __split_content_by_estimate(content, chunk_chars):
        chunks = []
        content_len = len(content)
        start_idx = 0
        is_final = False

        while not is_final:
            end_idx = FileHandler.__clamp(start_idx + chunk_chars, 0, content_len)
            is_final = (end_idx == content_len)
            # To save its original index in case we need to backtrack
            original_end_idx = end_idx
            # backtrack until we find a space or newline
            while not is_final and end_idx > start_idx and content[end_idx] not in [' ', '\n']:
                end_idx -= 1
            # The content is a single word that is longer than the block size
            if end_idx <= start_idx:
                end_idx = original_end_idx
            chunks.append(content[start_idx:end_idx])
            start_idx = end_idx

        return chunks
    
    @staticmethod
    def __save_response(base_name, path, response, format):
        file_name = os.path.join(path, f"GPT_{base_name}{format}")
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(response)
        except Exception as e:
            print(f"{inspect.currentframe().f_code.co_name}: An error occurred while saving the file: {e}")

    # Set the default directory for content files
    def set_default_dir(self):
        directory_path = self.notify("request_directory")
        if directory_path:
            try:
                self.default_dir = directory_path
                self.notify("update_default_label", default_dir=self.default_dir)
            except FileNotFoundError:
                # Notifying observer to show error
                self.notify("show_error", message=f"Directory '{self.default_dir}' not found.")
            except Exception as e:
                # Notifying observer to show error
                self.notify("show_error", message=f"An error occurred while reading the directory: {e}")
    
    # Open the prompt file
    def open_prompt_file(self):

        initial_directory = self.default_dir if self.default_dir else None
        prompt_file = self.notify("request_prompt_file", initialdir=initial_directory)

        if prompt_file:
            try:
                with open(prompt_file, "r", encoding="utf-8") as file:
                    self.prompt_content = file.read()
                self.notify("update_prompt_label", filepath=prompt_file)
                self.notify("reset_labels")
            except FileNotFoundError:
                self.notify("show_error", message=f"File '{prompt_file}' not found.")
            except Exception as e:
                self.notify("show_error", message=f"An error occurred while reading the file: {e}")

    # Open the content file
    def open_content_file(self):
        # Open the content file
        initial_directory = self.default_dir if self.default_dir else None
        content_file = self.notify("request_content_file", initialdir=initial_directory)

        # Set the input base name and path
        self.input_base_name = os.path.splitext(os.path.basename(content_file))[0]
        self.input_path = os.path.dirname(content_file)

        if content_file:
            try:
                with open(content_file, "r", encoding="utf-8") as file:
                    self.input_content = file.read()
                self.notify("update_content_label", filepath=content_file)
                self.notify("reset_labels")
            except FileNotFoundError:
                self.notify("show_error", message=f"File '{content_file}' not found.")
            except Exception as e:
                self.notify("show_error", message=f"An error occurred while reading the file: {e}")

    # Set the chunks to the request
    def set_chunks(self, language):
        # Check if the prompt and content files are selected
        if not self.input_content or not self.prompt_content:
            self.notify("show_error", message="Please ensure both the prompt and input files are selected.")
            return

        # Set the chunk token
        self._set_chunk_chars(language)
        
        # Split the content into chunks
        if self.chunk_chars > 0:
            self._set_chunks_content()
            self.notify("update_chunk_label", chunk_count=len(self.chunks_content))
            print(f"language: {language}, chunk_chars: {self.chunk_chars}, chunks_content: {len(self.chunks_content)}")
    
    # Run the file converter
    def run_file_converter(self, output_format):
        
        # Check if the block size and chunks are set
        if not self.chunk_chars or not self.chunks_content:
            self.notify("show_error", message=f"Please ensure the chunks are set.")
            return

        accumulated_response = GPTHandler.start_threaded_get_response(self.prompt_content, self.chunks_content)
        FileHandler.__save_response(self.input_base_name, self.input_path, accumulated_response, output_format)
        self.notify("update_run_label", run_count=len(self.chunks_content))

    # Private methods
    def _set_chunk_chars(self, language):
        chunk_chars = GPTHandler.calculate_chunk_chars(self.prompt_content, language)
        if chunk_chars == 0:
            self.notify("show_error", message=f"An error occurred while calculating the chunk characters ({self.chunk_chars}).")
            self.notify("reset_labels")
        else:
            self.chunk_chars = chunk_chars
    
    def _set_chunks_content(self):
        chunks_content = FileHandler.__split_content_by_estimate(self.input_content, self.chunk_chars)
        if not chunks_content:
            self.notify("show_error", message=f"An error occurred while splitting the content.")
            self.notify("reset_labels")
        else:
            self.chunks_content = chunks_content
            for _, chunk in enumerate(self.chunks_content):
                print(f"{_ + 1}th chunk: {GPTHandler.get_token_count(chunk)} tokens")

    # Callback methods
    def _on_gpthandler_thread_complete(self, processed_chunks):
        # This is called when GPTHandler's thread completes its task.
        # Notify the FileConverterApp.
        self.notify("one_thread_processing_complete", run_count=processed_chunks)