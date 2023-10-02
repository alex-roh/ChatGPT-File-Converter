import os
import openai
import tiktoken

import threading
from tkinter import *
from tkinter import filedialog, messagebox
import customtkinter

MODEL_TOKEN_LIMIT = 600
AVERAGE_CHARS_PER_TOKEN = 7 # Assuming an average of 5 characters per token for English

openai.api_key = os.environ.get('OPENAI_API_KEY')

# Global variables
default_dir = None
prompt_content = None
chunks_content = []
chunks_request = []
request_set = False
input_base_name = None
input_path = None
output_format = None
prompt_token_count = 0
block_size = 0

# Treading
processed_chunks = 0
lock = threading.Lock()

def clamp(x, min_val, max_val):
    return max(min_val, min(max_val, x))

def split_content_by_estimate(content):

    global block_size

    chunks = []
    content_len = len(content)
    start_idx = 0
    isFinal = False

    # Check if we're in the middle of the content
    while not isFinal:

        # Define the preliminary end index
        end_idx = clamp(start_idx + block_size, 0, content_len)

        if end_idx == content_len:
            isFinal = True

        # Try to adjust the end_idx to avoid cutting a word/sentence in the middle
        original_end_idx = end_idx

        while not isFinal and end_idx > start_idx and content[end_idx] not in [' ', '\n']:
            end_idx -= 1

        # If we looped back to the start index without finding a good breaking point,
        # then revert to the original end index
        if end_idx <= start_idx:
            end_idx = original_end_idx

        # Append this chunk to our list of chunks
        chunks.append(content[start_idx:end_idx])

        # Move the start index for the next chunk
        start_idx = end_idx

        if isFinal:
            break

    return chunks

def set_default_dir():
    global default_dir
    default_dir = filedialog.askdirectory(
        title="Select a Directory"
    )
    if default_dir:
        try:
            default_label.configure(text=default_dir)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Directory '{default_dir}' not found.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while reading the directory: {e}")

def open_prompt_file():
    global prompt_content, prompt_token_count, block_size, request_set
    prompt_file = filedialog.askopenfilename(
        title="Open Prompt File",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        initialdir="prompts"
    )
    if prompt_file:
        try:
            with open(prompt_file, "r", encoding="utf-8") as file:
                prompt_content = file.read()
            prompt_label.configure(text=prompt_file)
            encoding = tiktoken.get_encoding("cl100k_base")
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

            # calculate block size
            prompt_token_count = len(encoding.encode(prompt_content))
            max_tokens_for_content = MODEL_TOKEN_LIMIT - prompt_token_count
            block_size = max_tokens_for_content * AVERAGE_CHARS_PER_TOKEN

            # reset
            request_set = False
            chunk_label.configure(text=f"Not set yet")
            run_label.configure(text="Not replied yet")

        except FileNotFoundError:
            messagebox.showerror("Error", f"File '{prompt_file}' not found.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while reading the file: {e}")

def open_content_file():
    global input_base_name, input_path, default_dir, chunks_content, request_set

    if prompt_content == None:
        messagebox.showerror("Error", f"A prompt file is not found.")
        return
    
    initial_directory = default_dir if default_dir else None

    content_file = filedialog.askopenfilename(
        title="Open Content File",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        initialdir=initial_directory
    )
    
    input_base_name = os.path.splitext(os.path.basename(content_file))[0]
    input_path = os.path.dirname(content_file)

    if content_file:
        try:
            input_content = ""
            with open(content_file, "r", encoding="utf-8") as file:
                input_content = file.read()
            # split chunks
            chunks_content = split_content_by_estimate(input_content)
            content_label.configure(text=content_file)
            # reset
            request_set = False
            chunk_label.configure(text=f"Not set yet")
            run_label.configure(text="Not replied yet")
        except FileNotFoundError:
            messagebox.showerror("Error", f"File '{content_file}' not found.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while reading the file: {e}")    

def get_response_from_chatgpt(request):
    """Send the content to ChatGPT and return the response."""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": request}]
    )
    return response.choices[0].message["content"].strip()

def save_response(base_name, path, response, format):
    file_name = os.path.join(path, f"converted_{base_name}{format}")
    if file_name:
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(response)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving the file: {e}")

