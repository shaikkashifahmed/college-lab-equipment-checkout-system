"""LabDesk model: linked list + business rules. No GUI code lives here."""
import csv
import json
import os
import re
from datetime import date, timedelta

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "labdesk_data.json")
CATS = ["Computer Lab", "Engineering Physics Lab", "Basic Electrical Engineering Lab", "English Lab",
        "Engineering Chemistry Lab", "CSE Lab", "CSE (AIML) Lab", "CSD Lab", "Mechanical Engineering Lab",
        "EEE Lab", "ECE Lab", "Civil Engineering Lab"]
CONDS = ["Good", "Fair", "Needs repair"]
ROLL_RE = re.compile(r"^[A-Za-z0-9]{4,20}$")


def day(n=0):
    return (date.today() + timedelta(days=n)).isoformat()


def diff(a, b=None):
    """Days from date a to date b (default today)."""
    return (date.fromisoformat(b or day())) .toordinal() - date.fromisoformat(a).toordinal()


# ---------------------------------------------------------------- linked list
class Node:
    """One equipment record plus a pointer to the next node."""
    __slots__ = ("data", "next")

    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    """Singly linked list with head and tail pointers."""

    def __init__(self):
        self.head = self.tail = None
        self.size = 0

    def add(self, data):                       # O(1): link after the tail
        node = Node(data)
        if self.tail:
            self.tail.next = node
        else:
            self.head = node
        self.tail = node
        self.size += 1

    def find(self, item_id):                   # O(n): walk from HEAD until match or NULL
        cur = self.head
        while cur:
            if cur.data["id"] == item_id:
                return cur
            cur = cur.next
        return None

    def trace(self, item_id):
        """Like find, but also returns the IDs visited (for the Linked list screen)."""
        visited, cur = [], self.head
        while cur:
            visited.append(cur.data["id"])
            if cur.data["id"] == item_id:
                return True, visited
            cur = cur.next
        return False, visited

    def remove(self, item_id):                 # O(n): find the node, then bypass it
        prev, cur = None, self.head
        while cur:
            if cur.data["id"] == item_id:
                if prev:
                    prev.next = cur.next
                else:
                    self.head = cur.next
                if cur is self.tail:
                    self.tail = prev
                self.size -= 1
                return True
            prev, cur = cur, cur.next
        return False

    def to_list(self):
        out, cur = [], self.head
        while cur:
            out.append(cur.data)
            cur = cur.next
        return out


