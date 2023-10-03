import os
import openai
import tiktoken
import threading
import inspect

MODEL_TOKEN_LIMIT = 700
AVERAGE_CHARS_PER_TOKEN = 7 # Assuming an average of 5 characters per token for English
openai.api_key = os.environ.get('OPENAI_API_KEY')

class GPTHandler:

    # class variables
    lock = threading.Lock()
    encoding = None
    processed_chunks = 0

    def __init__(self):
        pass

    @staticmethod
    def __get_response_from_chatgpt(request):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": request}
            ]
        ) # TODO: Add a feature that allows the user to select the model
        return response.choices[0].message["content"].strip()

    @staticmethod
    def __threaded_get_response(prompt_content, chunks_request, chunk_index, chunk, response_list):
        try:
            request = "\nPrompt:\n" + prompt_content + "\nText:\n" + chunk + "\n"
            response = GPTHandler.__get_response_from_chatgpt(request)
            with GPTHandler.lock:
                response_list.append((chunk_index, response))
                GPTHandler.processed_chunks += 1
                print(f"{chunk_index} received: {GPTHandler.processed_chunks}/{len(chunks_request)} completed ({len(GPTHandler.encoding.encode(response))} tokens)")
        except Exception as e:
            print(f"{inspect.currentframe().f_code.co_name}: An error occurred in thread {chunk_index}: {e}")

    @staticmethod
    def start_threaded_get_response(prompt_content, chunks_request):

        if not prompt_content or not chunks_request:
            print(f"{inspect.currentframe().f_code.co_name}: Please ensure both the prompt and input files are selected.")
            return

        # Calculate the max characters left after adding the prompt
        # Estimate max character count based on remaining tokens
        accumulated_response = ""
        response_list = []  # List to store tuples of (index, response)
        threads = []

        for idx, chunk in enumerate(chunks_request):
            response_thread = threading.Thread(target=GPTHandler.__threaded_get_response, args=(prompt_content, chunks_request, idx, chunk, response_list), daemon=True)
            response_thread.start()
            threads.append(response_thread)

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        # Save the accumulated response to one file
        # Sort responses by their index and accumulate them in the correct order
        response_list.sort(key=lambda x: x[0])
        for idx, response in response_list:
            accumulated_response += f"\n{idx + 1}.\n" + response + "\n"
        
        return accumulated_response
            
    @staticmethod
    def calculate_block_size(prompt_content):
        # Get the encoding based on the model
        GPTHandler.encoding = tiktoken.get_encoding("cl100k_base")
        GPTHandler.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

        # Determine the block size based on the prompt token count
        prompt_token_count = len(GPTHandler.encoding.encode(prompt_content))
        max_tokens_for_content = MODEL_TOKEN_LIMIT - prompt_token_count
        block_size = max_tokens_for_content * AVERAGE_CHARS_PER_TOKEN
        
        return block_size

    @staticmethod
    def set_chunks_request(chunks_content):
        chunks_request = []
        index = 0

        for chunk in chunks_content:
            print(f"{index}th chunk: {len(GPTHandler.encoding.encode(chunk))} tokens")
            chunks_request.append(chunk)
            index += 1
        
        return chunks_request
        

