import os
import json
import sys
from pathlib import Path

def main():
    # Find available sessions
    sessions = sorted(Path('.').glob('* - Session *'), key=os.path.getmtime, reverse=True)
    
    if not sessions:
        print("No sessions found")
        return
        
    # Select session
    print("Available sessions:")
    for i, session in enumerate(sessions, 1):
        print(f"{i}. {session.name}")
    choice = int(input("Select session: ")) - 1
    session_folder = sessions[choice]
    
    # Communication loop
    while True:
        print("\n1. View State\n2. Update Config\n3. Exit")
        choice = input("Choice: ")
        
        if choice == '1':
            # Read state
            with open(session_folder/'command_pipe', 'w') as cmd_pipe:
                cmd_pipe.write("GET_STATE")
                
            with open(session_folder/'response_pipe', 'r') as resp_pipe:
                state = json.loads(resp_pipe.read())
                print(json.dumps(state, indent=2))
                
        elif choice == '2':
            new_config = json.loads(input("Enter new config (JSON): "))
            with open(session_folder/'command_pipe', 'w') as cmd_pipe:
                cmd_pipe.write(f"UPDATE_CONFIG {json.dumps(new_config)}")
                
            with open(session_folder/'response_pipe', 'r') as resp_pipe:
                print(resp_pipe.read())
                
        elif choice == '3':
            break

if __name__ == "__main__":
    main()