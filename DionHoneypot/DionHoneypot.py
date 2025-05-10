import logging
from logging.handlers import RotatingFileHandler
import argparse
import google.generativeai as genai
import json
from llamaapi import LlamaAPI
import sys
import os
import traceback
import random
import socket
import threading
import paramiko
from pathlib import Path
#Change honeypotLogger to just logging?
#Author: Declan Dean @ 2025

#TO DO
#Client Handle doesn't do backspaces or register movement keys
#Client Handle
    #Double check it breaks when \r doesn't show response either
#Only shutsdown when another attempt at connection is made?
#Swap to llama for testing
#Testing
    #Need to add response channel send so the listener can for testing
    #New case AI prompts
    #Inputs Outputs - Double check the C:\\Users\\
    #Client_IP in logging files
    #Write stress testing in diss for the connections
#AI Prompt changes all of them
#Removing username and password because it shouldn't require it?
#Generate fake IP Address? The client_ip address won't be any good for generation because it is the attacker's IP address so make a new one?
    #Take in the attacker's IP address and then generate an IP address in that area?

# Constants and Sources
SSH_BANNER = "SSH-2.0-MySSHServer_1.0"
#Base directory  of where user is running honeypot from
base_dir = base_dir = Path(__file__).parent.parent
server_key = base_dir / 'DionHoneypot' / 'static' / 'server.key'
honeypot_log_local_file_path = base_dir / 'DionHoneypot' / 'log_files' / 'audits.log'
host_key = paramiko.RSAKey(filename=server_key) #change to all caps?

UP_KEY = '\x1b[A'.encode()
DOWN_KEY = '\x1b[B'.encode()
RIGHT_KEY = '\x1b[C'.encode()
LEFT_KEY = '\x1b[D'.encode()
BACK_KEY = '\x7f'.encode()

