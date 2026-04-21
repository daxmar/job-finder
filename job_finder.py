import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
from datetime import datetime
import os
import webbrowser

PANDAS_AVAILABLE = False
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pass

REPORTLAB_AVAILABLE = False
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    pass

SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    pass

class JobFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Job Finder - Lowongan IT")
        self.root.geometry("1400x850")
        self.root.state('zoomed') if os.name == 'nt' else self.root.attributes('-zoomed', True)
        
        self.jobs = []
        self.driver = None
        self.setup_ui()
    
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(header_frame, text="🎯 Job Finder - Lowongan IT di Solo", font=('Arial', 24, 'bold')).pack()
        
        # Control frame
        control_frame = ttk.LabelFrame(self.root, text="Pencarian", padding=20)
        control_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(control_frame, text="Keywords (koma):").grid(row=0, column=0, sticky='w')
        self.keywords_var = tk.StringVar(value="IT Support, Programmer, Data Entry, Admin")
        ttk.Entry(control_frame, textvariable=self.keywords_var, width=40).grid(row=0, column=1, padx=10)
        
        ttk.Label(control_frame, text="Lokasi:").grid(row=0, column=2, sticky='w', padx=(20,0))
        self.location_var = tk.StringVar(value="surakarta")
        ttk.Entry(control_frame, textvariable=self.location_var, width=20).grid(row=0, column=3, padx=10)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=20)
        self.scrape_btn = ttk.Button(btn_frame, text="🔍 Start Scraping", command=self.start_scrape)
        self.scrape_btn.pack(side='left', padx=10)
        ttk.Button(btn_frame, text="🧪 Test Edge", command=self.test_edge).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="🗑️ Clear", command=self.clear).pack(side='left', padx=10)
        
        # Progress & status
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill='x', padx=20, pady=5)
        
        self.status_var = tk.StringVar(value="Ready - Click Test Edge first")
        ttk.Label(self.root, textvariable=self.status_var, font=('Consolas', 10)).pack(pady=5)
        
        # Log
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
        log_frame.pack(fill='x', padx=20, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=4, state='disabled', font=('Consolas', 9))
        self.log_text.pack(fill='x')
        
        # Results
        results_frame = ttk.LabelFrame(self.root, text="Lowongan Pekerjaan", padding=10)
        results_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Treeview
        columns = ('Judul', 'Perusahaan', 'Lokasi', 'Gaji', 'Tanggal', 'Link')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=20)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)
        
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.tree.bind('<Double-1>', self.open_job)
        
        # Export
        export_frame = ttk.Frame(self.root)
        export_frame.pack(fill='x', padx=20, pady=10)
        if PANDAS_AVAILABLE:
            ttk.Button(export_frame, text="📊 Export Excel", command=self.export_excel).pack(side='right', padx=10)
        if REPORTLAB_AVAILABLE:
            ttk.Button(export_frame, text="📄 Export PDF (Kartu)", command=self.export_pdf).pack(side='right', padx=10)
        ttk.Button(export_frame, text="Refresh Table", command=self.refresh_table).pack(side='right')
    
    def log(self, msg):
        """Add to log and print"""
        print(msg)
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"{datetime.now().strftime('%H:%M:%S')} | {msg}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.root.update()
    
    def status(self, msg):
        self.status_var.set(msg)
    
    def get_driver_service(self):
        """Helper untuk mendapatkan service driver (Lokal vs Manager)"""
        # Cek apakah ada msedgedriver.exe di folder project
        local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "msedgedriver.exe")
        
        if os.path.exists(local_path):
            self.log(f"Menggunakan driver lokal: {local_path}")
            return EdgeService(executable_path=local_path)
        
        # Jika tidak ada, gunakan manager (membutuhkan internet)
        self.log("Driver lokal tidak ditemukan, mencoba menggunakan webdriver-manager...")
        return EdgeService(EdgeChromiumDriverManager().install())

    def test_edge(self):
        if not SELENIUM_AVAILABLE:
            messagebox.showerror("Error", "Selenium not available. Run `pip install selenium webdriver-manager`")
            return
        threading.Thread(target=self._test_edge_thread, daemon=True).start()
    
    def _test_edge_thread(self):
        self.progress.start()
        self.status("Testing Edge...")
        self.log("Testing Microsoft Edge...")
        try:
            options = EdgeOptions()
            service = self.get_driver_service()
            driver = webdriver.Edge(service=service, options=options)
            driver.get("https://id.jobstreet.com")
            title = driver.title
            driver.quit()
            self.status("✅ Edge ready!")
            self.log(f"Success! Jobstreet loaded: {title[:50]}...")
        except Exception as e:
            error_msg = str(e)
            if "offline" in error_msg.lower() or "11001" in error_msg:
                self.log("❌ Error: Koneksi gagal. Harap download 'msedgedriver.exe' manual dan taruh di folder project.")
            else:
                self.log(f"Edge test failed: {error_msg}")
            self.status("Edge test failed (Offline?)")
        self.progress.stop()
    
    def start_scrape(self):
        if not SELENIUM_AVAILABLE:
            messagebox.showerror("Error", "Selenium not available")
            return
        if not messagebox.askyesno("Confirm", "Mulai scraping Jobstreet? (~2 menit)"):
            return
        self.scrape_btn.config(state='disabled')
        threading.Thread(target=self._scrape_thread, daemon=True).start()
    
    def _scrape_thread(self):
        self.progress.start()
        keywords = [k.strip() for k in self.keywords_var.get().split(',')]
        loc = self.location_var.get()
        
        self.jobs = []
        self.tree.delete(*self.tree.get_children())
        self.log("=== Starting scrape ===")
        
        for i, keyword in enumerate(keywords):
            self.status(f"Scraping {keyword} ({i+1}/{len(keywords)})")
            self.log(f"Searching '{keyword}' in {loc}")
            new_jobs = self.scrape_keyword(keyword, loc)
            self.jobs.extend(new_jobs)
            self.refresh_table()
            time.sleep(3)  # Rate limit
        
        self.progress.stop()
        self.scrape_btn.config(state='normal')
        self.status(f"Complete! {len(self.jobs)} lowongan")
        self.log(f"=== Complete: {len(self.jobs)} jobs found ===")
    
    def scrape_keyword(self, keyword, location):
        jobs = []
        driver = None
        try:
            # Pindahkan inisialisasi ke dalam try untuk menangani masalah koneksi/offline
            service = self.get_driver_service()
            options = EdgeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            
            driver = webdriver.Edge(service=service, options=options)
            # Langsung ke URL pencarian agar lebih stabil
            search_url = f"https://id.jobstreet.com/id/jobs?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
            driver.get(search_url)
            time.sleep(5)
            
            # Get jobs
            # Gunakan multiple selectors untuk cadangan
            selectors = [".job-card-container", "[data-automation='normalJob']", "article[data-automation='job-card']"]
            cards = []
            for selector in selectors:
                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if cards: break
                
            self.log(f"Found {len(cards)} job cards")
            
            for card in cards[:8]: # Limit 8 agar tidak terlalu lama saat mengambil detail
                try:
                    # Selector judul yang lebih fleksibel
                    title_elem = card.find_element(By.CSS_SELECTOR, "a[data-automation*='jobTitle'], a[class*='JobTitle']")
                    title = title_elem.text
                    link = title_elem.get_attribute('href')
                    
                    company_elem = card.find_element(By.CSS_SELECTOR, "[data-automation*='jobCompany'], [class*='Company']")
                    company = company_elem.text
                    
                    loc_elem = card.find_element(By.CSS_SELECTOR, "[data-automation*='jobLocation'], [class*='Location']")
                    job_loc = loc_elem.text
                    
                    salary = 'Not listed'
                    salary_elems = card.find_elements(By.CSS_SELECTOR, "[data-automation*='jobSalary']")
                    if salary_elems:
                        salary = salary_elems[0].text
                    
                    # --- Ambil Detail (Deskripsi & Pertanyaan) ---
                    self.log(f"   > Mengambil detail: {title[:30]}...")
                    driver.execute_script("window.open(arguments[0], '_blank');", link)
                    driver.switch_to.window(driver.window_handles[1])
                    
                    desc = "Tidak ada deskripsi."
                    questions = "Tidak ada pertanyaan khusus."
                    
                    try:
                        desc_elem = WebDriverWait(driver, 7).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-automation='jobAdDetails'], [class*='JobDescription']"))
                        )
                        desc = desc_elem.text
                        
                        q_elems = driver.find_elements(By.CSS_SELECTOR, "[data-automation='job-details-questions'] li")
                        if q_elems:
                            questions = "\n".join([q.text for q in q_elems])
                    except:
                        pass
                    
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    # ---------------------------------------------

                    jobs.append({
                        'Judul': title,
                        'Perusahaan': company,
                        'Lokasi': job_loc,
                        'Gaji': salary,
                        'Tanggal': 'Recent',
                        'Link': link,
                        'Deskripsi': desc,
                        'Pertanyaan': questions
                    })
                except:
                    continue
                    
        except Exception as e:
            self.log(f"Scrape error: {str(e)}")
        finally:
            if driver:
                driver.quit()
        
        return jobs
    
    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for job in self.jobs[-100:]:
            # Jangan memotong link di sini karena akan merusak fungsi double-click
            self.tree.insert('', 'end', values=(
                job['Judul'][:40],
                job['Perusahaan'],
                job['Lokasi'],
                job['Gaji'],
                job['Tanggal'],
                job['Link'] 
            ))
    
    def clear(self):
        self.jobs = []
        self.tree.delete(*self.tree.get_children())
        self.log("Results cleared")
    
    def export_excel(self):
        if not PANDAS_AVAILABLE:
            messagebox.showerror("Error", "Pandas not installed")
            return
        if not self.jobs:
            messagebox.showwarning("No data", "No jobs to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialname=f"lowongan_solo_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        if filename:
            df = pd.DataFrame(self.jobs)
            df.to_excel(filename, index=False)
            self.log(f"✅ Exported {len(self.jobs)} jobs to {os.path.basename(filename)}")
    
    def export_pdf(self):
        if not self.jobs:
            messagebox.showwarning("No data", "Cari lowongan dulu sebelum export PDF")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialname=f"lowongan_it_solo_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
        if not filename: return

        try:
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Custom Styles
            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], color=colors.hexColor("#007acc"), spaceAfter=12)
            card_title = ParagraphStyle('CardTitle', parent=styles['Heading2'], fontSize=12, textColor=colors.whitesmoke)
            body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=9, leading=11)
            label_style = ParagraphStyle('LabelStyle', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')

            story.append(Paragraph(f"Katalog Lowongan Kerja - {self.location_var.get().upper()}", title_style))
            story.append(Paragraph(f"Dicetak pada: {datetime.now().strftime('%d %B %Y')}", body_style))
            story.append(Spacer(1, 20))

            for job in self.jobs:
                # Header Kartu (Judul & Perusahaan)
                header_content = [
                    [Paragraph(f"<b>{job['Judul']}</b>", card_title)],
                    [Paragraph(f"🏢 {job['Perusahaan']} | 📍 {job['Lokasi']}", ParagraphStyle('Sub', parent=card_title, fontSize=10))]
                ]
                header_table = Table(header_content, colWidths=[480])
                header_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.hexColor("#007acc")),
                    ('PADDING', (0,0), (-1,-1), 10),
                ]))

                # Isi Kartu
                details = [
                    [Paragraph("💰 Gaji:", label_style), Paragraph(job['Gaji'], body_style)],
                    [Paragraph("📝 Deskripsi:", label_style), Paragraph(job['Deskripsi'][:400] + "...", body_style)],
                    [Paragraph("❓ Pertanyaan Perusahaan:", label_style), Paragraph(job['Pertanyaan'], body_style)],
                    [Paragraph("🔗 Link:", label_style), Paragraph(f"<font color='blue'>{job['Link']}</font>", body_style)]
                ]
                
                detail_table = Table(details, colWidths=[100, 380])
                detail_table.setStyle(TableStyle([
                    ('BOX', (0,0), (-1,-1), 1, colors.grey),
                    ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('PADDING', (0,0), (-1,-1), 8),
                    ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.lightgrey),
                ]))

                # Gabungkan dalam satu container agar kartu tidak terpotong antar halaman
                card_container = [header_table, detail_table, Spacer(1, 15)]
                story.append(KeepTogether(card_container))

            doc.build(story)
            self.log(f"✅ PDF Berhasil dibuat: {os.path.basename(filename)}")
            messagebox.showinfo("Success", "PDF berhasil dibuat dengan format kartu!")
            webbrowser.open(filename)
        except Exception as e:
            self.log(f"PDF Error: {str(e)}")
            messagebox.showerror("Error", f"Gagal membuat PDF: {e}")

    def open_job(self, event):
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            # Ambil link asli (bukan yang terpotong)
            link = self.tree.item(item)['values'][5]
            if link and str(link).startswith('http'):
                webbrowser.open(link)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = JobFinderApp(root)
    app.run()
