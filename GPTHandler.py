import os
import openai
import tiktoken
import threading
import inspect
import logging, sys

MAX_TOKENS_FOR_CURRENT_MODEL = 2048 # TODO: Add a feature that allows the user to select the model
CHUNK_TOKEN_LIMIT = 2000
SAFETY_MARGIN = 300
AVERAGE_CHARS_PER_TOKEN = 7
openai.api_key = os.environ.get('OPENAI_API_KEY')

class GPTHandler:

    # class variables
    lock = threading.Lock()
    encoding = tiktoken.get_encoding("cl100k_base")
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    processed_chunks = 0

    @staticmethod
    def __get_response_from_chatgpt(prompt, content):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "assistant", "content": "The input file is the content of the user (role)"},
                {"role": "user", "content": content},
            ]
        ) # TODO: Add a feature that allows the user to select the model
        return response.choices[0].message["content"].strip()

    @staticmethod
    def __threaded_get_response(prompt_content, num_chunks, chunk_index, chunk, response_list, callback=None):
        try:
            prompt = prompt_content
            response = GPTHandler.__get_response_from_chatgpt(prompt, chunk)
            with GPTHandler.lock:
                response_list.append((chunk_index, response))
                GPTHandler.processed_chunks += 1
                print(f"{chunk_index + 1} received: {GPTHandler.processed_chunks}/{num_chunks} completed ({GPTHandler.get_token_count(response)} tokens)")
                if callback:
                    callback(GPTHandler.processed_chunks)
        except Exception as e:
            print(f"{inspect.currentframe().f_code.co_name}: An error occurred in thread {chunk_index}: {e}")

    @staticmethod
    def start_threaded_get_response(prompt_content, chunks_content, callback=None):

        if not prompt_content or not chunks_content:
            print(f"{inspect.currentframe().f_code.co_name}: Please ensure both the prompt and input files are selected.")
            return

        # Calculate the max characters left after adding the prompt
        # Estimate max character count based on remaining tokens
        accumulated_response = ""
        response_list = []  # List to store tuples of (index, response)
        threads = []
        num_chunks = len(chunks_content)

        for idx, chunk in enumerate(chunks_content):
            response_thread = threading.Thread(target=GPTHandler.__threaded_get_response, args=(prompt_content, num_chunks, idx, chunk, response_list, callback), daemon=True)
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
    def get_token_count(content):
        return len(GPTHandler.encoding.encode(content))
            
    @staticmethod
    def calculate_chunk_chars(prompt_content, language):
        # Determine the average characters per token based on the language
        if language == "English":
            AVERAGE_CHARS_PER_TOKEN = 7
        elif language == "Korean":
            AVERAGE_CHARS_PER_TOKEN = 30
        else:
            print(f"{inspect.currentframe().f_code.co_name}: Language not supported.")
            return 0

        # Determine the block size based on the prompt token count
        prompt_token_count = GPTHandler.get_token_count(prompt_content)

        if prompt_token_count >= CHUNK_TOKEN_LIMIT:
            print(f"{inspect.currentframe().f_code.co_name}: The prompt is too long.")
            return 0

        max_tokens_for_content = CHUNK_TOKEN_LIMIT - prompt_token_count
        chunk_chars = max_tokens_for_content * AVERAGE_CHARS_PER_TOKEN

        print(f"{inspect.currentframe().f_code.co_name}: max_tokens_for_content: {max_tokens_for_content}, chunk_chars: {chunk_chars}")

        if chunk_chars > (MAX_TOKENS_FOR_CURRENT_MODEL * AVERAGE_CHARS_PER_TOKEN):
            chunk_chars = (MAX_TOKENS_FOR_CURRENT_MODEL * AVERAGE_CHARS_PER_TOKEN) - (SAFETY_MARGIN * AVERAGE_CHARS_PER_TOKEN)
        
        return chunk_chars
        

