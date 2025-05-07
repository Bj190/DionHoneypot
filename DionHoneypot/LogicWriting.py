def handle_command(channel, client_ip, bad_actor_input, current_directory, file_structure, current_user):
    channel.send(b"corporate-jumpbox2$ ")
    command = b""
    #Foreach logging?
    while True:  
        char = channel.recv(1)
        channel.send(char)
        if not char:
            channel.close()

        command += char
        command.strip()
        #AI prompts go here
        #In a switch case it all needs to channel.send?
        #Grouping commands together into the same AI prompts

        match command:
            case b'exit':
                channel.send("\nExiting the terminal honeypot. Goodbye!")
                return False
            case b'pwd':
                response = b"\n" + b"\\usr\\local" + b"\r\n"
                funnel_logger.info(f'Command {command.strip()}' + "executed by " f'{client_ip}')
            case b'whoami':
                response = b"\n" + b"corpuser1" + b"\r\n" #???
                funnel_logger.info(f'Command {command.strip()}' + "executed by " f'{client_ip}')
            case b'ls':
                response = b"\n" + b"jumpbox1.conf" + b"\r\n"
            case b'cat jumpbox1.conf':
                response = b"\n" + b"Go to deeboodah.com" + b"\r\n"
            case b'mkdir': #or remove
                #AI prompt which lets the AI alter the file structure and records the outputs
            case _:
                response = b"\n" + bytes(command.strip()) + b"\r\n"
                funnel_logger.info(f'Command {command.strip()}' + "executed by " f'{client_ip}')
                channel.send(response)
                channel.send(b"corporate-jumpbox2$ ")
                command = b""

    command = bad_actor_input
    match command:
        case "exit":
            channel.send("\nExiting the terminal honeypot. Goodbye!")
            return False
        #Error is theres a space between
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


def client_handle(client, addr, username, password, tarpit=False, current_directory=None, file_structure=None, current_user=None):
    client_ip = addr[0]
    print(f"{client_ip} connected to server.")
    
    try:
        transport = paramiko.Transport(client)
        transport.local_version = SSH_BANNER
        server = Server(client_ip=client_ip, input_username=username, input_password=password)
        transport.add_server_key(host_key)
        transport.start_server(server=server)

        channel = transport.accept(100)
        if channel is None:
            print("No channel was opened.")
            return

        if tarpit:
            endless_banner = "Welcome to Ubuntu 22.04 LTS (Jammy Jellyfish)!\r\n" * 100
            for line in endless_banner.splitlines():
                channel.send(line + "\r\n")
                time.sleep(8)
        else:
            channel.send("Welcome to Ubuntu 22.04 LTS (Jammy Jellyfish)!\r\n\r\n")

        if current_directory is None:
            current_directory = f"C:\\Users\\{current_user}"

        while True:
            # Send prompt to attacker
            channel.send(f"{current_directory}> ")

            # Read the command from the channel
            bad_actor_input = ""
            while True:
                char = channel.recv(1)
                if not char:
                    break
                if char in (b"\r", b"\n"):
                    channel.send("\r\n")
                    break
                channel.send(char)
                bad_actor_input += char.decode("utf-8", errors="ignore")

            if not bad_actor_input:
                break

            # Process the command
            continue_session = handle_command(
                channel, client_ip, bad_actor_input, current_directory, file_structure, current_user
            )
            if not continue_session:
                break

    except Exception as e:
        print(f"Exception during client handle: {e}")
    finally:
        try:
            transport.close()
        except Exception:
            pass
        client.close()
