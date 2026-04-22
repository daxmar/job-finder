import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
from datetime import datetime
import os
import webbrowser
import pandas as pd
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Import core scraper
try:
    from bing_maps_scraper import BingMapsScraper
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False
    BingMapsScraper = None

class BingMapsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🗺️ Bing Maps Scraper - Semua Data Tempat")
        self.root.geometry("1500x900")
        self.root.configure(bg='#1a1a1a')
        
        self.scraper = None
        self.places = []
        self.status_var = tk.StringVar(value="Ready - Install deps & click Test Edge")
        self.setup_ui()
    
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', background='#252526')
        style.configure('Title.TLabel', font=('Segoe UI', 22, 'bold'), foreground='#ffffff', background='#1a1a1a')
        style.configure('TButton', font=('Segoe UI', 11), background='#007acc', foreground='white')
        style.map('TButton', background=[('active', '#106ebe')])
        style.configure('Status.TLabel', font=('Consolas', 10), foreground='#cccccc', background='#1a1a1a')
        
        # Title
        ttk.Label(self.root, text="🗺️ Bing Maps Scraper - Semua Rincian Tempat (Nama, Alamat, Rating, HP, Jam, GPS, dll)", 
                 style='Title.TLabel').pack(pady=20)
        
        # Inputs
        input_frame = ttk.LabelFrame(self.root, text="🔍 Pencarian", padding=25)
        input_frame.pack(fill='x', padx=30, pady=15)
        
        ttk.Label(input_frame, text="Query:").grid(row=0, column=0, sticky='w', pady=10)
        self.query_var = tk.StringVar(value="coffee shop")
        ttk.Entry(input_frame, textvariable=self.query_var, width=40).grid(row=0, column=1, padx=15)
        
        ttk.Label(input_frame, text="Kota:").grid(row=0, column=2, sticky='w', padx=(30,0))
        self.city_var = tk.StringVar(value="solo")
        ttk.Entry(input_frame, textvariable=self.city_var, width=20).grid(row=0, column=3, padx=15)
        
        ttk.Label(input_frame, text="Max Pages:").grid(row=1, column=0, sticky='w', pady=10)
        self.pages_var = tk.StringVar(value="3")
        ttk.Entry(input_frame, textvariable=self.pages_var, width=10).grid(row=1, column=1, padx=15, sticky='w')
        
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=25)
        ttk.Button(btn_frame, text="🧪 Test Edge", command=self.test_edge).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="🚀 Scrape Bing Maps!", command=self.start_scrape).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="🗑️ Clear", command=self.clear_results).pack(side='left', padx=10)
        
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill='x', padx=30, pady=10)
        ttk.Label(self.root, textvariable=self.status_var, style='Status.TLabel').pack(pady=5)
        
        # Log
        log_frame = ttk.LabelFrame(self.root, text="📋 Log", padding=10)
        log_frame.pack(fill='x', padx=30, pady=10)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=4, font=('Consolas', 9), state='disabled')
        self.log_text.pack(fill='x')
        
        # Results table
        tree_frame = ttk.LabelFrame(self.root, text="📊 Tempat Ditemukan", padding=15)
        tree_frame.pack(fill='both', expand=True, padx=30, pady=10)
        
        columns = ('Nama', 'Alamat', 'Rating', 'HP', 'Website', 'Kategori', 'GPS')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180, minwidth=100)
        
        vscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vscroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")
        
        self.tree.bind('<Double-1>', self.open_maps_link)
        
        # Export buttons
        export_frame = ttk.Frame(self.root)
        export_frame.pack(fill='x', padx=30, pady=10)
        if pd:
            ttk.Button(export_frame, text="📈 Export Excel", command=self.export_excel).pack(side='right', padx=10)
        if REPORTLAB_AVAILABLE:
            ttk.Button(export_frame, text="📄 Export PDF Cards", command=self.export_pdf).pack(side='right', padx=10)
        ttk.Button(export_frame, text="🔄 Refresh Table", command=self.refresh_table).pack(side='right')
    
    def log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {msg}")
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{timestamp}] {msg}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.root.update()
    
    def status(self, msg):
        self.status_var.set(msg)
    
    def test_edge(self):
        if not SCRAPER_AVAILABLE:
            messagebox.showerror("Error", "bing_maps_scraper.py not found/installed")
            return
        threading.Thread(target=self._test_thread, daemon=True).start()
    
    def _test_thread(self):
        self.progress.start()
        self.status("Testing Bing Maps...")
        self.log("Testing Edge + Bing Maps connection...")
        try:
            self.scraper = BingMapsScraper()
            result = self.scraper.test_connection()
            self.status("✅ Edge + Bing Maps ready!")
            self.log(result)
        except Exception as e:
            self.status("❌ Test failed")
            self.log(f"Error: {str(e)}")
        self.progress.stop()
    
    def start_scrape(self):
        if not SCRAPER_AVAILABLE:
            return
        try:
            pages = int(self.pages_var.get())
        except:
            messagebox.showerror("Error", "Max pages must be number")
            return
        
        if not messagebox.askyesno("Confirm", f"Scrape '{self.query_var.get()} {self.city_var.get()}' ({pages} pages)?"):
            return
        
        threading.Thread(target=self._scrape_thread, daemon=True).start()
    
    def _scrape_thread(self):
        self.progress.start()
        self.scrape_btn.config(state='disabled') if hasattr(self, 'scrape_btn') else None
        
        query = self.query_var.get()
        city = self.city_var.get()
        pages = int(self.pages_var.get())
        
        self.places = []
        self.tree.delete(*self.tree.get_children())
        self.log(f"🚀 Starting scrape: '{query}' in '{city}' ({pages} pages)")
        self.status("Scraping in progress...")
        
        try:
            self.scraper = BingMapsScraper()
            self.places = self.scraper.scrape_places(query, city, pages)
            
            self.status(f"✅ Complete! {len(self.places)} places found")
            self.log(f"Found {len(self.places)} places with full details")
            self.refresh_table()
        except Exception as e:
            self.log(f"Scrape failed: {str(e)}")
            self.status("Scrape failed")
        finally:
            self.progress.stop()
            self.scrape_btn.config(state='normal') if hasattr(self, 'scrape_btn') else None
    
    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for place in self.places[-50:]:  # Last 50
            cats = ', '.join(place.get('categories', []))
            gps = f"{place.get('lat', '')}, {place.get('lng', '')}"
            self.tree.insert('', 'end', values=(
                place.get('name', '')[:40],
                place.get('address', '')[:40],
                place.get('rating', ''),
                place.get('phone', '')[:15],
                place.get('website', '')[:40],
                cats[:30],
                gps
            ))
    
    def clear_results(self):
        self.places = []
        self.tree.delete(*self.tree.get_children())
        self.log("Results cleared")
    
    def open_maps_link(self, event):
        selection = self.tree.selection()
        if selection:
            idx = self.tree.index(selection[0])
            if 0 <= idx < len(self.places):
                link = self.places[idx].get('maps_link', '')
                if link:
                    webbrowser.open(link)
    
    def export_excel(self):
        if not self.places:
            messagebox.showwarning("No Data", "Scrape dulu!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialname=f"bing_maps_{self.query_var.get().replace(' ', '_')}_{self.city_var.get()}.xlsx"
        )
        if filename:
            df = pd.DataFrame(self.places)
            df.to_excel(filename, index=False)
            self.log(f"✅ Excel exported: {len(self.places)} places")
    
    def export_pdf(self):
        if not REPORTLAB_AVAILABLE or not self.places:
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialname=f"bing_maps_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        if filename:
            self._create_pdf(filename)
    
    def _create_pdf(self, filename):
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], 
                                   fontSize=16, spaceAfter=20, alignment=1, textColor=colors.darkblue)
        
        story = []
        story.append(Paragraph(f"🗺️ Bing Maps - {self.query_var.get().upper()} {self.city_var.get().upper()}", title_style))
        story.append(Paragraph(f"Total: {len(self.places)} places | {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        for place in self.places:
            # Card layout
            data = [
                [f"<b>{place.get('name', 'N/A')}</b>"],
                [f"📍 {place.get('address', '')}"],
                [f"⭐ {place.get('rating', '')} ({place.get('reviews_count', '')} reviews)"],
                [f"📞 {place.get('phone', '')}"],
                [f"💰 {place.get('price_level', '')}"],
                [f"🕒 {place.get('hours', '')[:50]}..."],
                [f"🌐 {place.get('website', '')[:40]}..."],
                [f"📱 GPS: {place.get('lat', '')}, {place.get('lng', '')}"]
            ]
            
            t = Table(data, colWidths=[550])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('BOX', (0,0), (-1,-1), 2, colors.darkblue)
            ]))
            story.append(KeepTogether(t))
            story.append(Spacer(1, 15))
        
        doc.build(story)
        self.log(f"✅ PDF created: {os.path.basename(filename)}")
        webbrowser.open(filename)

if __name__ == "__main__":
    try:
        import pandas as pd
        root = tk.Tk()
        app = BingMapsApp(root)
        root.mainloop()
    except ImportError:
        print("Install pandas: pip install pandas openpyxl")

