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
        self.chunks_content = []
        self.chunks_request = []
        self.block_size = 0
    
    @staticmethod
    def __clamp(x, min_val, max_val):
        return max(min_val, min(max_val, x))

    @staticmethod
    # Split the content into chunks of size block_size
    def __split_content_by_estimate(content, block_size):
        chunks = []
        content_len = len(content)
        start_idx = 0
        is_final = False

        while not is_final:
            end_idx = FileHandler.__clamp(start_idx + block_size, 0, content_len)
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
                    prompt_content = file.read()

                # Calculate the block size
                block_size = GPTHandler.calculate_block_size(prompt_content)
                if block_size == 0:
                    self.notify("show_error", message=f"An error occurred while calculating the block size.")
                    return
                else:  
                    self.prompt_content = prompt_content
                    self.block_size = block_size

                self.notify("update_prompt_label", filepath=prompt_file)
                self.notify("reset_labels")
            except FileNotFoundError:
                self.notify("show_error", message=f"File '{prompt_file}' not found.")
            except Exception as e:
                self.notify("show_error", message=f"An error occurred while reading the file: {e}")

    # Open the content file
    def open_content_file(self):

        # Check if prompt file is selected
        if self.prompt_content == None:
            self.notify("show_error", message=f"A prompt file is not found.")
            return
        
        # Open the content file
        initial_directory = self.default_dir if self.default_dir else None
        content_file = self.notify("request_content_file", initialdir=initial_directory)

        # Set the input base name and path
        self.input_base_name = os.path.splitext(os.path.basename(content_file))[0]
        self.input_path = os.path.dirname(content_file)

        if content_file:
            try:
                input_content = ""
                with open(content_file, "r", encoding="utf-8") as file:
                    input_content = file.read()
                
                # Split the content into chunks of size block_size
                chunks_content = FileHandler.__split_content_by_estimate(input_content, self.block_size)
                if not chunks_content:
                    self.notify("show_error", message=f"An error occurred while splitting the content.")
                    return
                else:
                    self.chunks_content = chunks_content
                    self.notify("update_content_label", filepath=content_file)
                    self.notify("reset_labels")

            except FileNotFoundError:
                self.notify("show_error", message=f"File '{content_file}' not found.")
            except Exception as e:
                self.notify("show_error", message=f"An error occurred while reading the file: {e}")

    # Set the chunks to the request
    def set_chunks(self):
        
        # init
        chunks_request = []

        if not self.prompt_content or not self.chunks_content:
            self.notify("show_error", message=f"Please ensure both the prompt and input files are selected.")
            return

        # TODO: notify the observer that chunk/run label should be updated / reset to default
        self.notify("update_chunk_label", chunk_count=len(self.chunks_content))
        chunks_request = GPTHandler.set_chunks_request(self.chunks_content)

        if chunks_request:
            self.chunks_request = chunks_request
        else:
            self.notify("show_error", message=f"An error occurred while setting the chunks.")
            self.notify("reset_labels")

    def run_file_converter(self, output_format):

        accumulated_response = GPTHandler.start_threaded_get_response(self.prompt_content, self.chunks_request)
        FileHandler.__save_response(self.input_base_name, self.input_path, accumulated_response, output_format)
        self.notify("update_run_label", run_count=len(self.chunks_request))

