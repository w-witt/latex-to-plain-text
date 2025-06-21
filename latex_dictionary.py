import json
import os
from typing import Dict, Optional, List

class LatexDictionary:
    def __init__(self, dictionary_file: str = "latex_dict.json"):
        """Initialize the LaTeX dictionary.
        
        Args:
            dictionary_file (str): Path to the JSON file containing the dictionary
        """
        self.dictionary_file = dictionary_file
        self.commands: Dict[str, str] = {}
        self.load_dictionary()

    def load_dictionary(self) -> None:
        """Load the dictionary from the JSON file."""
        if os.path.exists(self.dictionary_file):
            with open(self.dictionary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.commands = data.get('commands', {})
        else:
            self.commands = {}

    def save_dictionary(self) -> None:
        """Save the dictionary to the JSON file."""
        with open(self.dictionary_file, 'w', encoding='utf-8') as f:
            json.dump({'commands': self.commands}, f, indent=4)

    def get_plain_text(self, latex_command: str) -> Optional[str]:
        """Get the plain text equivalent of a LaTeX command.
        
        Args:
            latex_command (str): The LaTeX command to look up
            
        Returns:
            Optional[str]: The plain text equivalent, or None if not found
        """
        return self.commands.get(latex_command)

    def add_command(self, latex_command: str, plain_text: str) -> None:
        """Add a new LaTeX command and its plain text equivalent to the dictionary.
        
        Args:
            latex_command (str): The LaTeX command to add
            plain_text (str): The plain text equivalent
        """
        self.commands[latex_command] = plain_text
        self.save_dictionary()

    def remove_command(self, latex_command: str) -> bool:
        """Remove a LaTeX command from the dictionary.
        
        Args:
            latex_command (str): The LaTeX command to remove
            
        Returns:
            bool: True if the command was removed, False if it wasn't found
        """
        if latex_command in self.commands:
            del self.commands[latex_command]
            self.save_dictionary()
            return True
        return False

    def get_all_commands(self) -> Dict[str, str]:
        """Get all commands in the dictionary.
        
        Returns:
            Dict[str, str]: Dictionary of all LaTeX commands and their plain text equivalents
        """
        return self.commands.copy()

    def search_commands(self, query: str) -> Dict[str, str]:
        """Search for commands containing the query string.
        
        Args:
            query (str): The search query
            
        Returns:
            Dict[str, str]: Dictionary of matching LaTeX commands and their plain text equivalents
        """
        query = query.lower()
        return {
            cmd: text for cmd, text in self.commands.items()
            if query in cmd.lower() or query in text.lower()
        }

    def export_to_text(self, output_file: str) -> None:
        """Export the dictionary to a plain text file.
        
        Args:
            output_file (str): Path to the output file
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            for cmd, text in sorted(self.commands.items()):
                f.write(f"{cmd} -> {text}\n")

    def import_from_text(self, input_file: str) -> None:
        """Import commands from a plain text file.
        
        Args:
            input_file (str): Path to the input file
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '->' in line:
                    cmd, text = line.split('->', 1)
                    self.add_command(cmd.strip(), text.strip())

def main():
    """Example usage of the LatexDictionary class."""
    # Initialize the dictionary
    dict = LatexDictionary()
    
    # Example: Look up a command
    print("Looking up \\alpha:")
    print(dict.get_plain_text(r'\alpha'))
    
    # Example: Add a new command
    print("\nAdding new command:")
    dict.add_command(r'\newcommand', "new command")
    print(f"Added command: {dict.get_plain_text(r'\newcommand')}")
    
    # Example: Search for commands
    print("\nSearching for commands containing 'sum':")
    results = dict.search_commands('sum')
    for cmd, text in results.items():
        print(f"{cmd} -> {text}")

if __name__ == "__main__":
    main() 