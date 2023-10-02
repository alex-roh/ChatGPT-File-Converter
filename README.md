# ChatGPT File Converter
## Overview
<div style="text-align:center; padding: 20px;">
  <img src="https://github.com/alex-roh/ChatGPT-File-Converter/assets/54312875/ed9e7dd5-18d3-4ed7-b668-06381a2a74be" alt="GUI screen" style="height: 400px;">
</div>

The ChatGPT File Converter is a Python program that streamlines interactions with the ChatGPT model. It simplifies the process of splitting files, attaching prompts to each segment, sending them to the ChatGPT model for processing, and then concatenating the responses into a final output file.

## Features
- **File Splitting**: Easily divide input files into smaller segments.
- **Prompt Attachment**: Load and append your prompt file to each file segment.
- **ChatGPT Interaction**: Streamlined interaction with the ChatGPT model to obtain responses for each segment.
- **Response Concatenation**: Reassemble the responses into a coherent output file.

## Usage
1. **Installation**: Clone this repository to your local machine.

    ```bash
    git clone https://github.com/alex-roh/ChatGPT-File-Converter.git
    ```

2. **Setup**: Install the necessary dependencies by running:

    ```bash
    pip install -r requirements.txt
    ```

3. **Configuration**: Customize your settings in the config.yaml file, specifying the input file, output file, and any other desired parameters.

4. **Execution**: Run the program using the following command:

    ```bash
    python chatgpt_file_converter.py
    ```

5. **Review Results**: Once the program finishes, you will find the concatenated responses in the specified output file.

## Contribution
Contributions are welcome! If you have ideas for improvements or new features, please feel free to submit issues or pull requests.

## License
This project is licensed under the MIT License.

---

Note: This project is primarily developed for simplifying interactions with the ChatGPT model and can be used for various applications such as text generation, summarization, and more.