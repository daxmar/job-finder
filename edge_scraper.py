import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime
try:
    import pandas as pd
except:
    pd = None

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except:
    REPORTLAB_AVAILABLE = False

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import os

class JobFinderEdgeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Job Finder Solo - EDGE ✅ (No Chrome Issues)")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', background='#252526')
        style.configure('Title.TLabel', font=('Segoe UI', 24, 'bold'), foreground='#ffffff', background='#1a1a1a')
        style.configure('TButton', font=('Segoe UI', 11, 'bold'), background='#007acc', foreground='white')
        style.map('TButton', background=[('active', '#106ebe')])
        style.configure('Status.TLabel', font=('Consolas', 10), foreground='#cccccc', background='#1a1a1a')
        
        self.jobs = []
        self.setup_ui()
        self.status_var = tk.StringVar(value="✅ Edge ready! 100% Windows compatible. Klik Test dulu.")
        ttk.Label(self.root, textvariable=self.status_var, style='Status.TLabel').pack(pady=15)
    
    def setup_ui(self):
        # Title
        ttk.Label(self.root, text="🎯 Job Finder Solo - Lowongan IT di Solo & Sekitarnya", style='Title.TLabel').pack(pady=30)
        
        # Inputs
        input_frame = ttk.LabelFrame(self.root, text="🔍 Pencarian", padding=30)
        input_frame.pack(fill='x', padx=30, pady=20)
        
        ttk.Label(input_frame, text="Job Types:").grid(row=0, column=0, sticky='w', pady=10)
        self.jobs_var = tk.StringVar(value="IT Support, Programmer, Data Entry, Admin")
        ttk.Entry(input_frame, textvariable=self.jobs_var, width=50).grid(row=0, column=1, padx=15)
        
        ttk.Label(input_frame, text="Lokasi:").grid(row=1, column=0, sticky='w', pady=10)
        self.loc_var = tk.StringVar(value="solo")
        ttk.Entry(input_frame, textvariable=self.loc_var, width=50).grid(row=1, column=1, padx=15)
        
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=25)
        ttk.Button(btn_frame, text="🧪 Test Edge", command=self.test_edge).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="🚀 Scraping!", command=self.scrape).pack(side='left', padx=10)
        
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill='x', padx=30, pady=20)
        
        # Results
        tree_frame = ttk.LabelFrame(self.root, text="📊 Lowongan Ditemukan", padding=15)
        tree_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        columns = ('Judul', 'Company', 'Lokasi', 'Gaji', 'Date', 'Link')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=25)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200, minwidth=100)
        
        vscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vscroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")
        
        # Buttons
        ttk.Button(self.root, text="🗑️ Clear", command=self.clear).pack(pady=20)
        if pd:
            ttk.Button(self.root, text="📈 Export Excel", command=self.export).pack(pady=5)
    
    def get_edge_options(self):
        options = webdriver.EdgeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        return options
    
    def test_edge(self):
        threading.Thread(target=self._test, daemon=True).start()
    
    def _test(self):
        self.progress.start()
        try:
            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=self.get_edge_options())
            driver.get("https://id.jobstreet.com")
            self.status_var.set("✅ Edge test OK! JobStreet loaded: " + driver.title[:50])
            driver.quit()
        except Exception as e:
            self.status_var.set(f"❌ Edge test fail: {str(e)}")
        self.progress.stop()
    
    def scrape(self):
        threading.Thread(target=self._scrape_all, daemon=True).start()
    
    def _scrape_all(self):
        self.progress.start()
        jobs_str = self.jobs_var.get()
        loc = self.loc_var.get()
        job_types = [j.strip() for j in jobs_str.split(',')]
        
        self.jobs = []
        self.tree.delete(*self.tree.get_children())
        
        for jt in job_types:
            self.status_var.set(f"Scraping {jt} {loc}...")
            jobs = self.scrape_one(jt, loc)
            self.jobs.extend(jobs)
        
        self.status_var.set(f"✅ Done! {len(self.jobs)} jobs found")
        self.progress.stop()
        self.update_tree()
    
    def scrape_one(self, job_type, location):
        jobs = []
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=self.get_edge_options())
        
        try:
            driver.get("https://id.jobstreet.com/id/jobs")
            time.sleep(4)
            
            # Search
            search = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[aria-label*='keyword'], input[placeholder*='keyword']")))
            search.send_keys(f"{job_type} {location}")
            
            loc_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label*='lokasi'], input[placeholder*='lokasi']")
            loc_input.send_keys(location)
            
            submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit.click()
            time.sleep(6)
            
            # Parse jobs
            cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, [data-automation='normalJob']")
            for card in cards[:12]:
                try:
                    title = card.find_element(By.CSS_SELECTOR, "a[data-automation*='jobTitle']").text
                    company = card.find_element(By.CSS_SELECTOR, "[data-automation*='jobCompany']").text
                    loc_text = card.find_element(By.CSS_SELECTOR, "[data-automation*='jobLocation']").text
                    salary = card.find_element(By.CSS_SELECTOR, "[data-automation*='jobSalary']").text.strip() if card.find_elements(By.CSS_SELECTOR, "[data-automation*='jobSalary']") else 'Confidential'
                    link = card.find_element(By.CSS_SELECTOR, "a[data-automation*='jobTitle']").get_attribute('href')
                    
                    jobs.append({
                        'Judul': title,
                        'Company': company,
                        'Lokasi': loc_text,
                        'Gaji': salary,
                        'Date': 'Recent',
                        'Link': link
                    })
                except:
                    continue
                    
        except Exception as e:
            print(f"Scrape error for {job_type}: {e}")
        finally:
            driver.quit()
        
        return jobs
    
    def update_tree(self):
        for job in self.jobs:
            self.tree.insert('', 'end', values=(job['Judul'][:35], job['Company'], job['Lokasi'], 
                                              job['Gaji'], job['Date'], job['Link'][:45]))
    
    def clear(self):
        self.jobs = []
        self.tree.delete(*self.tree.get_children())
    
    def export(self):
        if not pd or not self.jobs:
            return
        file = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if file:
            df = pd.DataFrame(self.jobs)
            df.to_excel(file, index=False)
            messagebox.showinfo("Exported", f"{len(self.jobs)} jobs saved!")

if __name__ == "__main__":
    root = tk.Tk()
    app = JobFinderEdgeApp(root)
    root.mainloop()
