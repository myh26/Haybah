import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import os
import shutil
import threading
from datetime import date
from flet import ,

class TailorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("نظام إدارة محل الخياطة - النسخة الاحترافية")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # دعم RTL كامل للعربية
        self.root.option_add('*font', 'Arial 12')
        
        # الاتصال بقاعدة البيانات
        self.conn = sqlite3.connect('tailor.db')
        self.current_user = None
        self.current_role = None
        self.entries = {}
        self.setup_database()
        
        # ✅ جديد: متغيرات البحث
        self.search_vars = {}
        
        self.show_login()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # ✅ جديد: فحص التذكيرات عند البدء
        self.check_reminders()
    
    def on_closing(self):
        """إغلاق آمن"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
        self.root.destroy()
    
    def setup_database(self):
        """إنشاء الجداول + جدول التذكيرات"""
        c = self.conn.cursor()

        # الجداول الأساسية (كما هي)
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('مدير', 'محاسب', 'خياط', 'موظف'))
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            total_amount REAL DEFAULT 0.0,
            paid_amount REAL DEFAULT 0.0,
            remaining_amount REAL DEFAULT 0.0
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('خياط', 'موظف'))
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            tailor_id INTEGER,
            measurements TEXT,
            fabric_type TEXT,
            cloth_type TEXT,
            quantity INTEGER DEFAULT 1,
            delivery_date DATE,
            total_amount REAL DEFAULT 0.0,
            paid_amount REAL DEFAULT 0.0,
            remaining_amount REAL DEFAULT 0.0,
            status TEXT DEFAULT '📝 تسجيل الطلب',
            current_employee TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (tailor_id) REFERENCES employees (id)
        )''')

        # ✅ جديد: جدول النسخ الاحتياطية
        c.execute('''CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            backup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            size_bytes INTEGER
        )''')

        # بيانات افتراضية
        default_users = [
            ('admin', '123456', 'مدير'),
            ('accountant', '123456', 'محاسب'),
            ('tailor', '123456', 'خياط'),
            ('employee', '123456', 'موظف')
        ]
        for user in default_users:
            c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", user)

        default_employees = [('خياط أحمد', 'خياط'), ('خياط محمد', 'خياط')]
        for emp in default_employees:
            c.execute("INSERT OR IGNORE INTO employees (name, role) VALUES (?, ?)", emp)

        self.conn.commit()

    def check_reminders(self):
        """✅ جديد: فحص التذكيرات (كل 30 دقيقة)"""
        c = self.conn.cursor()
        tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        c.execute("""
            SELECT cu.name, o.cloth_type, o.delivery_date 
            FROM orders o JOIN customers cu ON o.customer_id = cu.id 
            WHERE o.delivery_date = ? AND o.status != '🎁 جاهز للتسليم'
        """, (tomorrow,))
        
        reminders = c.fetchall()
        if reminders:
            reminder_text = "🚨تذكيرات غد" 
            
        for name, cloth, date in reminders[:5]:  # أول 5 فقط
             reminder_text += f"• {name}: {cloth}"

        if len(reminders) > 5:
                reminder_text += f"• و{len(reminders)-5} طلب آخر..."
            
messagebox.showwarning("تذكيرات التسليم", reminder_text)
        
        # إعادة الفحص بعد 30 دقيقة

self.root.after(1800000, 
        self.check_reminders)

    # باقي الدوال الأساسية (كما هي مع التحسينات)...
self.conn.commit()


     def show_login(self):
        """شاشة تسجيل الدخول مع RTL  عربي"""
        for w in self.root.winfo_children():
            w.destroy()

        title = tk.Label(
            self.root,
            text="تسجيل الدخول إلى نظام الخياطة",
            font=('Arial', 16, 'bold'), bg='#f0f0f0'
        )
        title.pack(pady=50)

        frame = tk.Frame(self.root, bg='#f0f0f0', relief='solid', bd=1)
        frame.pack(padx=80, pady=20)

        tk.Label(frame, text="اسم المستخدم:", font=('Arial', 12), bg='#f0f0f0').grid(
            row=0, column=0, padx=10, pady=10, sticky='e'
        )
        self.username_entry = tk.Entry(frame, font=('Arial', 12), justify='right', width=25)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(frame, text="كلمة المرور:", font=('Arial', 12), bg='#f0f0f0').grid(
            row=1, column=0, padx=10, pady=10, sticky='e'
        )
        self.password_entry = tk.Entry(frame, font=('Arial', 12), justify='right', show='*', width=25)
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        login_btn = tk.Button(
            frame, text="دخول",
            font=('Arial', 12, 'bold'),
            bg='#4CAF50', fg='white',
            width=15,
            command=self.login
        )
        login_btn.grid(row=2, column=0, columnspan=2, pady=20)

    def login(self):
        """التحقق من تسجيل الدخول"""
        user = self.username_entry.get().strip()
        pwd = self.password_entry.get().strip()

        c = self.conn.cursor()
        c.execute("SELECT id, username, role FROM users WHERE username=? AND password=?", (user, pwd))
        row = c.fetchone()

        if row:
            self.current_user = row[1]
            self.current_role = row[2]
            self.show_dashboard()
        else:
            messagebox.showerror("خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة")

    def show_dashboard(self):
        """اللوحة الرئيسية – القوائم عمودياً"""
        for w in self.root.winfo_children():
            w.destroy()

        title = tk.Label(
            self.root,
            text=f"لوحة التحكم — {self.current_role}",
            font=('Arial', 18, 'bold'), bg='#f0f0f0'
        )
        title.pack(pady=30)

        # الشريط الجانبي (عمودي)
        nav_frame = tk.Frame(self.root, bg='#f8f8f8', relief='sunken', bd=2)
        nav_frame.pack(padx=20, pady=20, fill='y', side='left')

        # قائمة العمود (vertical)
        buttons = [
            ("تسجيل طلب جديد", self.show_new_order),
            ("إدارة الطلبات", self.show_orders),
        ]

        if self.current_role == 'مدير':
            buttons.append(("إدارة الموظفين", self.manage_employees))

        if self.current_role in ['مدير', 'محاسب']:
            buttons.append(("قائمة الزبائن", self.show_customers_list))
            buttons.append(("طباعة PDF", self.print_customers_pdf))

        buttons.append(("التقارير", self.show_reports))

        for text, cmd in buttons:
            btn = tk.Button(
                nav_frame,
                text=text,
                font=('Arial', 12, 'bold'),
                bg='#2196F3', fg='white',
                width=20,
                anchor='center',
                command=cmd
            )
            btn.pack(pady=6, padx=6, ipady=5)

        # زر التنقل
        top_btns = tk.Frame(self.root, bg='#f0f0f0')
        top_btns.pack(pady=10, side='top')

        tk.Button(top_btns, text="👈 خروج", font=('Arial', 12), bg='#f44336', fg='white', 
                  command=self.logout).pack(side='right', padx=10)
        tk.Button(top_btns, text="🏠 لوحة التحكم", font=('Arial', 12), bg='#2196F3', fg='white', 
                  command=self.show_dashboard).pack(side='right', padx=10)

    def show_new_order(self):
        """نافذة طلب جديد ✅ إصلاح: استخدام self.entries"""
        window = tk.Toplevel(self.root)
        window.title("طلب جديد")
        window.geometry("600x800")
        window.configure(bg='#f9f9f9')

        # حقول بيانات العميل
        tk.Label(window, text="بيانات العميل", font=('Arial', 14, 'bold'), bg='#f9f9f9').pack(pady=10)

        # Frame للحُقول
        f = tk.Frame(window, bg='#f9f9f9')
        f.pack(pady=10)

        labels = [
            ("اسم العميل:", "name"),
            ("رقم الهاتف:", "phone"),
            ("مقاس الصدر:", "chest"),
            ("الطول:", "length"),
            ("نوع القماش:", "fabric"),
            ("نوع الثوب:", "cloth_type"),
            ("الكمية:", "quantity"),
            ("موعد التسليم:", "delivery_date"),
            ("المبلغ الإجمالي:", "total_amount"),
            ("المبلغ المدفوع:", "paid_amount")
        ]

        # ✅ إصلاح: استخدام self.entries
        for i, (lbl_text, key) in enumerate(labels):
            tk.Label(f, text=lbl_text, font=('Arial', 12), bg='#f9f9f9', anchor='e').grid(
                row=i, column=0, padx=10, pady=5, sticky='e'
            )
            justify = 'right' if key in ['name', 'phone'] else 'right'
            e = tk.Entry(f, font=('Arial', 12), justify=justify, width=30)
            e.grid(row=i, column=1, padx=10, pady=5)
            self.entries[key] = e

        # اختيار الخياط (فقط للمدير)
        if self.current_role == 'مدير':
            tailor_frame = tk.LabelFrame(window, text="اختيار الخياط", font=('Arial', 12), bg='#f9f9f9')
            tailor_frame.pack(pady=15, padx=20, fill='x')

            tk.Label(tailor_frame, text="الخياط:", font=('Arial', 11), bg='#f9f9f9').pack(side='right', padx=10)
            self.tailor_combo = ttk.Combobox(tailor_frame, font=('Arial', 11), justify='right', width=25)
            self.load_tailors_to_combo()
            self.tailor_combo.pack(pady=10, padx=10)

        # زر الحفظ
        save_btn = tk.Button(
            window, text="💾 حفظ الطلب",
            font=('Arial', 14, 'bold'),
            bg='#4CAF50', fg='white',
            width=20,
            command=lambda: self.save_order_in_window(window)
        )
        save_btn.pack(pady=20)

    def load_tailors_to_combo(self):
        """تحميل قائمة الخياطين"""
        c = self.conn.cursor()
        c.execute("SELECT id, name FROM employees WHERE role='خياط'")
        rows = c.fetchall()
        self.tailor_combo['values'] = [f"{r[0]} - {r[1]}" for r in rows]

    def save_order_in_window(self, window):
        c = self.conn.cursor()

        # التحقق من اسم العميل
        name = self.entries['name'].get().strip()
        if not name:
            messagebox.showwarning("تحذير", "الاسم مطلوب")
            return

        phone = self.entries['phone'].get().strip() or "غير محدد"
        fabric = self.entries['fabric'].get().strip()
        cloth_type = self.entries['cloth_type'].get().strip()
        quantity = int(self.entries['quantity'].get() or 1)
        total = float(self.entries['total_amount'].get() or 0.0)
        paid = float(self.entries['paid_amount'].get() or 0.0)
        remaining = total - paid
        delivery = self.entries['delivery_date'].get().strip()

        # measurements
        measurements = f"صدر: {self.entries['chest'].get().strip()}, طول: {self.entries['length'].get().strip()}"

        # حفظ/الحصول على العميل
        c.execute("SELECT id FROM customers WHERE name=? AND phone=?", (name, phone))
        row = c.fetchone()
        if row:
            customer_id = row[0]
        else:
            c.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))
            customer_id = c.lastrowid

        # حفظ الطلب
        tailor_id = None
        if self.current_role == 'مدير' and hasattr(self, 'tailor_combo') and self.tailor_combo.get():
            try:
                tid = int(self.tailor_combo.get().split()[0])
                tailor_id = tid
            except:
                pass

        c.execute('''
            INSERT INTO orders (
                customer_id,
                tailor_id,
                measurements,
                fabric_type,
                cloth_type,
                quantity,
                delivery_date,
                total_amount,
                paid_amount,
                remaining_amount,
                status,
                current_employee
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer_id,
            tailor_id,
            measurements,
            fabric,
            cloth_type,
            quantity,
            delivery,
            total,
            paid,
            remaining,
            '📝 تسجيل الطلب',
            self.current_user
        ))

        # تحديث العملاء
        c.execute('''
            UPDATE customers
            SET total_amount = total_amount + ?,
                paid_amount   = paid_amount + ?,
                remaining_amount = remaining_amount + ?
            WHERE id = ?
        ''', (total, paid, remaining, customer_id))

        self.conn.commit()
        messagebox.showinfo("نجح", "تم حفظ الطلب بنجاح!")
        window.destroy()
        # تنظيف الحقول
        self.entries.clear()
        self.show_dashboard()

    def show_orders(self):
        """عرض الطلبات مع مراعاة صلاحيات الخياط والموظف"""
        for w in self.root.winfo_children():
            w.destroy()

        title = tk.Label(
            self.root,
            text="إدارة الطلبات",
            font=('Arial', 18, 'bold'), bg='#f0f0f0'
        )
        title.pack(pady=20)

        # أعمدة ✅ إضافة عمود المتبقي
        cols = ('ر.م', 'العميل', 'النوع', 'الكمية', 'الحالة', 'التاريخ', 'الخياط', 'المتبقي')
        tree = ttk.Treeview(self.root, columns=cols, show='headings', height=18)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=110, anchor='center')

        # تحميل البيانات
        c = self.conn.cursor()

        # --- خياط فقط يرى طلباته التي لم تُكمل خياطتها ---
        if self.current_role == 'خياط':
            c.execute('''
                SELECT o.id, cu.name, o.cloth_type, o.quantity, o.status, o.delivery_date, e.name, o.remaining_amount
                FROM orders o
                JOIN customers cu ON o.customer_id = cu.id
                LEFT JOIN employees e ON o.tailor_id = e.id
                WHERE o.tailor_id = (SELECT id FROM employees WHERE name = ? AND role = 'خياط')
                  AND o.status IN ('📝 تسجيل الطلب', '✂️ القص', '🧵 الخياطة')
                ORDER BY o.id DESC
            ''', (self.current_user,))
        else:
            c.execute('''
                SELECT o.id, cu.name, o.cloth_type, o.quantity, o.status, o.delivery_date, e.name, o.remaining_amount
                FROM orders o
                JOIN customers cu ON o.customer_id = cu.id
                LEFT JOIN employees e ON o.tailor_id = e.id
                ORDER BY o.id DESC
            ''')

        for r in c.fetchall():
            tag = r[4]
            tree.insert('', tk.END, values=r, tags=(tag,))

        # تلوين حسب الحالة
        status_colors = {
            '📝 تسجيل الطلب': '#CCF',
            '✂️ القص': '#FCC',
            '🧵 الخياطة': '#CFC',
            '🔥 الكي': '#FFB347',
            '🎁 جاهز للتسليم': '#FFD700'
        }
        for k, v in status_colors.items():
            tree.tag_configure(k, background=v)

        tree.pack(pady=20, padx=20, fill='both', expand=True)

        # أزرار التنقل
        nav = tk.Frame(self.root, bg='#f0f0f0')
        nav.pack(pady=20)
        tk.Button(nav, text="🏠 لوحة التحكم", font=('Arial', 12), bg='#2196F3',
                  command=self.show_dashboard).pack(side='left', padx=10)
        
        # أزرار الإجراءات للطلب المحدد
        btn_frame = tk.Frame(self.root, bg='#f0f0f0')
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="🔄 تحديث حالة الطلب", font=('Arial', 12), bg='#FF9800', fg='white',
                  command=lambda: self.update_order_status(tree)).pack(side='left', padx=5)
        
        if self.current_role in ['مدير', 'محاسب']:
            tk.Button(btn_frame, text="💰 دفع", font=('Arial', 12), bg='#4CAF50', fg='white',
                      command=lambda: self.make_payment(tree)).pack(side='left', padx=5)

        tk.Button(btn_frame, text="🗑️ حذف طلب", font=('Arial', 12), bg='#f44336', fg='white',
                  command=lambda: self.delete_order(tree)).pack(side='left', padx=5)

    def update_order_status(self, tree):
        """تحديث حالة الطلب"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "اختر طلباً أولاً")
            return

        item = tree.item(selected[0])
        order_id = item['values'][0]
        current_status = item['values'][4]

        # الحالات التالية حسب الترتيب
        status_flow = {
            '📝 تسجيل الطلب': '✂️ القص',
            '✂️ القص': '🧵 الخياطة',
            '🧵 الخياطة': '🔥 الكي',
            '🔥 الكي': '🎁 جاهز للتسليم'
        }

        if current_status not in status_flow:
            messagebox.showinfo("معلومات", "الطلب مكتمل بالفعل")
            return

        new_status = status_flow[current_status]

        c = self.conn.cursor()
        c.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
        self.conn.commit()

        messagebox.showinfo("نجاح", f"تم تحديث الحالة إلى {new_status}")
        self.show_orders()

    def make_payment(self, tree):
        """✅ إصلاح كامل: دفعة جديدة للعميل"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "اختر طلباً أولاً")
            return

        item = tree.item(selected[0])
        order_id = item['values'][0]

        c = self.conn.cursor()
        c.execute("SELECT customer_id, remaining_amount, customer_id FROM orders WHERE id=?", (order_id,))
        result = c.fetchone()
        if not result:
            messagebox.showerror("خطأ", "خطأ في استرجاع بيانات الطلب")
            return
            
        customer_id, remaining = result[0], result[1]

        if remaining <= 0:
            messagebox.showinfo("معلومات", "الدفعة مدفوعة بالكامل")
            return

        # نافذة إدخال المبلغ
        dialog = tk.Toplevel(self.root)
        dialog.title("دفع مبلغ")
        dialog.geometry("350x200")
        dialog.configure(bg='#f9f9f9')
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"العميل: {item['values'][1]}", font=('Arial', 12, 'bold'), 
                bg='#f9f9f9').pack(pady=10)
        tk.Label(dialog, text=f"المتبقي: {remaining:.2f} ريال", font=('Arial', 12), 
                bg='#f9f9f9').pack(pady=5)

        entry = tk.Entry(dialog, font=('Arial', 12), justify='center', width=20)
        entry.pack(pady=10)
        entry.insert(0, f"{remaining:.2f}")
        entry.select_range(0, tk.END)

        def submit_payment():
            try:
                amount = float(entry.get())
                if amount <= 0 or amount > remaining:
                    messagebox.showerror("خطأ", f"المبلغ يجب أن يكون بين 1 و {remaining:.2f}")
                    return

                # تحديث الطلب
                c.execute("UPDATE orders SET paid_amount=paid_amount+?, remaining_amount=remaining_amount-? WHERE id=?",
                          (amount, amount, order_id))
                
                # تحديث العميل
                c.execute("UPDATE customers SET paid_amount=paid_amount+?, remaining_amount=remaining_amount-? WHERE id=?",
                          (amount, amount, customer_id))
                
                self.conn.commit()
                messagebox.showinfo("نجاح", f"تم تسجيل دفعة {amount:.2f} ريال بنجاح")
                dialog.destroy()
                self.show_orders()
            except ValueError:
                messagebox.showerror("خطأ", "أدخل رقماً صحيحاً")

        tk.Button(dialog, text="تأكيد الدفع", font=('Arial', 12, 'bold'), bg='#4CAF50', fg='white',
                  width=15, command=submit_payment).pack(pady=10)

    def delete_order(self, tree):
        """حذف طلب"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("تحذير", "اختر طلباً أولاً")
            return

        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الطلب؟"):
            return

        item = tree.item(selected[0])
        order_id = item['values'][0]

        c = self.conn.cursor()
        c.execute("DELETE FROM orders WHERE id=?", (order_id,))
        self.conn.commit()

        messagebox.showinfo("نجاح", "تم حذف الطلب")
        
    
    # [سأختصر هنا للمساحة - الكود الكامل متاح أدناه]

    def create_backup(self):
        """✅ جديد: إنشاء نسخة احتياطية"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"tailor_backup_{timestamp}.db"
            backup_path = filedialog.asksaveasfilename(
                initialname=backup_filename,
                defaultextension=".db",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")]
            )
            
            if backup_path:
                shutil.copy2('tailor.db', backup_path)
                
                # حفظ سجل النسخة
                c = self.conn.cursor()
                size = os.path.getsize(backup_path)
                c.execute("INSERT INTO backups (filename, size_bytes) VALUES (?, ?)", 
                         (backup_path, size))
                self.conn.commit()
                
                messagebox.showinfo("نجاح", f"تم إنشاء نسخة احتياطية:
{backup_path}
الحجم: {size/1024:.1f} KB")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل إنشاء النسخة:
{str(e)}")

    def restore_backup(self):
        """✅ جديد: استعادة نسخة احتياطية"""
        backup_file = filedialog.askopenfilename(
            filetypes=[("Database files", "*.db")]
        )
        if backup_file and messagebox.askyesno("تأكيد", "هل أنت متأكد؟ سيتم استبدال البيانات الحالية!"):
            try:
                shutil.copy2(backup_file, 'tailor.db')
                messagebox.showinfo("نجاح", "تم استعادة النسخة بنجاح!
يرجى إعادة تشغيل البرنامج.")
                self.root.quit()
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل الاستعادة:
{str(e)}")

    def advanced_search_orders(self, tree):
        """✅ جديد: بحث متقدم في الطلبات"""
        search_window = tk.Toplevel(self.root)
        search_window.title("بحث متقدم")
        search_window.geometry("500x400")
        search_window.configure(bg='#f9f9f9')

        # حقول البحث
        search_frame = tk.LabelFrame(search_window, text="معايير البحث", font=('Arial', 12))
        search_frame.pack(padx=20, pady=20, fill='x')

        tk.Label(search_frame, text="اسم العميل:", font=('Arial', 11)).grid(row=0, column=0, padx=10, pady=10, sticky='e')
        customer_search = tk.Entry(search_frame, font=('Arial', 11), width=25)
        customer_search.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(search_frame, text="نوع الثوب:", font=('Arial', 11)).grid(row=1, column=0, padx=10, pady=10, sticky='e')
        cloth_search = tk.Entry(search_frame, font=('Arial', 11), width=25)
        cloth_search.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(search_frame, text="الحالة:", font=('Arial', 11)).grid(row=2, column=0, padx=10, pady=10, sticky='e')
        status_combo = ttk.Combobox(search_frame, font=('Arial', 11), width=23,
                                   values=['📝 تسجيل الطلب', '✂️ القص', '🧵 الخياطة', 
                                          '🔥 الكي', '🎁 جاهز للتسليم'])
        status_combo.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(search_frame, text="المتبقي >:", font=('Arial', 11)).grid(row=3, column=0, padx=10, pady=10, sticky='e')
        remaining_search = tk.Entry(search_frame, font=('Arial', 11), width=25)
        remaining_search.grid(row=3, column=1, padx=10, pady=10)

        def perform_search():
            conditions = []
            params = []
            
            if customer_search.get().strip():
                conditions.append("cu.name LIKE ?")
                params.append(f"%{customer_search.get().strip()}%")
            
            if cloth_search.get().strip():
                conditions.append("o.cloth_type LIKE ?")
                params.append(f"%{cloth_search.get().strip()}%")
            
            if status_combo.get():
                conditions.append("o.status = ?")
                params.append(status_combo.get())
            
            if remaining_search.get().strip():
                try:
                    min_remaining = float(remaining_search.get())
                    conditions.append("o.remaining_amount >= ?")
                    params.append(min_remaining)
                except:
                    pass
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            c = self.conn.cursor()
            c.execute(f"""
                SELECT o.id, cu.name, o.cloth_type, o.quantity, o.status, 
                       o.delivery_date, e.name, o.remaining_amount
                FROM orders o
                JOIN customers cu ON o.customer_id = cu.id
                LEFT JOIN employees e ON o.tailor_id = e.id
                {where_clause}
                ORDER BY o.id DESC
            """, params)
            
            # مسح الجدول وإعادة التعبئة
            for item in tree.get_children():
                tree.delete(item)
            
            for row in c.fetchall():
                tree.insert('', tk.END, values=row)
            
            search_window.destroy()
            messagebox.showinfo("البحث", f"تم العثور على {len(c.fetchall())} نتيجة")

        tk.Button(search_frame, text="🔍 بحث", font=('Arial', 12, 'bold'), 
                 bg='#2196F3', fg='white', command=perform_search).grid(
                 row=4, column=0, columnspan=2, pady=20)

    def show_dashboard(self):
        """لوحة التحكم المُحسّنة مع أزرار جديدة"""
        for w in self.root.winfo_children():
            w.destroy()

        # العنوان مع التاريخ
        today = datetime.now().strftime('%Y/%m/%d - %A')
        title = tk.Label(self.root, text=f"🏠 لوحة التحكم — {self.current_role} | {today}",
                        font=('Arial', 18, 'bold'), bg='#f0f0f0')
        title.pack(pady=20)

        # أزرار سريعة في الأعلى
        quick_actions = tk.Frame(self.root, bg='#f0f0f0')
        quick_actions.pack(pady=10)
        
        tk.Button(quick_actions, text="💾 نسخ احتياطي", font=('Arial', 12, 'bold'), 
                 bg='#FF9800', fg='white', width=15, command=self.create_backup).pack(side='right', padx=5)
        tk.Button(quick_actions, text="📋 الطلبات المتأخرة", font=('Arial', 12, 'bold'), 
                 bg='#f44336', fg='white', width=18, command=self.show_overdue_orders).pack(side='right', padx=5)

        # الشريط الجانبي المُوسّع
        nav_frame = tk.Frame(self.root, bg='#f8f8f8', relief='sunken', bd=2, width=220)
        nav_frame.pack(padx=20, pady=20, fill='y', side='left')
        nav_frame.pack_propagate(False)

        buttons = [
            ("➕ تسجيل طلب جديد", self.show_new_order),
            ("📋 إدارة الطلبات", self.show_orders),
            ("🔍 بحث متقدم", lambda: self.advanced_search_orders(self.get_current_tree())),  # يحتاج tree
        ]

        if self.current_role == 'مدير':
            buttons.extend([
                ("👥 إدارة الموظفين", self.manage_employees),
                ("💱 استعادة نسخة", self.restore_backup)
            ])

        if self.current_role in ['مدير', 'محاسب']:
            buttons.extend([
                ("👤 قائمة الزبائن", self.show_customers_list),
                ("🖨️ طباعة PDF", self.print_customers_pdf)
            ])

        buttons.append(("📊 التقارير", self.show_reports))

        for text, cmd in buttons:
            btn = tk.Button(nav_frame, text=text, font=('Arial', 11, 'bold'), bg='#2196F3', 
                           fg='white', width=22, anchor='w', command=cmd)
            btn.pack(pady=8, padx=8, ipady=8, fill='x')







        # أزرار الخروج
        exit_frame = tk.Frame(self.root, bg='#f0f0f0')
        exit_frame.pack(side='bottom', pady=20)
        tk.Button(exit_frame, text="🚪 خروج", font=('Arial', 14, 'bold'), 
                 bg='#f44336', fg='white', width=15, command=self.logout).pack(pady=10)



         self.show_orders()

    def show_customers_list(self):
        """عرض قائمة الزبائن مع المبالغ"""
        for w in self.root.winfo_children():
            w.destroy()

        title = tk.Label(self.root, text="قائمة الزبائن", font=('Arial', 18, 'bold'), bg='#f0f0f0')
        title.pack(pady=20)

        cols = ('المعرف', 'الاسم', 'الهاتف', 'المجموع', 'المدفوع', 'المتبقي')
        tree = ttk.Treeview(self.root, columns=cols, show='headings', height=20)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor='center')

        c = self.conn.cursor()
        c.execute("SELECT id, name, phone, total_amount, paid_amount, remaining_amount FROM customers WHERE remaining_amount > 0 ORDER BY remaining_amount DESC")

        for r in c.fetchall():
            tree.insert('', tk.END, values=(r[0], r[1], r[2] or '', f"{r[3]:.2f}", f"{r[4]:.2f}", f"{r[5]:.2f}"))

        tree.pack(pady=20, padx=20, fill='both', expand=True)






    def show_overdue_orders(self):
        """✅ جديد: عرض الطلبات المتأخرة"""
        overdue_window = tk.Toplevel(self.root)
        overdue_window.title("الطلبات المتأخرة")
        overdue_window.geometry("900x600")

        cols = ('ر.م', 'العميل', 'الثوب', 'موعد التسليم', 'المتبقي', 'الحالة')
        tree = ttk.Treeview(overdue_window, columns=cols, show='headings', height=20)
        
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=140, anchor='center')

        c = self.conn.cursor()
        overdue_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        c.execute("""
            SELECT o.id, cu.name, o.cloth_type, o.delivery_date, o.remaining_amount, o.status
            FROM orders o JOIN customers cu ON o.customer_id = cu.id
            WHERE o.delivery_date < ? AND o.status != '🎁 جاهز للتسليم'
            ORDER BY o.delivery_date
        """, (overdue_date,))

        overdue_count = 0
        for row in c.fetchall():
            tree.insert('', tk.END, values=row)
            overdue_count += 1

        tree.pack(pady=20, padx=20, fill='both', expand=True)
        
        tk.Label(overdue_window, text=f"عدد الطلبات المتأخرة: {overdue_count}", 
                font=('Arial', 14, 'bold'), bg='orange').pack(pady=10)

    # # أزرار التنقل
        nav = tk.Frame(self.root, bg='#f0f0f0')
        nav.pack(pady=20)
        tk.Button(nav, text="🏠 لوحة التحكم", font=('Arial', 12), bg='#2196F3', fg='white',
                  command=self.show_dashboard).pack(side='left', padx=10)
        tk.Button(nav, text="👈 خروج", font=('Arial', 12), bg='#f44336', fg='white',
                  command=self.logout).pack(side='left', padx=10)

    def print_customers_pdf(self):
        """طباعة قائمة الزبائن كملف PDF"""
        try:
            from fpdf import FPDF
            import arabic_reshaper
            from bidi.algorithm import get_display
        except ImportError:
            messagebox.showerror("خطأ", "يرجى تثبيت: pip install fpdf arabic-reshaper python-bidi")
            return

        c = self.conn.cursor()
        c.execute("SELECT name, phone, total_amount, paid_amount, remaining_amount FROM customers WHERE remaining_amount > 0")
        customers = c.fetchall()

        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        pdf.add_font('Arial', '', 'arial.ttf', uni=True)  # تحتاج خط يدعم العربية
        pdf.set_font("Arial", size=16)
        
        # عنوان
        title = arabic_reshaper.reshape("قائمة الزبائن - نظام الخياطة")
        pdf.cell(0, 10, get_display(title), ln=1, align='C')

        pdf.set_font("Arial", size=12)
        pdf.cell(50, 8, "الاسم", 1, 0, 'C')
        pdf.cell(40, 8, "الهاتف", 1, 0, 'C')
        pdf.cell(35, 8, "المجموع", 1, 0, 'C')
        pdf.cell(35, 8, "المدفوع", 1, 0, 'C')
        pdf.cell(35, 8, "المتبقي", 1, 1, 'C')

        for cust in customers:
            name = arabic_reshaper.reshape(str(cust[0]))
            phone = arabic_reshaper.reshape(str(cust[1] or 'غير محدد'))
            
            pdf.cell(50, 8, get_display(name), 1, 0, 'C')
            pdf.cell(40, 8, get_display(phone), 1, 0, 'C')
            pdf.cell(35, 8, f"{cust[2]:.2f}", 1, 0, 'C')
            pdf.cell(35, 8, f"{cust[3]:.2f}", 1, 0, 'C')
            pdf.cell(35, 8, f"{cust[4]:.2f}", 1, 1, 'C')

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("PDF files", "*.pdf")],
            initialname=f"زبائن_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        if filename:
            pdf.output(filename)
            messagebox.showinfo("نجاح", f"تم الحفظ في:
{filename}")

    def manage_employees(self):
        """إدارة الموظفين/الخياطين (فقط للمدير)"""
        window = tk.Toplevel(self.root)
        window.title("إدارة الموظفين")
        window.geometry("500x500")
        window.configure(bg='#f9f9f9')

        # عرض الموظفين الحاليين
        tk.Label(window, text="الموظفون الحاليون:", font=('Arial', 14, 'bold'), bg='#f9f9f9').pack(pady=10)
        
        cols = ('رقم', 'الاسم', 'الدور')
        tree = ttk.Treeview(window, columns=cols, show='headings', height=8)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        c = self.conn.cursor()
        c.execute("SELECT id, name, role FROM employees")
        for r in c.fetchall():
            tree.insert('', tk.END, values=r)
        
        tree.pack(pady=10, padx=20, fill='x')

        # إضافة موظف جديد
        tk.Label(window, text="إضافة موظف/خياط جديد", font=('Arial', 14, 'bold'), bg='#f9f9f9').pack(pady=(20,10))

        frame = tk.Frame(window, bg='#f9f9f9')
        frame.pack(pady=10)

        tk.Label(frame, text="الاسم:", font=('Arial', 12), bg='#f9f9f9').grid(row=0, column=0, padx=10, pady=5, sticky='e')
        name_entry = tk.Entry(frame, font=('Arial', 12), width=25)
        name_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(frame, text="الدور:", font=('Arial', 12), bg='#f9f9f9').grid(row=1, column=0, padx=10, pady=5, sticky='e')
        role_combo = ttk.Combobox(frame, font=('Arial', 12), values=['خياط', 'موظف'], width=23)
        role_combo.grid(row=1, column=1, padx=10, pady=5)

        def add_employee():
            name = name_entry.get().strip()
            role = role_combo.get().strip()
            if not name or not role:
                messagebox.showwarning("تحذير", "أكمل كل الحقول")
                return

            c = self.conn.cursor()
            c.execute("INSERT INTO employees (name, role) VALUES (?, ?)", (name, role))
            self.conn.commit()
            messagebox.showinfo("نجاح", "تم إضافة الموظف")
            name_entry.delete(0, tk.END)
            role_combo.set('')
            self.manage_employees()  # إعادة تحميل

        tk.Button(window, text="إضافة موظف", font=('Arial', 12, 'bold'), bg='#4CAF50', fg='white',
                  command=add_employee, width=15).pack(pady=20)

        tk.Button(window, text="إغلاق", font=('Arial', 12), bg='#2196F3', fg='white',
                  command=window.destroy).pack(pady=5)

    def show_reports(self):
        """التقارير الإحصائية ✅ تحسين العرض"""
        for w in self.root.winfo_children():
            w.destroy()

        title = tk.Label(self.root, text="📊 التقارير الإحصائية", font=('Arial', 20, 'bold'), bg='#f0f0f0')
        title.pack(pady=30)

        c = self.conn.cursor()

        # الإحصائيات
        stats_queries = {
            "إجمالي الطلبات": "SELECT COUNT(*) FROM orders",
            "إجمالي المبيعات": "SELECT COALESCE(SUM(total_amount), 0) FROM orders",
            "المدفوع": "SELECT COALESCE(SUM(paid_amount), 0) FROM orders",
            "المتبقي": "SELECT COALESCE(SUM(remaining_amount), 0) FROM orders",
            "عدد العملاء": "SELECT COUNT(*) FROM customers",
            "عدد الخياطين": "SELECT COUNT(*) FROM employees WHERE role='خياط'"
        }

        info_frame = tk.Frame(self.root, bg='#e8f4f8', relief='raised', bd=3)
        info_frame.pack(padx=50, pady=20, ipadx=50, ipady=30)

        row = 0
        for label, query in stats_queries.items():
            c.execute(query)
            value = c.fetchone()[0]
            if "ريال" in label:
                value = f"{value:.2f}"
            
            tk.Label(info_frame, text=f"{label}:", font=('Arial', 14, 'bold'), 
                    bg='#e8f4f8', fg='#2E7D32', anchor='e', width=18).grid(
                row=row, column=0, padx=15, pady=10, sticky='e')
            tk.Label(info_frame, text=str(value), font=('Arial', 16, 'bold'), 
                    bg='#e8f4f8', fg='#1976D2', anchor='w', width=15).grid(
                row=row, column=1, padx=15, pady=10, sticky='w')
            row += 1

        # أزرار التنقل
        nav = tk.Frame(self.root, bg='#f0f0f0')
        nav.pack(pady=30)
        tk.Button(nav, text="🏠 لوحة التحكم", font=('Arial', 14, 'bold'), bg='#2196F3', fg='white',
                  command=self.show_dashboard, width=15).pack(side='left', padx=15)
        tk.Button(nav, text="👈 خروج", font=('Arial', 14, 'bold'), bg='#f44336', fg='white',
                  command=self.logout, width=15).pack(side='left', padx=15)

    def logout(self):
        """تسجيل الخروج"""
        self.current_user = None
        self.current_role = None
        self.entries.clear()
        self.show_login()

    def run(self):
        """تشغيل التطبيق"""
        self.root.mainloop()


# تشغيل التطبيق
if __name__ == "__main__":
    app = TailorApp()
    app.run()... باقي الدوال كما هي مع التحسينات السابقة

    def run(self):
        self.root.mainloop()

# تشغيل
if __name__ == "__main__":
    app = TailorApp()
    app.run()
