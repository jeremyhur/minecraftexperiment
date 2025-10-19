import tkinter as tk
from tkinter import scrolledtext, messagebox
import google.generativeai as genai
import pyautogui
import time
import json
import threading
import re

# Configure pyautogui for better mouse control
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class MinecraftControllerApp:
    def __init__(self, root):
        """
        Initializes the main application window and its widgets.
        """
        self.root = root
        self.root.title("Gemini Minecraft Controller")
        self.root.geometry("550x500")
        self.root.configure(bg='#2E2E2E')

        # --- Styling ---
        style = {
            "bg": "#2E2E2E",
            "fg": "#FFFFFF",
            "entry_bg": "#3C3C3C",
            "button_bg": "#007ACC",
            "button_fg": "#FFFFFF",
            "font_bold": ("Inter", 10, "bold"),
            "font_normal": ("Inter", 10),
        }

        # --- Widgets ---
        # API Key Input
        tk.Label(root, text="Gemini API Key:", font=style["font_bold"], bg=style["bg"], fg=style["fg"]).pack(pady=(10, 2), anchor='w', padx=10)
        self.api_key_entry = tk.Entry(root, width=60, show="*", bg=style["entry_bg"], fg=style["fg"], insertbackground=style["fg"], relief=tk.FLAT)
        self.api_key_entry.pack(pady=(0, 10), padx=10)

        # Command Input
        tk.Label(root, text="Enter your command for Minecraft:", font=style["font_bold"], bg=style["bg"], fg=style["fg"]).pack(pady=(10, 2), anchor='w', padx=10)
        self.command_entry = tk.Entry(root, width=60, bg=style["entry_bg"], fg=style["fg"], insertbackground=style["fg"], relief=tk.FLAT)
        self.command_entry.pack(pady=(0, 10), padx=10)

        # Execute Button
        self.execute_button = tk.Button(root, text="Execute Command", command=self.start_execution_thread, bg=style["button_bg"], fg=style["button_fg"], relief=tk.FLAT, font=style["font_bold"])
        self.execute_button.pack(pady=10)

        # Status & Log Display
        tk.Label(root, text="Status & Logs:", font=style["font_bold"], bg=style["bg"], fg=style["fg"]).pack(pady=(10, 2), anchor='w', padx=10)
        self.status_text = scrolledtext.ScrolledText(root, height=15, width=60, bg=style["entry_bg"], fg=style["fg"], relief=tk.FLAT, font=style["font_normal"])
        self.status_text.pack(pady=(0, 10), padx=10, expand=True, fill='both')

    def log(self, message):
        """
        Logs a message to the status text box, ensuring it's thread-safe.
        """
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END) # Auto-scroll
        self.root.update_idletasks()

    def start_execution_thread(self):
        """
        Starts the command execution in a separate thread to keep the GUI responsive.
        """
        api_key = self.api_key_entry.get()
        command = self.command_entry.get()

        if not api_key or not command:
            messagebox.showerror("Error", "Please provide both an API Key and a command.")
            return

        # Disable button to prevent multiple executions
        self.execute_button.config(state=tk.DISABLED, text="Executing...")
        
        # Run the main logic in a new thread
        thread = threading.Thread(target=self.execute_command, args=(api_key, command))
        thread.daemon = True
        thread.start()

    def execute_command(self, api_key, command):
        """
        Main logic for processing and executing the command.
        """
        try:
            self.log("="*30)
            self.log(f"Received command: '{command}'")
            self.log("Giving you 5 seconds to switch to Minecraft...")
            self.log("IMPORTANT: Make sure Minecraft is in focus and the mouse cursor is visible in the game!")
            
            for i in range(5, 0, -1):
                self.log(f"{i}...")
                time.sleep(1)
            self.log("Action starts now!")
            
            # Check if we can see the mouse cursor
            try:
                current_x, current_y = pyautogui.position()
                self.log(f"Mouse cursor is at: x={current_x}, y={current_y}")
            except Exception as e:
                self.log(f"Could not get mouse position: {e}")

            # Step 1: Get structured instructions from Gemini
            self.log("Contacting Gemini API...")
            instructions = self.get_gemini_instructions(api_key, command)
            if not instructions:
                self.log("Failed to get instructions from Gemini.")
                return

            self.log("Successfully received instructions from Gemini.")
            self.log("Executing actions...")

            # Step 2: Execute the actions using pyautogui
            self.execute_actions(instructions)
            self.log("All actions completed successfully.")

        except Exception as e:
            self.log(f"An error occurred: {e}")
            messagebox.showerror("Execution Error", f"An error occurred:\n{e}")
        finally:
            # Re-enable the button on the main thread
            self.root.after(0, self.enable_button)

    def enable_button(self):
        """Re-enables the execute button."""
        self.execute_button.config(state=tk.NORMAL, text="Execute Command")

    def get_gemini_instructions(self, api_key, command):
        """
        Sends the command to the Gemini API and gets structured JSON back.
        """
        try:
            self.log("=== DEBUGGING: Starting get_gemini_instructions method ===")
            genai.configure(api_key=api_key)
            self.log("API key configured")
            
            # First, let's see what models are actually available
            try:
                self.log("Checking available models...")
                models = genai.list_models()
                available_models = [m.name for m in models]
                self.log(f"Available models: {available_models}")
            except Exception as e:
                self.log(f"Could not list models: {e}")
            
            # Try different models in order of preference (using models from your available list)
            model_names_to_try = [
                'gemini-2.5-flash',
                'gemini-2.0-flash',
                'gemini-2.5-pro',
                'gemini-2.0-pro-exp',
                'gemini-flash-latest',
                'gemini-pro-latest',
                'models/gemini-2.5-flash',
                'models/gemini-2.0-flash',
                'models/gemini-2.5-pro'
            ]
            
            model = None
            for model_name in model_names_to_try:
                try:
                    self.log(f"Trying {model_name}...")
                    model = genai.GenerativeModel(model_name)
                    self.log(f"Model {model_name} created successfully")
                    
                    # Test if the model actually works
                    self.log(f"Testing {model_name} with a simple request...")
                    test_response = model.generate_content("Hello")
                    self.log(f"✅ {model_name} works! Using this model.")
                    break
                except Exception as e:
                    self.log(f"❌ {model_name} failed: {e}")
                    continue
            
            if model is None:
                self.log("All model attempts failed. No working model found.")
                return None

            # This detailed prompt is crucial for getting reliable JSON output.
            prompt = f"""
            You are an expert at translating natural language commands into structured JSON for a Python automation script that uses the 'pyautogui' library to play Minecraft. Your task is to convert the user's command into a sequence of actions.

            IMPORTANT: Each action object MUST have a "type" field (not "action_type"). The exact format is:

            The valid action types are:
            1. `press_key`: For holding a key down for a duration.
               - `type`: "press_key" (exactly this string)
               - `key`: The key to press (e.g., 'w', 'a', 's', 'd', 'space', 'shift', 'e', 'f').
               - `duration`: The duration in seconds (float).
            2. `type_text`: For typing a string of text, often for in-game commands.
               - `type`: "type_text" (exactly this string)
               - `text`: The string to type.
            3. `click`: For mouse clicks.
               - `type`: "click" (exactly this string)
               - `button`: 'left' or 'right'.
               - `clicks`: Number of clicks (integer).
               - `interval`: Time between clicks in seconds (float).
            4. `move_mouse_relative`: For moving the mouse relative to its current position. This is used for looking around.
               - `type`: "move_mouse_relative" (exactly this string)
               - `x_offset`: Pixels to move horizontally (integer, negative for left). Use LARGE values: 500-1000 for full turns, 200-400 for half turns.
               - `y_offset`: Pixels to move vertically (integer, negative for up). Use LARGE values: 200-500 for looking up/down.
               - `duration`: Time in seconds to perform the move (float). Use 1.0-2.0 seconds for smooth, visible movement.

            Example format:
            {{
              "actions": [
                {{"type": "move_mouse_relative", "x_offset": 800, "y_offset": 0, "duration": 1.5}},
                {{"type": "press_key", "key": "space", "duration": 0.5}}
              ]
            }}
            
            NOTE: If mouse movement doesn't work in the game, you can also use keyboard turning:
            - For turning left: {{"type": "turn_with_keys", "direction": "left", "duration": 1.0}}
            - For turning right: {{"type": "turn_with_keys", "direction": "right", "duration": 1.0}}

            Analyze the user's command and respond ONLY with a single JSON object containing a key "actions" which is a list of action objects. Do not include any explanation or markdown formatting like ```json.

            User Command: "{command}"
            """

            self.log("Sending request to Gemini...")
            response = model.generate_content(prompt)
            self.log("Received response from Gemini")
            
            # Clean up the response to ensure it's valid JSON
            text_response = response.text
            self.log(f"Raw Gemini Response:\n{text_response}")
            
            # Also log the parsed actions for debugging
            try:
                json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
                if json_match:
                    clean_json = json_match.group(0)
                    parsed_actions = json.loads(clean_json)
                    self.log(f"Parsed actions: {parsed_actions}")
            except Exception as e:
                self.log(f"Error parsing actions: {e}")

            # Use regex to find the JSON block, robust against markdown
            json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
            if not json_match:
                self.log("Error: No valid JSON object found in Gemini's response.")
                return None
                
            clean_json = json_match.group(0)
            return json.loads(clean_json)

        except Exception as e:
            self.log(f"Error calling Gemini API: {e}")
            self.log(f"Exception type: {type(e).__name__}")
            return None

    def execute_actions(self, instructions):
        """
        Parses the JSON and executes each action using pyautogui.
        """
        actions = instructions.get("actions", [])
        if not actions:
            self.log("No actions found in the instructions.")
            return

        for action in actions:
            action_type = action.get("type")
            self.log(f" > Executing: {action}")
            try:
                if action_type == "press_key":
                    pyautogui.keyDown(action["key"])
                    time.sleep(action["duration"])
                    pyautogui.keyUp(action["key"])
                elif action_type == "type_text":
                    pyautogui.write(action["text"], interval=0.05)
                elif action_type == "click":
                    pyautogui.click(
                        button=action["button"],
                        clicks=action["clicks"],
                        interval=action["interval"]
                    )
                elif action_type == "turn_with_keys":
                    # Alternative turning method using keyboard controls
                    direction = action.get("direction", "right")
                    duration = action.get("duration", 1.0)
                    
                    if direction == "left":
                        self.log(f"Turning left with keyboard for {duration} seconds")
                        pyautogui.keyDown('left')
                        time.sleep(duration)
                        pyautogui.keyUp('left')
                    elif direction == "right":
                        self.log(f"Turning right with keyboard for {duration} seconds")
                        pyautogui.keyDown('right')
                        time.sleep(duration)
                        pyautogui.keyUp('right')
                    else:
                        self.log(f"Unknown turn direction: {direction}")
                        
                elif action_type == "move_mouse_relative":
                    self.log(f"Moving mouse relative: x={action['x_offset']}, y={action['y_offset']}, duration={action['duration']}")
                    
                    # Get current mouse position before movement
                    current_x, current_y = pyautogui.position()
                    self.log(f"Current mouse position: x={current_x}, y={current_y}")
                    
                    try:
                        # Try using drag instead of moveRel - this might work better with games
                        self.log(f"Attempting drag movement (more game-friendly)...")
                        pyautogui.drag(
                            action["x_offset"],
                            action["y_offset"],
                            duration=action["duration"]
                        )
                        
                        # Check new position after movement
                        new_x, new_y = pyautogui.position()
                        self.log(f"New mouse position: x={new_x}, y={new_y}")
                        self.log(f"Drag movement completed successfully")
                        
                    except Exception as e:
                        self.log(f"Drag movement failed: {e}")
                        # Fallback: try relative movement
                        self.log(f"Trying relative movement as fallback...")
                        try:
                            pyautogui.moveRel(
                                action["x_offset"],
                                action["y_offset"],
                                duration=action["duration"]
                            )
                            final_x, final_y = pyautogui.position()
                            self.log(f"Relative movement completed. Final position: x={final_x}, y={final_y}")
                        except Exception as e2:
                            self.log(f"Relative movement also failed: {e2}")
                    
                    # Try an alternative approach: simulate mouse movement in smaller steps
                    self.log("Trying alternative mouse movement with smaller steps...")
                    try:
                        # Get current position again
                        current_x, current_y = pyautogui.position()
                        target_x = current_x + action["x_offset"]
                        target_y = current_y + action["y_offset"]
                        
                        # Move in smaller steps to simulate more natural mouse movement
                        steps = 10
                        step_x = action["x_offset"] / steps
                        step_y = action["y_offset"] / steps
                        step_duration = action["duration"] / steps
                        
                        for i in range(steps):
                            pyautogui.moveRel(step_x, step_y, duration=step_duration)
                            time.sleep(0.01)  # Small delay between steps
                        
                        final_x, final_y = pyautogui.position()
                        self.log(f"Step-by-step movement completed. Final position: x={final_x}, y={final_y}")
                    except Exception as e3:
                        self.log(f"Step-by-step movement also failed: {e3}")
                    
                    # Try one more approach: use mouse events
                    self.log("Trying mouse events approach...")
                    try:
                        # Get current position again
                        current_x, current_y = pyautogui.position()
                        target_x = current_x + action["x_offset"]
                        target_y = current_y + action["y_offset"]
                        
                        # Try using mouse events
                        pyautogui.moveTo(target_x, target_y, duration=action["duration"])
                        final_x, final_y = pyautogui.position()
                        self.log(f"Mouse events movement completed. Final position: x={final_x}, y={final_y}")
                    except Exception as e4:
                        self.log(f"Mouse events movement also failed: {e4}")
                else:
                    self.log(f"Warning: Unknown action type '{action_type}'")
                
                time.sleep(0.2) # Small delay between actions

            except KeyError as e:
                self.log(f"Error: Missing parameter {e} for action {action}")
            except Exception as e:
                self.log(f"Error executing action {action}: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MinecraftControllerApp(root)
    root.mainloop()
