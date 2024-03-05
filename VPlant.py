import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET
from PIL import Image, ImageTk  # Ensure Pillow is installed (pip install Pillow)
import os
import re

class BPMNViewerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VPlant - Recommendation System for Vertical Farming")
        self.geometry("1000x600")
        self.style = ttk.Style(self)
        self.style.configure('TButton', font=('Helvetica', 12), borderwidth='1')
        self.style.configure('TLabel', font=('Helvetica', 12), background='lightgray')
        self.configure(bg='lightgray')

        self.file_path = None
        self.file_state = {"elements": {}, "sequence_flows": {}, "current_element_id": None, "current_index": 0}
        self.conditional_responses = {}
        self.element_ids = []

        self.initialize_ui()

    def initialize_ui(self):
        self.sidebar = tk.Frame(self, width=200, bg='lightgray', relief='sunken', borderwidth=2)
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT, expand=False)
        self.content = tk.Frame(self, bg='white')
        self.content.pack(fill=tk.BOTH, side=tk.LEFT, expand=True, padx=(5,0), pady=5)

        load_button = ttk.Button(self.sidebar, text="Load BPMN File", command=self.load_bpmn_file)
        load_button.pack(pady=10, padx=10, fill=tk.X)
        self.next_button = ttk.Button(self.content, text="Next Step", state=tk.DISABLED, command=self.process_next_step)
        self.next_button.pack(pady=10, padx=10)

        self.info_label = ttk.Label(self.content, text="No BPMN file loaded. Please load a file to begin.", wraplength=550)
        self.info_label.pack(pady=10, padx=10)

        self.image_panel = tk.Label(self.content, bg='white')
        self.image_panel.pack(side="bottom", fill="both", expand="yes", padx=10, pady=10)

        close_button = ttk.Button(self.sidebar, text="Close VPlant", command=self.destroy)
        close_button.pack(pady=10, padx=10, fill=tk.X)

    def load_bpmn_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("BPMN Files", "*.bpmn")])
        if file_path:
            self.file_path = file_path
            self.parse_bpmn_file(file_path)
            messagebox.showinfo("Success", "BPMN file loaded successfully.")
            self.info_label.config(text="BPMN file loaded successfully. Click 'Next Step' to start.")
            self.next_button['state'] = 'normal'

    def parse_bpmn_file(self, file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
        for elem in root.findall('.//bpmn:*', bpmn_ns):
            elem_id = elem.get('id')
            elem_type = elem.tag.split('}')[-1]
            if elem_type in ['startEvent', 'task', 'endEvent']:
                elem_name, image_path = self.extract_image_path(elem.get('name', 'Unnamed'))
                conditions = re.findall(r'ifyes="([^"]*)"|ifno="([^"]*)"', elem_name)
                clean_name = re.sub(r' ifyes="[^"]*"| ifno="[^"]*"', '', elem_name).strip()
                self.file_state["elements"][elem_id] = {"id": elem_id, "type": elem_type, "name": clean_name, "image_path": image_path}
                self.element_ids.append(elem_id)
                if conditions:
                    self.conditional_responses[elem_id] = {"ifyes": conditions[0][0], "ifno": conditions[0][1]}

    def extract_image_path(self, elem_name):
        if 'path="' in elem_name:
            path_start = elem_name.find('path="') + 6
            path_end = elem_name.find('"', path_start)
            image_name = elem_name[path_start:path_end]
            image_path = os.path.join(os.getcwd(), image_name)
            return elem_name[:path_start-7], image_path  # Exclude 'path="' part from the name
        return elem_name, None

    def process_next_step(self):
        if self.file_state["current_index"] < len(self.element_ids):
            current_id = self.element_ids[self.file_state["current_index"]]
            self.file_state["current_element_id"] = current_id
            current_element = self.file_state["elements"][current_id]
            self.info_label.config(text=f"Current: {current_element['type']} - {current_element['name']}")
            if current_element["image_path"]:
                self.display_image(current_element["image_path"])
            else:
                self.clear_image()  # Clear the image if no image is associated with the current step.
            if current_id in self.conditional_responses:
                self.check_symptoms(current_id)
            self.file_state["current_index"] += 1
        else:
            messagebox.showinfo("End", "End of BPMN process.")
            self.next_button['state'] = 'disabled'
            self.clear_image()  # Ensure to clear the image at the end of the process.

    def display_image(self, image_path):
        try:
            img = Image.open(image_path)
            img = img.resize((400, 300), Image.Resampling.LANCZOS)  # Updated resize method
            img_tk = ImageTk.PhotoImage(img)
            self.image_panel.config(image=img_tk)
            self.image_panel.image = img_tk
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def clear_image(self):
        self.image_panel.config(image='')
        self.image_panel.image = None

    def check_symptoms(self, task_id):
        condition = self.conditional_responses.get(task_id, {})
        response = messagebox.askyesno("Check Condition", "Select Yes or No based on the condition.")
        if response is not None:  # Check if the response is explicitly True or False.
            message = condition["ifyes"] if response else condition["ifno"]
            if message:  # Display the message only if it's not empty.
                messagebox.showinfo("Action Required", message)
            else:
                self.info_label.config(text="")  # Clear the instruction text if the message is empty.
        else:
            # Handle closing the dialog or selecting 'Cancel' without setting an info label text.
            self.info_label.config(text="Please make a selection to proceed.")

if __name__ == "__main__":
    app = BPMNViewerApp()
    app.mainloop()
