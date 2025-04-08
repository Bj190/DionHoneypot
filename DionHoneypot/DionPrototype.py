import logging
from logging.handlers import RotatingFileHandler
import google.generativeai as genai
import random
import socket

#Socket for IP address. Paramiko for shell?

#More information logging to be implemented like IP Address or Directory.

# Logging setup for auditing bad actor inputs.
logging_format = logging.Formatter('%(asctime)s %(message)s')
honeypot_logger = logging.getLogger('TerminalHoneypotLogger')
honeypot_logger.setLevel(logging.INFO)
honeypot_handler = RotatingFileHandler('terminal_honeypot.log', maxBytes=10000, backupCount=5)
honeypot_handler.setFormatter(logging_format)
honeypot_logger.addHandler(honeypot_handler)

# Configure Google Generative AI API
key = ""

genai.configure(api_key=key)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# Global scope
current_user = None
file_structure = None

# Desktop username Generation
#Testing - To be changed later
first_names = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Charles", "Thomas",
    "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Paul", "Andrew", "George", "Edward", "Samuel",
    "Benjamin", "Jack", "Henry", "Isaac", "Oliver", "Harry", "Ethan", "Oscar", "Liam", "Mary", "Jennifer", 
    "Linda", "Patricia", "Elizabeth", "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Betty", "Helen", "Sandra", 
    "Ashley", "Dorothy", "Amanda", "Ruth", "Sharon", "Michelle", "Kimberly", "Emily", "Melissa", "Laura", 
    "Deborah", "Carolyn", "Rebecca", "Rachel", "Shirley"
]
last_names = [
    "Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Moore", "Davis", "Clark", "Lewis",
    "Roberts", "Walker", "Young", "Harris", "Martin", "Jackson", "Thompson", "White", "King", "Scott",
    "Adams", "Baker", "Nelson", "Carter", "Mitchell", "Perez", "Reed", "Cook", "Murphy", "Bailey", "Cooper",
    "Morris", "Stewart", "Price", "Hughes", "Wood", "Cole", "Ryan", "Ward", "Allen", "Ross", "West", "Turner", 
    "Evans", "Gray", "Shaw", "Richards"
]

# Function to generate a fake username
# Randomly creates a user from arrays and 3 numbers
def generate_fake_user():
    global current_user
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    random_digits = ''.join(str(random.randint(0, 9)) for _ in range(3))
    current_user = f"{first_name[0].lower()}{last_name.lower()}{random_digits}"
    print(f"Generated username: {current_user}")

def generate_fake_file_structure():
    global file_structure
    # Debug
    if not current_user:
        print("Error: current_user is not defined. Please generate a username first.")
        return {}

    ai_prompt = f"""
    You are simulating a corporate Windows environment. 
    Generate a realistic file structure for a user named {current_user}. 
    The file structure should include directories such as 'Desktop', 'Documents', 'Downloads', and any common corporate directories like 'Program Files' or 'Users'.
    The file structure must be returned in JSON format only, like:
    {{
        "C:\\": ["Program Files", "Users", "Windows"],
        "C:\\Users":["{current_user}", "Public", "Admin"],
        "C:\\Users\\{current_user}": ["Desktop", "Documents", "Downloads"]
    }}
    DO NOT include any text, explanations, or terminal-like output.
    """
    
    try:
        response = model.generate_content(ai_prompt)
        file_structure = response.text.strip()
        print("Stored File Structure:" + file_structure)
        
    except Exception as e:
        print(f"Error generating file structure: {e}")
        return {}

def generate_fake_directory_listing(path, file_structure):
    if path in file_structure:
        return "\n".join(file_structure[path])
    return "The system cannot find the path specified."

def handle_command(bad_actor_input, current_directory, file_structure, current_user):
    # Logic wrong here
    #The match command needs some AI in the responses to be able to navigate and produce outputs?
    #Consistency problems in the AI could be resolved here?
    #Using elif instead of switch? but also using swtich?
    #No mkdir?
    command = bad_actor_input.lower()
    match command:
        case "exit":
            print("\nExiting the terminal honeypot. Goodbye!")
            return False
        case _ if command.startswith("cd "):
            # Change directory command
            new_dir = bad_actor_input[3:].strip()
            if new_dir == "..":
                parts = current_directory.split("\\")
                if len(parts) > 1:
                    current_directory = "\\".join(parts[:-1])
                else:
                    current_directory = "C:\\"
            elif new_dir in file_structure.get(current_directory, []):
                # Simulate changing to the new directory
                current_directory = f"{current_directory}\\{new_dir}"
                ai_prompt = f"""You are a windows PowerShell terminal simulation running on a corporate desk computer.
                The current user is {current_user}.
                The file structure for {current_user} is as follows:
                {file_structure}
                The user is currently in {current_directory}.
                The user has entered the following command: {bad_actor_input}.
                Respond with a plausible but deceptive output that simulates the behavior of a corporate system's PowerShell terminal.
                Do not provide any information unless directly requested by the user. Avoid attempting to interact with the system or perform any actions outside of a standard PowerShell command environment.
                """
            else:
                print("The system cannot find the path specified.")
        
        case "dir":
            print(generate_fake_directory_listing(current_directory, file_structure))
        
        case _:
            ai_prompt = f"""
                You are a Windows PowerShell terminal simulation running on a corporate desk computer.
                The user has entered the following command: {bad_actor_input}.
                The current user is {current_user}.
                The file structure for {current_user} is as follows:
                {file_structure}
                Respond with a plausible but deceptive output that simulates the behavior of a corporate system's PowerShell terminal.
                Do not provide any information unless directly requested by the user. Avoid attempting to interact with the system or perform any actions outside of a standard PowerShell command environment.
                """
            response = model.generate_content(ai_prompt)
            ai_response = response.text.strip()
            print(ai_response)

    return True


def deceptive_terminal():
    print("Welcome to the Secure Server Terminal. Please enter your commands below.")
    generate_fake_user()
    generate_fake_file_structure()
    current_directory = f"C:\\Users\\{current_user}"
    while True:
        try:
            fake_prompt = f"{current_directory}> "
            bad_actor_input = input(f"{fake_prompt} ")
            honeypot_logger.info(f"Bad Actor Command: {bad_actor_input}")
            if not handle_command(bad_actor_input, current_directory, file_structure, current_user):
                break
        except KeyboardInterrupt:
            print("\nExiting the terminal honeypot. Goodbye!")
            break
        except Exception as e:
            honeypot_logger.error(f"Error: {e}")
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    deceptive_terminal()