# ---------------------------------------------------------------- sample data
def seed():
    rows = [
        (101, "Digital Multimeter", 2, 12, "Shelf B1", "Good", 3), (102, "Oscilloscope", 2, 6, "Bench 2", "Good", 2),
        (103, "Vernier Caliper", 1, 15, "Cupboard A", "Good", 4), (104, "Spectrometer", 1, 2, "Dark room", "Needs repair", 2),
        (105, "Burette Set", 4, 20, "Cupboard C", "Good", 5), (106, "pH Meter", 4, 5, "Shelf C2", "Good", 2),
        (107, "Raspberry Pi Kit", 0, 10, "Rack 1", "Good", 3), (108, "Headset with Mic", 3, 18, "Cabinet E", "Good", 5),
        (109, "Desktop Computer (i5)", 5, 40, "CSE Lab 1", "Good", 5), (110, "Network Switch 24-port", 5, 6, "Rack N1", "Good", 2),
        (111, "Wireless Router", 5, 8, "Rack N2", "Good", 2), (112, "Arduino Uno Kit", 5, 15, "Cupboard S1", "Good", 4),
        (113, "NVIDIA Jetson Nano Kit", 6, 8, "AIML Store", "Good", 2), (114, "GPU Workstation", 6, 4, "AIML Lab 2", "Good", 1),
        (115, "Pi Camera AI Kit", 6, 10, "AIML Store", "Fair", 3), (116, "Graphics Tablet", 7, 12, "CSD Studio", "Good", 3),
        (117, "VR Headset", 7, 5, "CSD Studio", "Good", 1), (118, "Pen Display Monitor", 7, 6, "CSD Studio", "Good", 2),
        (119, "Vernier Height Gauge", 8, 8, "Metrology Rack", "Good", 2), (120, "Micrometer Screw Gauge", 8, 20, "Metrology Rack", "Good", 5),
        (121, "Digital Tachometer", 8, 6, "Cabinet M2", "Good", 2), (122, "Bench Vice", 8, 10, "Workshop W1", "Fair", 3),
        (123, "Lathe Tool Kit", 8, 6, "Workshop W2", "Good", 2), (124, "Infrared Thermometer", 8, 8, "Cabinet M1", "Good", 2),
        (125, "Function Generator", 9, 8, "EEE Bench 3", "Good", 2), (126, "DC Power Supply", 9, 12, "EEE Bench 1", "Good", 3),
        (127, "Clamp Meter", 9, 10, "Shelf E2", "Good", 3), (128, "Insulation Tester (Megger)", 9, 3, "Cabinet E1", "Good", 1),
        (129, "Rheostat", 9, 15, "Shelf E3", "Good", 4), (130, "Logic Analyzer", 10, 5, "ECE Bench 2", "Good", 1),
        (131, "FPGA Board (Basys 3)", 10, 8, "ECE Store", "Good", 2), (132, "Soldering Station", 10, 12, "ECE Bench 1", "Good", 3),
        (133, "Spectrum Analyzer", 10, 2, "ECE Cabinet", "Good", 1), (134, "Total Station", 11, 2, "Survey Room", "Good", 1),
        (135, "Dumpy Level", 11, 6, "Survey Room", "Good", 2), (136, "Measuring Tape (30 m)", 11, 15, "Survey Room", "Good", 4),
        (137, "Vicat Apparatus", 11, 4, "Concrete Lab", "Fair", 1)]
    eq = [dict(id=i, name=n, cat=CATS[c], qty=q, loc=l, cond=cd, min=m, dmg=1 if i == 104 else 0) for i, n, c, q, l, cd, m in rows]
    A, R = ("23EC042", "Asha Rao"), ("23EC051", "Ravi Kumar")

    def rec(i, e, who, st, iss, due, **x):
        return dict(id=i, eq=e, roll=who[0], name=who[1], qty=1, st=st, req=iss or day(), days=7, iss=iss, due=due,
                    ret=x.get("ret"), dmg=x.get("dmg", 0), note=x.get("note", ""))
    recs = [rec(1, 102, A, "issued", day(-9), day(-2)), rec(2, 101, R, "issued", day(-5), day(1)),
            rec(3, 107, A, "returned", day(-14), day(-7), ret=day(-8)),
            rec(4, 104, R, "returned", day(-12), day(-5), ret=day(-5), dmg=1, note="Lens cracked"),
            rec(5, 103, A, "pending", None, None),
            rec(6, 101, A, "returned", day(-20), day(-13), ret=day(-14)), rec(7, 101, R, "returned", day(-30), day(-23), ret=day(-22)),
            rec(8, 103, R, "returned", day(-18), day(-11), ret=day(-12))]
    return dict(eq=eq, rec=recs, nid=138, rid=9, sid=2,
                users=[dict(id="admin", name="Lab Assistant", role="admin", pw="admin123"),
                       dict(id=A[0], name=A[1], role="student", pw="stud123"),
                       dict(id=R[0], name=R[1], role="student", pw="stud123")],
                res=[dict(id=1, eq=106, roll=A[0], name=A[1], date=day(3), qty=2, st="active")])