def append_chunks():
    global chunks_content, chunks_request, block_size, request_set, processed_chunks

    if not prompt_content or not chunks_content:
        messagebox.showerror("Error", "Please ensure both the prompt and input files are selected.")
        return

    # init
    chunks_request = []
    processed_chunks = 0

    chunk_label.configure(text=f"{len(chunks_content)} requests generated")
    encoding = tiktoken.get_encoding("cl100k_base")
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    index = 0
    for chunk in chunks_content:
        print(f"{index}th chunk: {len(encoding.encode(chunk))} tokens")
        chunks_request.append(chunk)
        index += 1

    request_set = True

def threaded_get_response(chunk_index, chunk, response_list):
    try:
        request = "\nPrompt:\n" + prompt_content + "\nText:\n" + chunk + "\n"
        response = get_response_from_chatgpt(request)
        with lock:
            response_list.append((chunk_index, response))
            global processed_chunks
            processed_chunks += 1
            print(f"{chunk_index} received: {processed_chunks}/{len(chunks_request)} completed")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred in thread {chunk_index}: {e}")

def get_response_and_save():
    global chunks_request, block_size, request_set

    if not prompt_content or not chunks_request:
        messagebox.showerror("Error", "Please ensure both the prompt and input files are selected.")
        return
    
    if not request_set:
        messagebox.showerror("Error", "Please ensure the SET button is selected.")
        return

    # init
    request_set = False

    # Calculate the max characters left after adding the prompt
    # Estimate max character count based on remaining tokens
    accumulated_response = ""
    response_list = []  # List to store tuples of (index, response)
    threads = []

    for i, chunk in enumerate(chunks_request):
        response_thread = threading.Thread(target=threaded_get_response, args=(i, chunk, response_list), daemon=True)
        response_thread.start()
        threads.append(response_thread)

    # Wait for all threads to finish
    for t in threads:
        t.join()

    # Save the accumulated response to one file
    # Sort responses by their index and accumulate them in the correct order
    response_list.sort(key=lambda x: x[0])
    for idx, response in response_list:
        accumulated_response += f"\n{idx + 1}.\n" + response + "\n"
    
    save_response(input_base_name, input_path, accumulated_response, output_format.get())
    print("All completed!")
    run_label.configure(text=f"Completed!")

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("green")
app = customtkinter.CTk()
app.title('Send Content/Prompt to ChatGPT Turbo 16k')
output_format = StringVar(value=".txt")

frame = customtkinter.CTkFrame(master=app)
frame.pack()

# Set default button
set_default_bt = customtkinter.CTkButton(frame, text="Set Default Content Directory", command=set_default_dir)
set_default_bt.pack()
default_label = customtkinter.CTkLabel(frame, text="No default directory set", wraplength=350)
default_label.pack()

# Open prompt button
open_prompt_bt = customtkinter.CTkButton(frame, text="Open Prompt File", command=open_prompt_file)
open_prompt_bt.pack()
prompt_label = customtkinter.CTkLabel(frame, text="No prompt file selected", wraplength=350)
prompt_label.pack()

# Open content button
open_content_bt = customtkinter.CTkButton(frame, text="Open Content File", command=open_content_file)
open_content_bt.pack()
content_label = customtkinter.CTkLabel(frame, text="No content file selected", wraplength=350)
content_label.pack()

# Set button
set_bt = customtkinter.CTkButton(frame, text="SET", command=append_chunks)
set_bt.pack()
chunk_label = customtkinter.CTkLabel(frame, text="Not set yet", wraplength=350)
chunk_label.pack()

# Run button
run_bt = customtkinter.CTkButton(frame, text="RUN", command=get_response_and_save)
run_bt.pack()
run_label = customtkinter.CTkLabel(frame, text="Not replied yet", wraplength=350)
run_label.pack()

# Progressbar
# progressBar = customtkinter.CTkProgressBar(
#     frame,
#     mode='determinate'
# )
# progressBar.pack()
# progressBar.set(0)

# Add option to select output format
output_format_label = customtkinter.CTkLabel(frame, text="Select Output Format:")
output_format_label.pack()
output_format_dropdown = OptionMenu(frame, output_format, ".tct", ".md", ".csv")
output_format_dropdown.pack()

frame.pack()
app.mainloop()