#Logger
#Need to check if it makes a new file or if it requires to file to be there
#Check to make sure all the logging is changed to current
logging.basicConfig(
    handlers=[RotatingFileHandler(honeypot_log_local_file_path, maxBytes=100000, backupCount=10)],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
#Create logger
honeypot_logger = logging.getLogger('honeypotLogger')

#Paramiko Invoke shell for powershel terminal
#Socket for IP address. Paramiko for shell?


# Configure Google Generative AI API
#Gemini
key = ""
model = genai.GenerativeModel('gemini-1.5-pro-latest')
genai.configure(api_key=key)

#Llama
#llama = LlamaAPI("10d14105-3136-415c-a7b2-010f0a0125c5")

# Global scope
current_user = None
file_structure = None

#Paramiko Server
#Changes to be made
class Server(paramiko.ServerInterface):
    #Add variable so that the conditional self.input_username is checked against that rather than it being hard coded in None
    #Not important rn

    def __init__(self, client_ip, input_username=None, input_password=None):
        self.event = threading.Event()
        self.client_ip = client_ip
        self.input_username = input_username
        self.input_password = input_password

    def check_channel_request(self, kind, chanid):
        honeypot_logger.info('client called check_channel_request ({}): {}'.format(self.client_ip, kind))
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
    
    def get_allowed_auths(self, username):
        honeypot_logger.info('client called get_allowed_auths ({}) with username {}'.format(self.client_ip, username))
        return "password"
        
    def check_auth_password(self, username, password):
        honeypot_logger.info('new client credentials ({}): username: {}, password: {}'.format(
                    self.client_ip, username, password))
        if self.input_username is not None and self.input_password is not None:
            if username == self.input_username and password == self.input_password:
                return paramiko.AUTH_SUCCESSFUL
            else:
                return paramiko.AUTH_FAILED
        else:
            return paramiko.AUTH_SUCCESSFUL
    
    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    #Pass in username here?
    def check_channel_exec_request(self, username, channel, command):
        command_text = str(command.decode("utf-8"))
        honeypot_logger.info('client sent command via check_channel_exec_request ({}): {}'.format(self.client_ip, username, command))
        return True
    
#Client Handler
#Changes to be made
def client_handle(client, addr):
    client_ip = addr[0]
    honeypot_logger.info('New connection from: {}'.format(client_ip))
    print(f"{client_ip} connected to server.")
    try:
    
        # Initlizes a Transport object using the socket connection from client.
        transport = paramiko.Transport(client)
        transport.add_server_key(host_key)
        transport.local_version = SSH_BANNER
        # Creates an instance of the SSH server, adds the host key to prove its identity, starts SSH server.
        server = Server(client_ip)
        try:
            transport.start_server(server=server)

        except paramiko.SSHException:
            print('*** SSH negotiation failed.')
            raise Exception("SSH negotiation failed")


        # Establishes an encrypted tunnel for bidirectional communication between the client and server.
        channel = transport.accept(10)
        if channel is None:
            print('*** No channel (from '+client_ip+').')
            raise Exception("No channel")
        
        #channel.settimeout(10)

        if transport.remote_mac != '':
            honeypot_logger.info('Client mac ({}): {}'.format(client_ip, transport.remote_mac))

        if transport.remote_compression != '':
            honeypot_logger.info('Client compression ({}): {}'.format(client_ip, transport.remote_compression))

        if transport.remote_version != '':
            honeypot_logger.info('Client SSH version ({}): {}'.format(client_ip, transport.remote_version))
            
        if transport.remote_cipher != '':
            honeypot_logger.info('Client SSH cipher ({}): {}'.format(client_ip, transport.remote_cipher))

        server.event.wait(10)
        if not server.event.is_set():
            honeypot_logger.info('** Client ({}): never asked for a shell'.format(client_ip))
            raise Exception("No shell request")
        #Right placement?
        #Testing purpose file_structure and current_directory need to be changed for linux
        generate_fake_user()
        generate_fake_file_structure()
        current_directory = f"/home/{current_user}"
        try:
            channel.send("Welcome to Ubuntu 18.04.4 LTS (GNU/Linux 4.15.0-128-generic x86_64)\r\n\r\n")
            run = True
            while run:
                channel.send("$ ")
                command = ""
                while not command.endswith("\r"):
                    data = channel.recv(1024)
                    print(client_ip+"- received:",data) #debug
                    # Echo input to psuedo-simulate a basic terminal
                    if(
                        data != UP_KEY
                        and data != DOWN_KEY
                        and data != LEFT_KEY
                        and data != RIGHT_KEY
                        and data != BACK_KEY
                    ):
                        #Decode issue - 
                        #!!! Exception: <class 'AttributeError'>: 'str' object has no attribute 'decode'
                        channel.send(data)
                        command += data.decode("utf-8") #This takes in and adds the input from client to the command each time
                
                channel.send("\r\n")
                command = command.rstrip()
                logging.info('Command receied ({}): {}'.format(client_ip, command))

                if command == "exit":
                    #Settings?
                    #settings.addLogEntry("Connection closed (via exit command): " + client_ip + "\n")
                    run = False

                else:
                    ai_reponse = handle_command(command, channel, current_directory, file_structure, client_ip, current_user)
                    channel.send(ai_reponse + "\r\n")

        except Exception as err:
            print('!!! Exception: {}: {}'.format(err.__class__, err))
            try:
                transport.close()
            except Exception:
                pass

        channel.close()

    except Exception as err:
        print('!!! Exception: {}: {}'.format(err.__class__, err))
        try:
            transport.close()
        except Exception:
            pass
    '''
        # Set up user and file system
        generate_fake_user()
        generate_fake_file_structure()
        
        #Line breaks is the problem when using the prompt?
        standard_banner = "Welcome to Ubuntu 22.04 LTS (Jammy Jellyfish)!\n"
        
        # Endless Banner: If tarpit option is passed, then send 'endless' ssh banner.
        if tarpit: #Nessecary?
            endless_banner = standard_banner * 100
            for line in endless_banner.splitlines:
                channel.send(line)
                time.sleep(8) #Hardcoded Delay?
            # Standard Banner: Send generic welcome banner to impersonate server.
        else:
            channel.send(standard_banner)
            # Send channel connection to deceptive_terminal for interpretation.
            #deceptive_terminal should then send it to handle_command

        # Start shell interaction
        handle_command(channel, client_ip, current_directory, file_structure, current_user)

    except Exception as error:
        print(error)
        print("!!! Exception !!!")
    finally:
        try:
            transport.close()
        except Exception:
            pass
        
        client.close()
        '''

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
        '''api_request_json = {
            "model": "llama3.1-70b",
            "messages": [{"role": "user", "content": ai_prompt}],
            "stream": False,
        }
        response = llama.run(api_request_json)
        file_structure = response.json().get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        print("Stored File Structure:" + file_structure)
        '''
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

#need channel?
def handle_command(command, channel, current_directory, file_structure, client_ip, current_user):
    response = ""
    match command:
        #Failsafe exit
        case "exit" | "logout":
            return False
        #Navigation
        case command.startswith("cd") | command.startswith("pwd") | command.startswith("dir"):
            #prompt: command, current directory, file structure
            return True
        #File Manipulation
        case command.startswith("mkdir") | command.startswith("rm") | command.startswith("del") | command.startswith("touch"):
            #prompt: command, current directory, file structure
            return True
        #System Information
        case "whoami" | "hostname" | "ipconfig" | "systeminfo":
            #prompt command, client_ip, current_user
            return True
        case command.startswith("cat") | command.startswith("type"):
            #prompt command, current_directory, file_structure
            return True
        case _:
            try:
        # Fallback to AI/LLM
        #Inform AI of the circumstances as much as possible or? Enforce the AI into a role?
        #Introduce formatting to the prompt?
        #Prompt needs to be changed for linux? Discuss a way to check the terminal and how that could also be a variable to feed to the AI
                ai_prompt = f"""
                You are simulating a Linux terminal running on a corporate desktop. 
                Only respond with the raw output **exactly** as the terminal would—no explanations, markdown, or extra comments.
                The current user is: {current_user}
                The command entered was: {command}
                The current directory is: {current_directory}
                The file structure is as follows (JSON): 
                {file_structure}
                If the command is valid for a terminal, return the realistic output (with formatting, spacing, etc.). 
                If the command is invalid, respond exactly how Linux would (e.g., "The term '{command}' is not recognized as the name of a cmdlet, function, script file, or operable program").
                """
                response = model.generate_content(ai_prompt)
                return response.text.strip()
            except Exception as err:
                print('!!! Exception: {}: {}'.format(err.__class__, err))
    return True

'''
    #byte or string?
    #Grant uses byte but simon uses string 
    #match cases to be added
    try:
        # Fallback to AI/LLM
        #Inform AI of the circumstances as much as possible or? Enforce the AI into a role?
        #Introduce formatting to the prompt?
        ai_prompt = f"""
        You are simulating a Windows PowerShell terminal running on a corporate desktop. 
        Only respond with the raw output **exactly** as the terminal would—no explanations, markdown, or extra comments.
        The current user is: {current_user}
        The command entered was: {command}
        The current directory is: {current_directory}
        The file structure is as follows (JSON): 
        {file_structure}
        If the command is valid for a terminal, return the realistic output (with formatting, spacing, etc.). 
        If the command is invalid, respond exactly how PowerShell would (e.g., "The term '{command}' is not recognized as the name of a cmdlet, function, script file, or operable program").
        """
        response = model.generate_content(ai_prompt)
                response = response = client.chat.completions.create(
            model="llama3.1-70b",
            messages=[
                {"role": "system", "content": "Assistant is a large language model trained by Llama AI."},
                {"role": "user", "content": ai_prompt}
            ]
        )
        
        return response.text.strip()
    except Exception as err:
        print('!!! Exception: {}: {}'.format(err.__class__, err))
        '''

#Honeypot
def deceptive_terminal(port, bind):
    # Open a new socket using TCP, bind to port.
    try:
        socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socks.bind((bind, port))
    except Exception as err:
        print('*** Bind failed: {}'.format(err))
        traceback.print_exc()
        sys.exit(1)

    threads = []
    while True:
        try:
            socks.listen(100) #Handle 100 connections
            print('Listening for connection on port {} ...'.format(port))
            client, addr = socks.accept()
        except Exception as err:
            print('*** Listen/accept failed: {}'.format(err))
            traceback.print_exc()
        new_thread = threading.Thread(target=client_handle, args=(client, addr))
        new_thread.start()
        threads.append(new_thread)
    #Unreachable? #For loop and keyboardInterrupt logic?
    for thread in threads:
        thread.join()
#Needs to be reworked for the SSH Server
if __name__ == "__main__":
    #Password and username taken out if need be add parser.add_arugment for them
    parser = argparse.ArgumentParser(description='Run an SSH honeypot server')
    parser.add_argument("--port", "-p", help="The port to bind the ssh server to (default 22)", default=2222, type=int, action="store")
    parser.add_argument("--bind", "-b", help="The address to bind the ssh server to", default="", type=str, action="store")
    args = parser.parse_args()
    deceptive_terminal(args.port, args.bind)