# ---------------------------------------------------------------- store + rules
class Store:
    def __init__(self, path=DATA_FILE):
        self.path = path
        self.load()

    # persistence ---------------------------------------------------
    def load(self):
        data = None
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, ValueError):
                data = None
        self.d = data or seed()
        self.items = LinkedList()
        for e in self.d["eq"]:
            self.items.add(e)

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.d, f, indent=1)
        except OSError:
            pass

    def reset(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        self.load()

    # lookups -------------------------------------------------------
    @property
    def rec(self):
        return self.d["rec"]

    @property
    def res(self):
        return self.d["res"]

    def login(self, uid, pw):
        for u in self.d["users"]:
            if u["id"].lower() == uid.strip().lower() and u["pw"] == pw:
                return u
        return None

    def equipment(self, item_id):
        n = self.items.find(item_id)
        return n.data if n else None

    def issued_qty(self, item_id):
        return sum(r["qty"] for r in self.rec if r["eq"] == item_id and r["st"] == "issued")

    def available(self, e):
        return e["qty"] - e["dmg"] - self.issued_qty(e["id"])

    def low_stock(self, e):
        return self.available(e) < e["min"]

    @staticmethod
    def is_overdue(r):
        return r["st"] == "issued" and r["due"] < day()

    @staticmethod
    def is_soon(r):
        return r["st"] == "issued" and day() <= r["due"] <= day(2)

    def pending_count(self):
        return sum(1 for r in self.rec if r["st"] == "pending")

    def search(self, text="", cat=""):
        """Search by ID, name or lab (walks every node: O(n))."""
        t = text.strip().lower()
        return [e for e in self.items.to_list()
                if (not cat or e["cat"] == cat) and (not t or t in f"{e['id']} {e['name']} {e['cat']}".lower())]

    @staticmethod
    def parse_code(text):
        m = re.search(r"\d+", text or "")
        return int(m.group()) if m else None

    # equipment management -----------------------------------------
    def _check_eq(self, f, existing=None):
        name, loc = f.get("name", "").strip(), f.get("loc", "").strip()
        if not name or not loc:
            return "Enter a name and a location."
        try:
            qty, mn, dmg = int(f["qty"]), int(f["min"]), int(f.get("dmg") or 0)
        except (ValueError, KeyError):
            return "Quantity, minimum and damaged units must be whole numbers."
        if qty < 1 or mn < 0 or dmg < 0:
            return "Quantity must be 1 or more; minimum and damaged cannot be negative."
        if dmg > qty or (existing and qty - dmg < self.issued_qty(existing["id"])):
            return "Damaged units and units on loan cannot exceed the quantity."
        if f.get("cat") not in CATS or f.get("cond") not in CONDS:
            return "Choose a valid lab and condition."
        return dict(name=name, loc=loc, qty=qty, min=mn, dmg=dmg, cat=f["cat"], cond=f["cond"])

    def add_equipment(self, f):
        v = self._check_eq(f)
        if isinstance(v, str):
            return v
        v["id"] = self.d["nid"]
        self.d["nid"] += 1
        self.d["eq"].append(v)
        self.items.add(v)                       # O(1) tail insert
        self.save()

    def update_equipment(self, item_id, f):
        e = self.equipment(item_id)
        v = self._check_eq(f, e)
        if isinstance(v, str):
            return v
        e.update(v)
        self.save()

    def delete_equipment(self, item_id):
        if self.issued_qty(item_id):
            return "Return all units before deleting."
        self.items.remove(item_id)
        self.d["eq"] = [e for e in self.d["eq"] if e["id"] != item_id]
        self.save()

    # issue / approval / return ------------------------------------
    def _new_record(self, item_id, roll, name, days, status):
        e = self.equipment(item_id)
        roll, name = roll.strip().upper(), name.strip()
        if not e:
            return "Choose equipment."
        if not ROLL_RE.match(roll):
            return "Enter a valid roll number."
        if not name:
            return "Enter the student name."
        if days not in (3, 7, 14):
            return "Choose a loan period of 3, 7 or 14 days."
        if self.available(e) < 1:
            return f"{e['name']} has none available."
        r = dict(id=self.d["rid"], eq=item_id, roll=roll, name=name, qty=1, st=status, req=day(), days=days,
                 iss=None, due=None, ret=None, dmg=0, note="")
        if status == "issued":
            r["iss"], r["due"] = day(), day(days)
        self.d["rid"] += 1
        self.rec.append(r)
        self.save()

    def issue(self, item_id, roll, name, days):
        return self._new_record(item_id, roll, name, days, "issued")

    def request(self, item_id, roll, name, days):
        return self._new_record(item_id, roll, name, days, "pending")

    def approve(self, rid):
        r = next((x for x in self.rec if x["id"] == rid and x["st"] == "pending"), None)
        if not r:
            return "That request is no longer pending."
        if self.available(self.equipment(r["eq"])) < r["qty"]:
            return "Not enough stock to approve."
        r.update(st="issued", iss=day(), due=day(r["days"]))
        self.save()

    def reject(self, rid):
        r = next((x for x in self.rec if x["id"] == rid and x["st"] == "pending"), None)
        if not r:
            return "That request is no longer pending."
        r["st"] = "rejected"
        self.save()

    def return_item(self, rid, dmg, note=""):
        r = next((x for x in self.rec if x["id"] == rid and x["st"] == "issued"), None)
        if not r:
            return "That item is not on loan."
        try:
            dmg = int(dmg)
        except ValueError:
            return "Damaged units must be a whole number."
        if dmg < 0 or dmg > r["qty"]:
            return f"Damaged units must be between 0 and {r['qty']}."
        if dmg and not note.strip():
            return "Describe the damage so the lab assistant can follow up."
        r.update(st="returned", ret=day(), dmg=dmg, note=note.strip())
        if dmg:
            e = self.equipment(r["eq"])
            e["dmg"] += dmg
            e["cond"] = "Needs repair"
        self.save()

    # reservations -------------------------------------------------
    def reserve(self, item_id, roll, name, on_date, qty):
        e = self.equipment(item_id)
        try:
            d = date.fromisoformat(on_date.strip())
            qty = int(qty)
        except ValueError:
            return "Enter the date as YYYY-MM-DD and a whole-number quantity."
        if not e or not roll.strip() or not name.strip():
            return "Choose equipment and enter roll no and name."
        if d.isoformat() < day(1):
            return "Pick a date from tomorrow onward."
        busy = sum(r["qty"] for r in self.rec if r["eq"] == item_id and r["st"] == "issued" and r["due"] >= d.isoformat())
        busy += sum(r["qty"] for r in self.res if r["eq"] == item_id and r["st"] == "active" and r["date"] == d.isoformat())
        free = e["qty"] - e["dmg"] - busy
        if qty < 1 or qty > free:
            return f"Only {max(0, free)} of {e['name']} will be free on {d.isoformat()}."
        self.res.append(dict(id=self.d["sid"], eq=item_id, roll=roll.strip().upper(), name=name.strip(),
                             date=d.isoformat(), qty=qty, st="active"))
        self.d["sid"] += 1
        self.save()

    def cancel_reservation(self, sid):
        for r in self.res:
            if r["id"] == sid:
                r["st"] = "cancelled"
        self.save()

    # alerts, analytics, history, reports --------------------------
    def alerts(self, user):
        out, admin = [], user["role"] == "admin"
        mine = [r for r in self.rec if admin or r["roll"] == user["id"]]
        for r in mine:
            nm = self.equipment(r["eq"])["name"] if self.equipment(r["eq"]) else "Deleted item"
            who = f"{r['name']} ({r['roll']}) - due {r['due']}" if admin else f"Due {r['due']}. Please return it."
            if self.is_overdue(r):
                out.append(("red", f"{nm} is overdue by {diff(r['due'])} day(s)", who))
            elif self.is_soon(r):
                out.append(("amber", f"{nm} is due {'today' if r['due'] == day() else 'on ' + r['due']}", who))
        if admin:
            for e in self.items.to_list():
                if self.low_stock(e):
                    out.append(("amber", f"Low stock: {e['name']}",
                                f"{self.available(e)} available, minimum is {e['min']}. Replace or restock."))
        return out

    def usage(self):
        """[(equipment, units borrowed)] for issued and returned records."""
        return [(e, sum(r["qty"] for r in self.rec if r["eq"] == e["id"] and r["st"] in ("issued", "returned")))
                for e in self.items.to_list()]

    def history(self, roll):
        return sorted([r for r in self.rec if r["roll"] == roll.strip().upper() and r["iss"]], key=lambda r: -r["id"])

    def inventory_rows(self):
        return [[e["id"], e["name"], e["cat"], e["loc"], e["qty"], self.available(e), self.issued_qty(e["id"]), e["dmg"], e["cond"]]
                for e in self.items.to_list()]

    def issue_rows(self):
        return [[r["id"], r["roll"], r["name"], r["eq"], (self.equipment(r["eq"]) or {}).get("name", ""), r["iss"], r["due"],
                 "overdue" if self.is_overdue(r) else r["st"]] for r in self.rec if r["iss"]]

    def return_rows(self):
        return [[r["id"], r["roll"], r["name"], (self.equipment(r["eq"]) or {}).get("name", ""), r["iss"], r["due"], r["ret"],
                 max(0, diff(r["due"], r["ret"])), r["dmg"], r["note"]] for r in self.rec if r["st"] == "returned"]


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
