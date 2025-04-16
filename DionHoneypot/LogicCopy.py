def handle_command(channel, client_ip, bad_actor_input, current_directory, file_structure, current_user):
    #Logic wrong here
    #The match command needs some AI in the responses to be able to navigate and produce outputs?
    #Consistency problems in the AI could be resolved here?
    #Using elif instead of switch? but also using swtich?
    #No mkdir? Logic needs rework so that AI is allowed to alter and change the file_struture
    #Convert from f"" to b""?
    #String is causing errors in the code so b"" is more robust? But it needs to go to AI so?
    #b because it can only contain ASCII and numbers
    command = bad_actor_input
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



def unified_shell(channel, client_ip, model):
    current_directory = "C:\\Users\\corpuser1"
    current_user = "corpuser1"
    file_structure = {
        "C:\\Users\\corpuser1": ["Documents", "Downloads", "Desktop"],
        "C:\\Users\\corpuser1\\Documents": ["resume.docx", "budget.xlsx"],
        # Add more structure if needed
    }

    channel.send(b"corporate-jumpbox2$ ")
    command = b""

    while True:
        char = channel.recv(1)
        if not char:
            channel.close()
            break

        command += char
        channel.send(char)  # Echo char back

        if char == b"\r":
            decoded_cmd = command.strip().decode(errors='ignore')
            response = handle_combined_command(decoded_cmd, current_directory, file_structure, current_user, model)

            # Send response and prompt again
            channel.send(b"\n" + response.encode(errors='ignore') + b"\r\n")
            channel.send(b"corporate-jumpbox2$ ")
            command = b""  # Reset command

def handle_combined_command(command, current_directory, file_structure, current_user, model):
    #AI fallback if all other commands fail document and explain this approach and that I had this idea in mind
    #But mention that doing this would just mean i'm creating the SSH honeypot myself and goes against the goal of the project
    #So new goal to have as little basic commands as possible but still giving guidance to the AI where needed
    #Could use AI to generalise some of these commands and prompts for example
    #Remove and Create directories would require the AI to interact with the file_strucutre so the command could be passed through
    #And in that match case using OR operators the AI prompt can be further expanded to give permission to alter the file_structure?
    '''Introduce command history or partial autocomplete to improve realism.

Track attacker behavior across sessions to personalize responses (e.g., dynamic bait).

Extend command support for Windows (e.g., ipconfig, tasklist, netstat) and Linux (sudo, nano, etc.).

Consider a plugin system where AI can be toggled for specific commands.'''

    if command == "exit":
        return "Goodbye!"
    elif command == "pwd":
        return current_directory
    elif command == "whoami":
        return current_user
    elif command == "ls" or command == "dir":
        return "\n".join(file_structure.get(current_directory, []))
    elif command.startswith("cd "):
        new_dir = command[3:].strip()
        if new_dir == "..":
            parts = current_directory.split("\\")
            current_directory = "\\".join(parts[:-1]) if len(parts) > 1 else current_directory
        elif new_dir in file_structure.get(current_directory, []):
            current_directory = f"{current_directory}\\{new_dir}"
        else:
            return "The system cannot find the path specified."
        return f"Changed directory to {current_directory}"
    elif command == "cat jumpbox1.conf":
        return "Go to deeboodah.com"
    else:
        # AI fallback
        prompt = f"""You are a Windows PowerShell terminal simulation running on a corporate desk computer.
Current user: {current_user}
Current directory: {current_directory}
File structure: {file_structure}
User typed: {command}
Respond with a plausible but deceptive output simulating PowerShell.
Avoid suggesting actual exploitation steps."""
        return model.generate_content(prompt).text.strip()
    


    #Logic wrong here
    #The match command needs some AI in the responses to be able to navigate and produce outputs?
    #Consistency problems in the AI could be resolved here?
    #Using elif instead of switch? but also using swtich?
    #No mkdir? Logic needs rework so that AI is allowed to alter and change the file_struture
    #Convert from f"" to b""?
    #String is causing errors in the code so b"" is more robust? But it needs to go to AI so?
    #b because it can only contain ASCII and numbers
    '''Convert all string responses to bytes before channel.send().

Replace print() with channel.send().

Make the shell terminal type (PowerShell vs Bash) configurable.

Normalize input: Convert from bytes to str at parsing, then convert output back.'''
    #current_directory = "C:\\Users\\" + current_user

    #Suggested changes
    '''
    elif command.startswith("mkdir "):
    new_dir = command[6:].strip()
    file_structure.setdefault(current_directory, []).append(new_dir)
    return f"Directory {new_dir} created."
    '''
        #Changes being made
    '''channel.send(b"C:\\Users\\Admin> ")
    command = b""
    while True:
        char = channel.recv(1)
        if not char:
            break
        channel.send(char)
        command += char
        if char == b"\r":
            response = handle_command(channel, client_ip, command.strip().decode())
            channel.send(response.encode() + b"\r\n")
            channel.send(b"C:\\Users\\Admin> ")
            command = b""
            '''

    command = bad_actor_input
    match command:
        case "exit":
            channel.send("\nExiting the terminal honeypot. Goodbye!")
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
                channel.send("The system cannot find the path specified.")
        
        case "dir":
            channel.send(generate_fake_directory_listing(current_directory, file_structure))
        
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
            channel.send(ai_response)

    return True
