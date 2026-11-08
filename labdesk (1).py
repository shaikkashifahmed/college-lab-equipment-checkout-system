"""LabDesk - Lab Equipment Checkout System (Tkinter GUI).

Run:  python labdesk.py
Optional, for QR codes:  pip install qrcode pillow
Logins: admin / admin123   |   23EC042 / stud123
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from model import (Store, CATS, CONDS, day, diff, write_csv)

try:                                    # QR codes are optional
    import qrcode
    from PIL import ImageTk
    HAS_QR = True
except ImportError:
    HAS_QR = False

TEAL, DARK, BG, CARD, INK, MUT, LINE = "#0f766e", "#0f2a27", "#f3f6f5", "#ffffff", "#13201e", "#5d6f6b", "#dbe4e1"
LEVEL_BG = {"red": "#fee2e2", "amber": "#fef3c7", "green": "#dcfce7"}
FONT, FONT_B = ("Segoe UI", 10), ("Segoe UI", 10, "bold")


# ------------------------------------------------------------------ helpers
class Form(tk.Toplevel):
    """Small pop-up form. fields = [(key, label, kind, default, options)]; on_ok(values) returns an error text or None."""

    def __init__(self, app, title, fields, on_ok, ok_text="Save", intro=""):
        super().__init__(app)
        self.title(title)
        self.configure(bg=CARD, padx=18, pady=14)
        self.resizable(False, False)
        self.transient(app)
        self.on_ok, self.vars = on_ok, {}
        row = 0
        if intro:
            tk.Label(self, text=intro, bg=CARD, fg=MUT, justify="left", wraplength=360, font=FONT).grid(
                row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
            row += 1
        first = None
        for key, label, kind, default, opts in fields:
            tk.Label(self, text=label, bg=CARD, fg=MUT, font=FONT).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 10))
            var = tk.StringVar(value=str(default))
            self.vars[key] = var
            if kind == "combo":
                w = ttk.Combobox(self, textvariable=var, values=opts, state="readonly", width=36)
            elif kind == "spin":
                w = ttk.Spinbox(self, textvariable=var, from_=0, to=999, width=36)
            else:
                w = ttk.Entry(self, textvariable=var, width=38)
            w.grid(row=row, column=1, pady=4)
            first = first or w
            row += 1
        self.err = tk.Label(self, text="", bg=CARD, fg="#b91c1c", wraplength=360, justify="left", font=FONT)
        self.err.grid(row=row, column=0, columnspan=2, sticky="w", pady=(6, 0))
        bf = tk.Frame(self, bg=CARD)
        bf.grid(row=row + 1, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(bf, text="Cancel", command=self.destroy).pack(side="left", padx=6)
        ttk.Button(bf, text=ok_text, style="Accent.TButton", command=self.submit).pack(side="left")
        self.bind("<Return>", lambda e: self.submit())
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()
        if first:
            first.focus_set()

    def submit(self):
        err = self.on_ok({k: v.get() for k, v in self.vars.items()})
        if err:
            self.err.config(text=err)
        else:
            self.destroy()


def make_tree(parent, cols, widths, height=14):
    """Treeview with a scrollbar. Returns (frame, tree). Rows use iid = record/equipment id."""
    frame = tk.Frame(parent, bg=BG)
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=height, selectmode="browse")
    for c, w in zip(cols, widths):
        tree.heading(c, text=c)
        tree.column(c, width=w, anchor="w")
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    for tag, bg in LEVEL_BG.items():
        tree.tag_configure(tag, background=bg)
    return frame, tree


def bar_chart(parent, rows, suffix="", width=430):
    """Horizontal bar chart drawn on a Canvas. rows = [(label, value)]."""
    h = 30 * max(1, len(rows)) + 10
    cv = tk.Canvas(parent, width=width, height=h, bg=CARD, highlightthickness=0)
    top = max([v for _, v in rows] + [1])
    for i, (label, v) in enumerate(rows):
        y = 8 + i * 30
        cv.create_text(4, y + 10, text=label[:22], anchor="w", font=FONT, fill=INK)
        cv.create_rectangle(170, y + 3, width - 50, y + 17, fill="#e6efed", outline="")
        cv.create_rectangle(170, y + 3, 170 + (width - 220) * v / top, y + 17, fill=TEAL, outline="")
        cv.create_text(width - 4, y + 10, text=f"{v}{suffix}", anchor="e", font=FONT_B, fill=INK)
    return cv


def card(parent, title):
    box = tk.Frame(parent, bg=CARD, highlightbackground=LINE, highlightthickness=1, padx=14, pady=10)
    tk.Label(box, text=title, bg=CARD, fg=INK, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
    return box


# ------------------------------------------------------------------ application
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LabDesk - Lab Equipment Checkout System")
        self.geometry("1200x720")
        self.minsize(1000, 620)
        self.configure(bg=BG)
        self.store, self.user, self.view, self.photo = Store(), None, "dashboard", None
        self.setup_style()
        self.show_login()

    @property
    def admin(self):
        return self.user["role"] == "admin"

    def setup_style(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure(".", font=FONT)
        st.configure("Treeview", rowheight=28, background=CARD, fieldbackground=CARD, foreground=INK, bordercolor=LINE)
        st.configure("Treeview.Heading", font=FONT_B, background="#e6efed", foreground=INK)
        st.map("Treeview", background=[("selected", TEAL)], foreground=[("selected", "#ffffff")])
        st.configure("TButton", padding=(10, 5))
        st.configure("Accent.TButton", background=TEAL, foreground="#ffffff", padding=(10, 5))
        st.map("Accent.TButton", background=[("active", "#0b5f58")])
        st.configure("Danger.TButton", foreground="#b91c1c", padding=(10, 5))

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    # ---------------------------------------------------------------- login
    def show_login(self):
        self.clear()
        self.user = None
        outer = tk.Frame(self, bg=BG)
        outer.place(relx=0.5, rely=0.5, anchor="center")
        box = tk.Frame(outer, bg=CARD, highlightbackground=LINE, highlightthickness=1, padx=30, pady=26)
        box.pack()
        tk.Label(box, text="LabDesk", bg=CARD, fg=TEAL, font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(box, text="Lab Equipment Checkout System", bg=CARD, fg=MUT, font=FONT).pack(anchor="w", pady=(0, 14))
        self.l_id, self.l_pw = tk.StringVar(), tk.StringVar()
        tk.Label(box, text="ID / Roll no", bg=CARD, fg=MUT, font=FONT).pack(anchor="w")
        e1 = ttk.Entry(box, textvariable=self.l_id, width=32)
        e1.pack(pady=(2, 10))
        tk.Label(box, text="Password", bg=CARD, fg=MUT, font=FONT).pack(anchor="w")
        ttk.Entry(box, textvariable=self.l_pw, show="*", width=32).pack(pady=(2, 6))
        self.l_msg = tk.Label(box, text="", bg=CARD, fg="#b91c1c", font=FONT)
        self.l_msg.pack(anchor="w")
        ttk.Button(box, text="Sign in", style="Accent.TButton", command=self.do_login).pack(fill="x", pady=8)
        tk.Label(box, text="Demo: admin / admin123   |   23EC042 / stud123", bg=CARD, fg=MUT,
                 font=("Segoe UI", 9)).pack(anchor="w")
        self.bind("<Return>", lambda e: self.do_login() if self.user is None else None)
        e1.focus_set()

    def do_login(self):
        u = self.store.login(self.l_id.get(), self.l_pw.get())
        if not u:
            self.l_msg.config(text="ID or password is incorrect.")
            return
        self.user, self.view = u, "dashboard"
        self.unbind("<Return>")
        self.show_main()

    # ---------------------------------------------------------------- main frame
    def show_main(self):
        self.clear()
        side = tk.Frame(self, bg=DARK, width=210)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Label(side, text="LabDesk", bg=DARK, fg="#ffffff", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=16, pady=(18, 0))
        who = "Lab assistant" if self.admin else f"{self.user['name']} (Student)"
        tk.Label(side, text=who, bg=DARK, fg="#9fb8b3", font=("Segoe UI", 9), wraplength=180, justify="left").pack(anchor="w", padx=16, pady=(0, 14))
        self.nav_btns = {}
        self.nav_box = tk.Frame(side, bg=DARK)
        self.nav_box.pack(fill="x")
        tk.Button(side, text="Log out", bg="#1c4540", fg="#ffffff", relief="flat", command=self.show_login).pack(side="bottom", fill="x", padx=12, pady=12)
        if self.admin:
            tk.Button(side, text="Reset sample data", bg="#1c4540", fg="#ffffff", relief="flat", command=self.reset).pack(side="bottom", fill="x", padx=12)
        main = tk.Frame(self, bg=BG)
        main.pack(side="left", fill="both", expand=True)
        head = tk.Frame(main, bg=BG)
        head.pack(fill="x", padx=22, pady=(16, 8))
        self.title_lbl = tk.Label(head, text="", bg=BG, fg=INK, font=("Segoe UI", 18, "bold"))
        self.title_lbl.pack(side="left")
        if self.admin:
            ttk.Button(head, text="Issue equipment", style="Accent.TButton", command=self.issue_dialog).pack(side="right")
        ttk.Button(head, text="Scan QR", command=self.scan_dialog).pack(side="right", padx=8)
        self.status = tk.Label(main, text="", bg=BG, fg=TEAL, anchor="w", font=FONT_B)
        self.status.pack(side="bottom", fill="x", padx=22, pady=6)
        self.content = tk.Frame(main, bg=BG)
        self.content.pack(fill="both", expand=True, padx=22)
        self.navigate(self.view)

    def nav_items(self):
        if self.admin:
            return [("dashboard", "Dashboard"), ("equipment", "Equipment"), ("requests", "Requests"), ("records", "Records"),
                    ("reservations", "Reservations"), ("analytics", "Analytics"), ("history", "Student history"),
                    ("reports", "Reports"), ("linkedlist", "Linked list")]
        return [("dashboard", "Dashboard"), ("equipment", "Equipment"), ("records", "My history"), ("reservations", "Reservations")]

    TITLES = {"dashboard": "Dashboard", "equipment": "Equipment", "requests": "Approval requests", "records": "Issue records",
              "reservations": "Reservations", "analytics": "Usage analytics", "history": "Student borrowing history",
              "reports": "Reports", "linkedlist": "Equipment linked list"}

    def navigate(self, key):
        self.view = key
        for w in self.nav_box.winfo_children():
            w.destroy()
        for k, label in self.nav_items():
            if k == "requests" and self.store.pending_count():
                label += f"  ({self.store.pending_count()})"
            tk.Button(self.nav_box, text=label, anchor="w", relief="flat", font=FONT_B if k == key else FONT, bg="#2a4d48" if k == key else DARK,
                      fg="#ffffff", activebackground="#2a4d48", activeforeground="#ffffff", padx=16, pady=6,
                      command=lambda k=k: self.navigate(k)).pack(fill="x")
        title = "My borrowing history" if key == "records" and not self.admin else self.TITLES[key]
        self.title_lbl.config(text=title)
        for w in self.content.winfo_children():
            w.destroy()
        self.status.config(text="")
        getattr(self, "v_" + key)(self.content)

    def refresh(self):
        self.navigate(self.view)

    def say(self, text):
        self.status.config(text=text)

    def pick(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("LabDesk", "Select a row first.")
            return None
        return int(sel[0])

    def with_pick(self, tree, fn):
        item_id = self.pick(tree)
        if item_id is not None:
            fn(item_id)

    def reset(self):
        if messagebox.askyesno("Reset", "Reset all data to the sample set?"):
            self.store.reset()
            self.refresh()

    def eq_label(self, e):
        return f"{e['id']} - {e['name']} ({self.store.available(e)} free)"

    def eq_options(self):
        return [self.eq_label(e) for e in self.store.items.to_list()]

    # ---------------------------------------------------------------- dashboard
    def v_dashboard(self, p):
        s = self.store
        if self.admin:
            items = s.items.to_list()
            kp = [("Total units", sum(e["qty"] for e in items)), ("Available", sum(s.available(e) for e in items)),
                  ("Issued", sum(s.issued_qty(e["id"]) for e in items)), ("Damaged", sum(e["dmg"] for e in items)),
                  ("Overdue", sum(1 for r in s.rec if s.is_overdue(r))), ("Pending requests", s.pending_count())]
        else:
            mine = [r for r in s.rec if r["roll"] == self.user["id"]]
            kp = [("Items I hold", sum(1 for r in mine if r["st"] == "issued")), ("Overdue", sum(1 for r in mine if s.is_overdue(r))),
                  ("Awaiting approval", sum(1 for r in mine if r["st"] == "pending")),
                  ("Reservations", sum(1 for r in s.res if r["roll"] == self.user["id"] and r["st"] == "active"))]
        row = tk.Frame(p, bg=BG)
        row.pack(fill="x", pady=(0, 14))
        for i, (label, val) in enumerate(kp):
            k = tk.Frame(row, bg=CARD, highlightbackground=LINE, highlightthickness=1, padx=14, pady=8)
            k.grid(row=0, column=i, sticky="ew", padx=(0, 10))
            row.columnconfigure(i, weight=1)
            red = label in ("Overdue",) and val
            tk.Label(k, text=str(val), bg=CARD, fg="#b91c1c" if red else INK, font=("Segoe UI", 22, "bold")).pack(anchor="w")
            tk.Label(k, text=label, bg=CARD, fg=MUT, font=("Segoe UI", 9)).pack(anchor="w")
        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True)
        a = card(body, "Due-date and stock alerts")
        a.pack(side="left", fill="both", expand=True, padx=(0, 10))
        alerts = s.alerts(self.user)
        if not alerts:
            tk.Label(a, text="No alerts. Everything is on track.", bg=CARD, fg=MUT, font=FONT).pack(anchor="w")
        for level, title, sub in alerts:
            f = tk.Frame(a, bg=LEVEL_BG[level], padx=10, pady=6)
            f.pack(fill="x", pady=3)
            tk.Label(f, text=title, bg=LEVEL_BG[level], fg=INK, font=FONT_B, anchor="w").pack(fill="x")
            tk.Label(f, text=sub, bg=LEVEL_BG[level], fg=MUT, font=("Segoe UI", 9), anchor="w").pack(fill="x")
        if self.admin:
            b = card(body, "Most borrowed")
            b.pack(side="left", fill="both", padx=(0, 0))
            top = sorted(s.usage(), key=lambda x: -x[1])[:5]
            bar_chart(b, [(e["name"], n) for e, n in top]).pack()

    # ---------------------------------------------------------------- equipment
    def v_equipment(self, p):
        bar = tk.Frame(p, bg=BG)
        bar.pack(fill="x", pady=(0, 8))
        self.q, self.cat = tk.StringVar(), tk.StringVar(value="All labs")
        ttk.Entry(bar, textvariable=self.q, width=30).pack(side="left")
        tk.Label(bar, text="Search by ID, name or lab", bg=BG, fg=MUT, font=("Segoe UI", 9)).pack(side="left", padx=8)
        cb = ttk.Combobox(bar, textvariable=self.cat, values=["All labs"] + CATS, state="readonly", width=30)
        cb.pack(side="left", padx=8)
        cols = ("ID", "Equipment", "Lab", "Location", "Total", "Free", "Issued", "Damaged", "Condition", "Stock")
        frame, tree = make_tree(p, cols, (50, 190, 190, 110, 55, 55, 60, 70, 100, 80))
        self.eq_tree = tree
        if self.admin:
            for text, cmd in (("Delete", self.del_equipment), ("Edit", self.edit_equipment), ("Add equipment", self.add_equipment)):
                ttk.Button(bar, text=text, command=cmd, style="Accent.TButton" if text.startswith("Add") else "TButton").pack(side="right", padx=3)
            ttk.Button(bar, text="Issue", command=lambda: self.with_pick(tree, self.issue_dialog)).pack(side="right", padx=3)
        else:
            ttk.Button(bar, text="Request checkout", style="Accent.TButton", command=lambda: self.with_pick(tree, self.request_dialog)).pack(side="right", padx=3)
        ttk.Button(bar, text="QR code", command=lambda: self.with_pick(tree, self.qr_dialog)).pack(side="right", padx=3)
        frame.pack(fill="both", expand=True, pady=(0, 6))
        self.q.trace_add("write", lambda *a: self.fill_equipment())
        cb.bind("<<ComboboxSelected>>", lambda e: self.fill_equipment())
        self.fill_equipment()

    def fill_equipment(self):
        s, tree = self.store, self.eq_tree
        tree.delete(*tree.get_children())
        cat = "" if self.cat.get() == "All labs" else self.cat.get()
        for e in s.search(self.q.get(), cat):
            a = s.available(e)
            stock = "No stock" if a < 1 else "Low stock" if s.low_stock(e) else "In stock"
            tag = ("red",) if a < 1 else ("amber",) if s.low_stock(e) else ()
            tree.insert("", "end", iid=str(e["id"]), tags=tag, values=(
                e["id"], e["name"], e["cat"], e["loc"], e["qty"], a, s.issued_qty(e["id"]), e["dmg"], e["cond"], stock))

    def eq_fields(self, e=None):
        e = e or {}
        return [("name", "Name", "entry", e.get("name", ""), None), ("cat", "Lab / category", "combo", e.get("cat", CATS[0]), CATS),
                ("qty", "Quantity", "spin", e.get("qty", 1), None), ("loc", "Location", "entry", e.get("loc", ""), None),
                ("min", "Low-stock minimum", "spin", e.get("min", 2), None),
                ("cond", "Condition", "combo", e.get("cond", "Good"), CONDS), ("dmg", "Damaged units", "spin", e.get("dmg", 0), None)]

    def add_equipment(self):
        def ok(v):
            err = self.store.add_equipment(v)
            if not err:
                self.refresh()
                self.say("Equipment added to the linked list.")
            return err
        Form(self, "Add equipment", self.eq_fields(), ok, "Add to list")

    def edit_equipment(self):
        item_id = self.pick(self.eq_tree)
        if item_id is None:
            return

        def ok(v):
            err = self.store.update_equipment(item_id, v)
            if not err:
                self.refresh()
                self.say("Equipment updated.")
            return err
        Form(self, "Edit equipment", self.eq_fields(self.store.equipment(item_id)), ok)

    def del_equipment(self):
        item_id = self.pick(self.eq_tree)
        if item_id is None:
            return
        e = self.store.equipment(item_id)
        if messagebox.askyesno("Delete", f"Delete {e['name']}?"):
            err = self.store.delete_equipment(item_id)
            if err:
                messagebox.showerror("LabDesk", err)
            else:
                self.refresh()
                self.say("Equipment deleted.")

    # ---------------------------------------------------------------- issue / request / return
    def issue_dialog(self, item_id=None):
        if self.view == "equipment" and item_id is None and self.eq_tree.selection():
            item_id = int(self.eq_tree.selection()[0])
        opts = self.eq_options()
        default = next((o for o in opts if item_id and o.startswith(f"{item_id} ")), opts[0])

        def ok(v):
            err = self.store.issue(int(v["eq"].split()[0]), v["roll"], v["name"], int(v["days"]))
            if not err:
                self.refresh()
                self.say(f"Issued. Due {day(int(v['days']))}.")
            return err
        Form(self, "Issue equipment", [("eq", "Equipment", "combo", default, opts), ("roll", "Roll no", "entry", "", None),
                                       ("name", "Student name", "entry", "", None), ("days", "Loan period (days)", "combo", "7", ["3", "7", "14"])],
             ok, "Issue")

    def request_dialog(self, item_id=None):
        opts = self.eq_options()
        default = next((o for o in opts if item_id and o.startswith(f"{item_id} ")), opts[0])

        def ok(v):
            err = self.store.request(int(v["eq"].split()[0]), self.user["id"], self.user["name"], int(v["days"]))
            if not err:
                self.refresh()
                self.say("Request sent for approval.")
            return err
        Form(self, "Request checkout", [("eq", "Equipment", "combo", default, opts), ("days", "Loan period (days)", "combo", "7", ["3", "7", "14"])],
             ok, "Send request", "The lab assistant will approve or reject your request.")

    def return_dialog(self, rid):
        r = next((x for x in self.store.rec if x["id"] == rid), None)
        if not r or r["st"] != "issued":
            messagebox.showinfo("LabDesk", "That item is not currently on loan.")
            return
        late = f" ({diff(r['due'])} day(s) late)" if self.store.is_overdue(r) else ""

        def ok(v):
            err = self.store.return_item(rid, v["dmg"], v["note"])
            if not err:
                self.refresh()
                self.say("Returned. Damage reported." if int(v["dmg"]) else "Returned.")
            return err
        Form(self, "Return equipment", [("dmg", "Units damaged / not working", "spin", 0, None), ("note", "What happened (if damaged)", "entry", "", None)],
             ok, "Confirm return", f"{self.store.equipment(r['eq'])['name']} - due {r['due']}{late}")

    # ---------------------------------------------------------------- QR + scan
    def qr_dialog(self, item_id):
        if item_id is None:
            return
        e = self.store.equipment(item_id)
        win = tk.Toplevel(self)
        win.title(f"QR code - {e['name']}")
        win.configure(bg=CARD, padx=20, pady=16)
        code = f"LABDESK:{e['id']}"
        if HAS_QR:
            img = qrcode.make(code).get_image().resize((240, 240))
            self.photo = ImageTk.PhotoImage(img)
            tk.Label(win, image=self.photo, bg=CARD).pack()

            def save():
                path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=f"qr-{e['id']}.png")
                if path:
                    img.save(path)
            ttk.Button(win, text="Save as PNG", command=save).pack(pady=6)
        else:
            tk.Label(win, text="QR image needs:  pip install qrcode pillow", bg=CARD, fg=MUT, font=FONT).pack(pady=10)
        tk.Label(win, text=f"{e['name']}\nCode: {code}", bg=CARD, fg=INK, font=FONT_B).pack()
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=(10, 0))

    def scan_dialog(self):
        def ok(v):
            item_id = self.store.parse_code(v["code"])
            if item_id is None or not self.store.equipment(item_id):
                return "No equipment found for that code."
            self.after(50, lambda: self.item_dialog(item_id))
            return None
        Form(self, "Scan equipment QR", [("code", "Scan or type the code", "entry", "LABDESK:", None)], ok, "Look up",
             "Point a USB or phone scanner at the QR code, or type the code printed under it.")

    def item_dialog(self, item_id):
        s, e = self.store, self.store.equipment(item_id)
        win = tk.Toplevel(self)
        win.title(e["name"])
        win.configure(bg=CARD, padx=20, pady=16)
        tk.Label(win, text=f"{e['id']} - {e['name']}", bg=CARD, fg=INK, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(win, text=f"{e['cat']} | {e['loc']}\nAvailable {s.available(e)} of {e['qty']} | Damaged {e['dmg']} | {e['cond']}",
                 bg=CARD, fg=MUT, justify="left", font=FONT).pack(anchor="w", pady=8)
        row = tk.Frame(win, bg=CARD)
        row.pack(anchor="w")
        act = (lambda: (win.destroy(), self.issue_dialog(item_id))) if self.admin else (lambda: (win.destroy(), self.request_dialog(item_id)))
        ttk.Button(row, text="Issue" if self.admin else "Request checkout", style="Accent.TButton", command=act).pack(side="left", padx=(0, 6))
        held = next((r for r in s.rec if r["eq"] == item_id and r["st"] == "issued" and (self.admin or r["roll"] == self.user["id"])), None)
        if held:
            ttk.Button(row, text="Return", command=lambda: (win.destroy(), self.return_dialog(held["id"]))).pack(side="left")
        ttk.Button(win, text="Close", command=win.destroy).pack(anchor="e", pady=(12, 0))

    # ---------------------------------------------------------------- requests (admin)
    def v_requests(self, p):
        s = self.store
        bar = tk.Frame(p, bg=BG)
        bar.pack(fill="x", pady=(0, 8))
        frame, tree = make_tree(p, ("Rec", "Student", "Roll no", "Equipment", "Requested", "Loan (days)"), (60, 180, 110, 220, 110, 90))
        for r in s.rec:
            if r["st"] == "pending":
                tree.insert("", "end", iid=str(r["id"]), values=(r["id"], r["name"], r["roll"], s.equipment(r["eq"])["name"], r["req"], r["days"]))

        def act(fn, msg):
            rid = self.pick(tree)
            if rid is None:
                return
            err = fn(rid)
            if err:
                messagebox.showerror("LabDesk", err)
            else:
                self.refresh()
                self.say(msg)
        ttk.Button(bar, text="Reject", command=lambda: act(s.reject, "Request rejected.")).pack(side="right", padx=3)
        ttk.Button(bar, text="Approve", style="Accent.TButton", command=lambda: act(s.approve, "Request approved and issued.")).pack(side="right", padx=3)
        tk.Label(bar, text="Pending checkout requests from students", bg=BG, fg=MUT, font=FONT).pack(side="left")
        frame.pack(fill="both", expand=True)

    # ---------------------------------------------------------------- records
    def v_records(self, p):
        bar = tk.Frame(p, bg=BG)
        bar.pack(fill="x", pady=(0, 8))
        self.rf, self.rq = tk.StringVar(value="All"), tk.StringVar()
        cb = ttk.Combobox(bar, textvariable=self.rf, values=["All", "Issued", "Overdue", "Returned", "Pending", "Rejected"], state="readonly", width=14)
        cb.pack(side="left")
        if self.admin:
            ttk.Entry(bar, textvariable=self.rq, width=28).pack(side="left", padx=8)
            tk.Label(bar, text="Search roll no or student", bg=BG, fg=MUT, font=("Segoe UI", 9)).pack(side="left")
        cols = ("Rec", "Student", "Equipment", "Issued", "Due", "Returned", "Damaged", "Status")
        frame, tree = make_tree(p, cols, (50, 190, 200, 100, 100, 100, 70, 90))
        self.rec_tree = tree
        ttk.Button(bar, text="Return selected", style="Accent.TButton", command=lambda: self.pick_return(tree)).pack(side="right")
        frame.pack(fill="both", expand=True)
        self.rq.trace_add("write", lambda *a: self.fill_records())
        cb.bind("<<ComboboxSelected>>", lambda e: self.fill_records())
        self.fill_records()

    def pick_return(self, tree):
        rid = self.pick(tree)
        if rid is not None:
            self.return_dialog(rid)

    def fill_records(self):
        s, tree = self.store, self.rec_tree
        tree.delete(*tree.get_children())
        f, q = self.rf.get().lower(), self.rq.get().strip().lower()
        for r in sorted(s.rec, key=lambda x: -x["id"]):
            if not self.admin and r["roll"] != self.user["id"]:
                continue
            over = s.is_overdue(r)
            status = "Overdue" if over else r["st"].capitalize()
            if f != "all" and f != r["st"] and not (f == "overdue" and over):
                continue
            if q and q not in f"{r['roll']} {r['name']}".lower():
                continue
            e = s.equipment(r["eq"])
            tree.insert("", "end", iid=str(r["id"]), tags=("red",) if over else ("green",) if r["st"] == "returned" else (), values=(
                r["id"], f"{r['name']} ({r['roll']})", e["name"] if e else "Deleted item", r["iss"] or "-", r["due"] or "-", r["ret"] or "-", r["dmg"], status))

    # ---------------------------------------------------------------- reservations
    def v_reservations(self, p):
        s = self.store
        form = card(p, "Reserve for a lab session")
        form.pack(side="left", fill="y", padx=(0, 12), anchor="n")
        opts = self.eq_options()
        self.rv = {k: tk.StringVar(value=v) for k, v in (("eq", opts[0]), ("date", day(1)), ("qty", "1"), ("roll", ""), ("name", ""))}
        fields = [("Equipment", "eq", "combo"), ("Session date (YYYY-MM-DD)", "date", "entry"), ("Quantity", "qty", "entry")]
        if self.admin:
            fields += [("Roll no", "roll", "entry"), ("Student name", "name", "entry")]
        for label, key, kind in fields:
            tk.Label(form, text=label, bg=CARD, fg=MUT, font=FONT).pack(anchor="w")
            if kind == "combo":
                ttk.Combobox(form, textvariable=self.rv[key], values=opts, state="readonly", width=34).pack(pady=(0, 6))
            else:
                ttk.Entry(form, textvariable=self.rv[key], width=36).pack(pady=(0, 6))
        msg = tk.Label(form, text="", bg=CARD, fg="#b91c1c", wraplength=260, justify="left", font=FONT)
        msg.pack(anchor="w")

        def reserve():
            v = {k: x.get() for k, x in self.rv.items()}
            roll, name = (v["roll"], v["name"]) if self.admin else (self.user["id"], self.user["name"])
            err = s.reserve(int(v["eq"].split()[0]), roll, name, v["date"], v["qty"])
            if err:
                msg.config(text=err)
            else:
                self.refresh()
                self.say(f"Reserved for {v['date']}.")
        ttk.Button(form, text="Reserve", style="Accent.TButton", command=reserve).pack(anchor="e", pady=6)
        right = tk.Frame(p, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        frame, tree = make_tree(right, ("ID", "Date", "Equipment", "Qty", "Student", "Status"), (40, 90, 170, 40, 150, 80))
        for r in sorted(s.res, key=lambda x: x["date"]):
            if self.admin or r["roll"] == self.user["id"]:
                e = s.equipment(r["eq"])
                tree.insert("", "end", iid=str(r["id"]), tags=("green",) if r["st"] == "active" else (),
                            values=(r["id"], r["date"], e["name"] if e else "", r["qty"], f"{r['name']} ({r['roll']})", r["st"].capitalize()))

        def cancel():
            rid = self.pick(tree)
            if rid is not None:
                s.cancel_reservation(rid)
                self.refresh()
        ttk.Button(right, text="Cancel selected", command=cancel).pack(side="bottom", anchor="e", pady=6)
        frame.pack(fill="both", expand=True)

    # ---------------------------------------------------------------- analytics (admin)
    def v_analytics(self, p):
        s = self.store
        use = sorted(s.usage(), key=lambda x: -x[1])
        top = card(p, "Frequently borrowed")
        top.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        bar_chart(top, [(e["name"], n) for e, n in use[:5]]).pack()
        least = card(p, "Least used")
        least.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        bar_chart(least, [(e["name"], n) for e, n in use[::-1][:5]]).pack()
        util = card(p, "Utilisation right now (share of units on loan)")
        util.grid(row=1, column=0, columnspan=2, sticky="nsew")
        rows = sorted(((e["name"], round(s.issued_qty(e["id"]) / e["qty"] * 100)) for e in s.items.to_list()), key=lambda x: -x[1])[:8]
        bar_chart(util, rows, "%", 880).pack()
        p.columnconfigure(0, weight=1)
        p.columnconfigure(1, weight=1)

    # ---------------------------------------------------------------- history (admin)
    def v_history(self, p):
        s = self.store
        bar = tk.Frame(p, bg=BG)
        bar.pack(fill="x", pady=(0, 8))
        roll = tk.StringVar()
        ttk.Entry(bar, textvariable=roll, width=24).pack(side="left")
        summary = tk.Label(bar, text="Enter a roll number, e.g. 23EC042", bg=BG, fg=MUT, font=FONT)
        frame, tree = make_tree(p, ("Rec", "Equipment", "Issued", "Due", "Returned", "Damaged", "Status"), (50, 220, 100, 100, 100, 70, 90))

        def show(*_):
            tree.delete(*tree.get_children())
            rows = s.history(roll.get())
            for r in rows:
                over = s.is_overdue(r)
                tree.insert("", "end", iid=str(r["id"]), tags=("red",) if over else (), values=(
                    r["id"], s.equipment(r["eq"])["name"] if s.equipment(r["eq"]) else "Deleted item", r["iss"], r["due"], r["ret"] or "-", r["dmg"],
                    "Overdue" if over else r["st"].capitalize()))
            summary.config(text=f"{rows[0]['name']}: {len(rows)} loans, {sum(1 for r in rows if r['dmg'])} with damage reports" if rows else "No borrowing history for that roll number.")
        ttk.Button(bar, text="Show history", style="Accent.TButton", command=show).pack(side="left", padx=8)
        summary.pack(side="left")
        frame.pack(fill="both", expand=True)

    # ---------------------------------------------------------------- reports (admin)
    def v_reports(self, p):
        s = self.store
        bar = tk.Frame(p, bg=BG)
        bar.pack(fill="x", pady=(0, 8))

        def export(name, header, rows):
            path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"{name}-{day()}.csv", filetypes=[("CSV file", "*.csv")])
            if path:
                write_csv(path, header, rows)
                self.say(f"Saved {name} report.")
        ttk.Button(bar, text="Inventory report", style="Accent.TButton", command=lambda: export(
            "inventory", ["ID", "Name", "Category", "Location", "Total", "Available", "Issued", "Damaged", "Condition"], s.inventory_rows())).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Issue report", style="Accent.TButton", command=lambda: export(
            "issues", ["Rec", "Roll", "Student", "Equipment ID", "Equipment", "Issued", "Due", "Status"], s.issue_rows())).pack(side="left", padx=6)
        ttk.Button(bar, text="Return report", style="Accent.TButton", command=lambda: export(
            "returns", ["Rec", "Roll", "Student", "Equipment", "Issued", "Due", "Returned", "Days late", "Damaged", "Note"], s.return_rows())).pack(side="left", padx=6)
        tk.Label(bar, text="Reports are saved as CSV files that open in Excel.", bg=BG, fg=MUT, font=FONT).pack(side="left", padx=10)
        frame, tree = make_tree(p, ("ID", "Equipment", "Total", "Available", "Issued", "Damaged", "Condition"), (50, 260, 70, 80, 70, 80, 110))
        for row in s.inventory_rows():
            tree.insert("", "end", values=(row[0], row[1], row[4], row[5], row[6], row[7], row[8]))
        frame.pack(fill="both", expand=True)

    # ---------------------------------------------------------------- linked list view (admin)
    def v_linkedlist(self, p):
        bar = tk.Frame(p, bg=BG)
        bar.pack(fill="x", pady=(0, 8))
        tid = tk.StringVar()
        ttk.Entry(bar, textvariable=tid, width=14).pack(side="left")
        msg = tk.Label(bar, text="Each node points to the next. Search starts at HEAD.", bg=BG, fg=MUT, font=FONT)
        cv = tk.Canvas(p, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        sb = ttk.Scrollbar(p, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=sb.set)

        def draw(hit=None, seen=()):
            cv.delete("all")
            nodes, per, w, h, gap, x0, rh = self.store.items.to_list(), 6, 110, 52, 34, 80, 96
            cv.create_text(36, 40, text="HEAD", font=FONT_B, fill=TEAL)
            cv.create_line(58, 40, x0, 40, arrow=tk.LAST, width=2)
            for i, e in enumerate(nodes):
                r, c = divmod(i, per)
                x, y = x0 + c * (w + gap), 14 + r * rh
                fill = "#dcfce7" if e["id"] == hit else "#fef3c7" if e["id"] in seen else "#e6efed"
                cv.create_rectangle(x, y, x + w, y + h, fill=fill, outline=TEAL, width=2)
                cv.create_text(x + w / 2, y + 16, text=str(e["id"]), font=FONT_B, fill=INK)
                cv.create_text(x + w / 2, y + 36, text=e["name"][:16], font=("Segoe UI", 8), fill=MUT)
                mid = y + h / 2
                if i == len(nodes) - 1:
                    cv.create_line(x + w, mid, x + w + gap, mid, arrow=tk.LAST, width=2)
                    cv.create_text(x + w + gap + 22, mid, text="NULL", font=FONT_B, fill=MUT)
                elif c == per - 1:      # wrap to the next row
                    cv.create_line(x + w, mid, x + w + 16, mid, x + w + 16, y + rh - 14, x0 - 18, y + rh - 14, x0 - 18, mid + rh,
                                   x0, mid + rh, arrow=tk.LAST, width=2)
                else:
                    cv.create_line(x + w, mid, x + w + gap, mid, arrow=tk.LAST, width=2)
            rows = (len(nodes) - 1) // per + 1
            cv.configure(scrollregion=(0, 0, 900, 30 + rows * rh))

        def trace(*_):
            try:
                target = int(tid.get())
            except ValueError:
                msg.config(text="Enter a numeric ID, e.g. 103.")
                return
            found, visited = self.store.items.trace(target)
            draw(target if found else None, visited)
            msg.config(text=f"Found after {len(visited)} comparison(s)." if found else f"Not found. Checked {len(visited)} nodes and reached NULL.")
        ttk.Button(bar, text="Trace search", style="Accent.TButton", command=trace).pack(side="left", padx=8)
        msg.pack(side="left")
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        draw()


if __name__ == "__main__":
    App().mainloop()
