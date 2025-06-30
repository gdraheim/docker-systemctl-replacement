#!/usr/bin/env python3

# Simple localectl emulator using locale

import sys
import subprocess
import re
import os


def show_help():
    """Display help information and exit."""
    print(f"Usage: {sys.argv[0]} <command> [options]")
    print("Commands:")
    print("  status           Show current locale settings")
    print("  set-locale VAR=VALUE [...]")
    print("                   Set locale variables (e.g. LANG=en_US.UTF-8)")
    sys.exit(1)


def run_locale_command():
    """Run the locale command and return its output with proper indentation."""
    try:
        result = subprocess.run(['locale'], capture_output=True, text=True, check=True)
        # Add indentation to each line
        indented_output = '\n'.join(f"      {line}" for line in result.stdout.strip().split('\n'))
        return indented_output
    except subprocess.CalledProcessError as e:
        print(f"Error running locale command: {e}", file=sys.stderr)
        sys.exit(1)


def handle_status():
    """Handle the status command."""
    print("   System Locale:")
    print(run_locale_command())


def handle_set_locale(args):
    """Handle the set-locale command."""
    if not args:
        print("No locale variables provided.")
        sys.exit(1)
    
    # Validate and collect locale assignments
    valid_assignments = []
    locale_pattern = re.compile(r'^[A-Z_]+=.+$')
    
    for var in args:
        if locale_pattern.match(var):
            valid_assignments.append(var)
        else:
            print(f"Invalid locale assignment: {var}")
            sys.exit(1)
    
    # Write to /etc/locale.conf
    try:
        with open('/etc/locale.conf', 'w') as f:
            for assignment in valid_assignments:
                f.write(f"{assignment}\n")
    except IOError as e:
        print(f"Error writing to /etc/locale.conf: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("Locale settings updated. Current settings:")
    print(run_locale_command())


def main():
    """Main function to handle command line arguments and dispatch commands."""
    if len(sys.argv) < 2:
        show_help()
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    if command == "status":
        handle_status()
    elif command == "set-locale":
        handle_set_locale(args)
    else:
        show_help()


if __name__ == "__main__":
    main()
