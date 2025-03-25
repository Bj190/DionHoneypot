import logging
from logging.handlers import RotatingFileHandler
import google.generativeai as genai

# Configure Google Generative AI API
key = ""  # Replace with your API key

genai.configure(api_key=key)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# Logging setup for auditing bad actor inputs.
logging_format = logging.Formatter('%(asctime)s %(message)s')
honeypot_logger = logging.getLogger('TerminalHoneypotLogger')
honeypot_logger.setLevel(logging.INFO)
honeypot_handler = RotatingFileHandler('terminal_honeypot.log', maxBytes=2000, backupCount=5)
honeypot_handler.setFormatter(logging_format)
honeypot_logger.addHandler(honeypot_handler)

def deceptive_terminal():
    """Simulated command prompt for a honeypot."""
    print("Welcome to the Secure Server Terminal. Please enter your commands below.")
    fake_prompt = "C:\\>"  # Simulates a Windows-like command prompt
    
    while True:
        try:
            # Capture input from the bad actor.
            bad_actor_input = input(f"{fake_prompt} ")

            # Log the bad actor's input.
            honeypot_logger.info(f"Bad Actor Command: {bad_actor_input}")

            ai_prompt = f"""
            You are a Windows PowerShell terminal simulation running on a corporate desk computer. 
            The user has entered the following command: {bad_actor_input}.
            Respond with a realistic but fabricated output that simulates the behavior of a corporate system's PowerShell terminal. 
            Do not provide any information unless directly requested by the user. Avoid attempting to interact with the system or perform any actions outside of a standard PowerShell command environment.
            Simulate fake file structures, processes, and network information relevant to an average corporate setup. Track fabricated assets internally and ensure they remain consistent across multiple inputs.
            Respond concisely and strictly within the scope of the command entered.
            """
            # Create a prompt for Gemini Pro to generate deceptive responses.
            #ai_prompt = f"""
            #You are simulating a Windows PowerShell terminal on a corporate desk computer. 
            #The user has entered the following command: {bad_actor_input}. 
            #Respond with a plausible but deceptive output, mimicking a real terminal environment. 
            #Do not provide any information unless specifically requested. 
            #Only show fake file structures, processes, or network information relevant to the command entered.
            #You must consistently track the fabricated assets (such as files, processes, or network connections) 
            #and ensure the environment remains coherent across interactions.
            #Limit your responses to terminal-like output only, with no extra commentary or explanations.
            #"""

            # Generate response using Gemini Pro
            response = model.generate_content(ai_prompt)

            # Extract and print the AI's response
            ai_response = response.text.strip()
            print(ai_response)

        except KeyboardInterrupt:
            print("\nExiting the terminal honeypot. Goodbye!")
            break
        except Exception as e:
            honeypot_logger.error(f"Error: {e}")
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    deceptive_terminal()