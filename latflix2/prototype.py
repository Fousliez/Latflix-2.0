from __future__ import annotations

import json
import sqlite3
import sys
import webbrowser
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QComboBox, QCompleter, QDialog,
    QDialogButtonBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox,
    QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem, QTextEdit,
    QToolButton, QVBoxLayout, QWidget
)

from .config import APP_NAME, data_root

COLS = ["Jméno","Obličej","Sex","Typ","Nahota","Věk","Národnost","Tagy","Sledování",
        "Posl. kontrola","Počet výskytů","Pozn.","Stav"]
YES = ["Ano","Ne","Asi ne","Asi ano","Zjistit"]
FACE = ["Ano","Asi ano","Asi ne","Ne","Zjistit"]
STATUS = ["Aktivní","Neaktivní","Smazaná"]
TEXT = {"Jméno","Věk","Posl. kontrola"}
SELECT = {"Obličej","Sex","Typ","Nahota","Národnost","Stav"}

def s(v): return str(v or "").strip()

def age(src):
    x=s(src)
    if not x: return ""
    try: n=int(x)
    except ValueError: return x
    if 1 <= n <= 100: return str(n)
    if 1800 <= n <= date.today().year: return str(date.today().year-n)
    return x

def platform(url):
    raw=s(url)
    if not raw: return "Automaticky"
    host=urlparse(raw if "://" in raw else "https://"+raw).netloc.lower()
    for needle,name in [("instagram","Instagram"),("facebook","Facebook"),("redgifs","Redgifs"),
                        ("pornhub","Pornhub"),("linktr.ee","Linktree"),("x.com","X"),
                        ("tiktok","TikTok"),("reddit","Reddit"),("youtube","YouTube")]:
        if needle in host: return name
    host=host.removeprefix("www.").split(":")[0]
    return host.split(".")[0].capitalize() if host else "Odkaz"

class Store:
    def __init__(self):
        self.path=data_root()/"prototype"/"latflix2-prototype.db"
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.db() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS girls(
              id INTEGER PRIMARY KEY, name TEXT DEFAULT '', face TEXT DEFAULT '', sex TEXT DEFAULT '',
              typ TEXT DEFAULT '', nahota TEXT DEFAULT '', age_source TEXT DEFAULT '', nationality TEXT DEFAULT '',
              tags TEXT DEFAULT '[]', last_check TEXT DEFAULT '', note TEXT DEFAULT '', status TEXT DEFAULT '',
              locked INTEGER DEFAULT 0, favorite INTEGER DEFAULT 0, profile TEXT DEFAULT '',
              aliases TEXT DEFAULT '[]', sort_order INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS links(
              id INTEGER PRIMARY KEY, girl_id INTEGER, site TEXT DEFAULT '', url TEXT DEFAULT '',
              FOREIGN KEY(girl_id) REFERENCES girls(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS catalog(
              id INTEGER PRIMARY KEY, kind TEXT, name TEXT, color TEXT DEFAULT '#d7e9ff', ord INTEGER DEFAULT 0,
              UNIQUE(kind,name));
            CREATE TABLE IF NOT EXISTS occurrences(girl_id INTEGER PRIMARY KEY, cnt INTEGER DEFAULT 0);
            """)
            seeds={"type":["Herečka","Modelka","Amatérka"],
                   "nationality":["Česká","Americká","Britská","Německá","Francouzská","Italská","Španělská","Kanadská","Australská","Japonská","Slovenská"],
                   "tag":["Latex","Ruined","Softdomme"],
                   "platform":["Instagram","Facebook","Redgifs","Pornhub","Linktree","X","TikTok","Reddit","YouTube"]}
            for kind,names in seeds.items():
                for i,name in enumerate(names):
                    c.execute("INSERT OR IGNORE INTO catalog(kind,name,ord) VALUES(?,?,?)",(kind,name,i))
    def db(self):
        c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON"); return c
    def girls(self,fav=False):
        q="""SELECT g.*,COALESCE(o.cnt,0) occurrences,
             (SELECT COUNT(*) FROM links l WHERE l.girl_id=g.id) tracking
             FROM girls g LEFT JOIN occurrences o ON o.girl_id=g.id"""
        if fav: q+=" WHERE favorite=1"
        q+=" ORDER BY sort_order DESC,id DESC"
        with self.db() as c: return [dict(r) for r in c.execute(q)]
    def girl(self,gid):
        with self.db() as c:
            r=c.execute("""SELECT g.*,COALESCE(o.cnt,0) occurrences,
              (SELECT COUNT(*) FROM links l WHERE l.girl_id=g.id) tracking
              FROM girls g LEFT JOIN occurrences o ON o.girl_id=g.id WHERE g.id=?""",(gid,)).fetchone()
        return dict(r) if r else None
    def add(self,n):
        with self.db() as c:
            top=c.execute("SELECT COALESCE(MAX(sort_order),0) FROM girls").fetchone()[0]
            out=[]
            for i in range(n):
                cur=c.execute("INSERT INTO girls(sort_order) VALUES(?)",(top+n-i,)); out.append(cur.lastrowid)
            return out
    def set(self,gid,key,val):
        if key not in {"name","face","sex","typ","nahota","age_source","nationality","tags","last_check","note","status","locked","favorite","profile","aliases"}: return
        with self.db() as c: c.execute(f"UPDATE girls SET {key}=? WHERE id=?",(val,gid))
    def delete(self,ids):
        with self.db() as c:
            for gid in ids: c.execute("DELETE FROM girls WHERE id=? AND locked=0",(gid,))
    def cleanup(self):
        with self.db() as c:
            c.execute("""DELETE FROM girls WHERE trim(name)='' AND trim(face)='' AND trim(sex)='' AND trim(typ)=''
              AND trim(nahota)='' AND trim(age_source)='' AND trim(nationality)='' AND tags='[]'
              AND trim(last_check)='' AND trim(note)='' AND trim(status)='' AND trim(profile)=''
              AND favorite=0 AND NOT EXISTS(SELECT 1 FROM links l WHERE l.girl_id=girls.id)""")
    def links(self,gid):
        with self.db() as c: return [dict(r) for r in c.execute("SELECT * FROM links WHERE girl_id=? ORDER BY id",(gid,))]
    def all_links(self):
        with self.db() as c: return [dict(r) for r in c.execute("SELECT l.*,g.name girl FROM links l JOIN girls g ON g.id=l.girl_id ORDER BY l.id DESC")]
    def add_link(self,gid,site,url):
        if not s(url): return
        site=s(site)
        if not site or site=="Automaticky": site=platform(url)
        with self.db() as c:
            c.execute("INSERT INTO links(girl_id,site,url) VALUES(?,?,?)",(gid,site,s(url)))
            c.execute("INSERT OR IGNORE INTO catalog(kind,name,ord) VALUES('platform',?,9999)",(site,))
    def del_link(self,lid):
        with self.db() as c: c.execute("DELETE FROM links WHERE id=?",(lid,))
    def catalog(self,kind):
        with self.db() as c: return [dict(r) for r in c.execute("SELECT * FROM catalog WHERE kind=? ORDER BY ord,id",(kind,))]
    def names(self,kind): return [x["name"] for x in self.catalog(kind)]
    def replace_catalog(self,kind,rows):
        with self.db() as c:
            c.execute("DELETE FROM catalog WHERE kind=?",(kind,))
            for i,(name,color) in enumerate(rows):
                if s(name): c.execute("INSERT INTO catalog(kind,name,color,ord) VALUES(?,?,?,?)",(kind,s(name),color or "#d7e9ff",i))
    def nat_rank(self):
        with self.db() as c:
            rows=c.execute("SELECT nationality,count(*) c FROM girls WHERE trim(nationality)<>'' GROUP BY nationality ORDER BY c DESC,lower(nationality)").fetchall()
        return [r["nationality"] for r in rows]
    def link_rank(self):
        with self.db() as c:
            rows=c.execute("SELECT site,count(DISTINCT girl_id)c FROM links WHERE trim(site)<>'' GROUP BY lower(site) ORDER BY c DESC,lower(site)").fetchall()
        return {s(r["site"]).casefold():i for i,r in enumerate(rows)}

class EditLine(QLineEdit):
    enter=Signal()
    def keyPressEvent(self,e:QKeyEvent):
        if e.key()==Qt.Key_Escape: e.accept(); return
        if e.key() in (Qt.Key_Return,Qt.Key_Enter): self.enter.emit(); e.accept(); return
        super().keyPressEvent(e)

class GirlTable(QTableWidget):
    committed=Signal(int,int,str)
    selector=Signal(int,int)
    tags=Signal(int,int)
    note=Signal(int,int)
    copy_name=Signal(int,int)
    def __init__(self,parent=None):
        super().__init__(parent); self.setColumnCount(len(COLS)+2)
        self.setHorizontalHeaderLabels(["🔒","#"]+COLS); self.verticalHeader().hide()
        self.setSelectionBehavior(QAbstractItemView.SelectRows); self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers); self.setSortingEnabled(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive); self.horizontalHeader().setSectionsMovable(False)
        self.header_locked=True; self.horizontalHeader().sectionClicked.connect(self.header_click)
        self.cellDoubleClicked.connect(self.double); self.editor=None; self.erow=self.ecol=-1; self.suggestions=[]
    def header_click(self,col):
        if col==0:
            self.header_locked=not self.header_locked
            self.horizontalHeaderItem(0).setText("🔒" if self.header_locked else "🔓")
            self.horizontalHeader().setSectionsMovable(not self.header_locked)
    def locked(self,row): return bool(self.item(row,0).data(Qt.UserRole+1))
    def double(self,row,col):
        if col<2:return
        name=COLS[col-2]
        if self.locked(row):
            if name=="Jméno": self.copy_name.emit(row,col)
            return
        if name in SELECT:self.selector.emit(row,col)
        elif name=="Tagy":self.tags.emit(row,col)
        elif name=="Pozn.":self.note.emit(row,col)
        elif name in TEXT:self.edit(row,col)
    def edit(self,row,col):
        if row<0 or self.locked(row) or COLS[col-2] not in TEXT:return
        item=self.item(row,col); ed=EditLine(self.viewport())
        raw=item.data(Qt.UserRole+2); ed.setText(str(raw if raw is not None else item.text()))
        if COLS[col-2]=="Jméno" and self.suggestions:
            cp=QCompleter(self.suggestions,ed); cp.setCaseSensitivity(Qt.CaseInsensitive); cp.setFilterMode(Qt.MatchContains); ed.setCompleter(cp)
        ed.setGeometry(self.visualItemRect(item)); ed.show(); ed.setFocus(); ed.setCursorPosition(len(ed.text()))
        self.editor=ed; self.erow=row; self.ecol=col
        ed.editingFinished.connect(self.commit); ed.enter.connect(self.enter_key)
    def commit(self):
        if not self.editor:return
        ed=self.editor; row,col=self.erow,self.ecol; val=ed.text()
        self.editor=None; self.erow=self.ecol=-1; ed.hide(); ed.deleteLater()
        item=self.item(row,col); item.setData(Qt.UserRole+2,val)
        item.setText(age(val) if COLS[col-2]=="Věk" else val)
        self.committed.emit(row,col,val)
    def enter_key(self):
        row,col=self.erow,self.ecol; self.commit()
        if row+1<self.rowCount():
            self.selectRow(row+1); QTimer.singleShot(0,lambda:self.edit(row+1,col))
    def mousePressEvent(self,e:QMouseEvent):
        idx=self.indexAt(e.position().toPoint()); had=self.editor is not None
        target=(idx.row(),idx.column()) if idx.isValid() else (-1,-1)
        if had:self.commit()
        super().mousePressEvent(e)
        if had and target[0]>=0 and target[1]>=2 and not self.locked(target[0]):
            n=COLS[target[1]-2]
            if n in TEXT:QTimer.singleShot(0,lambda:self.edit(*target))
            elif n in SELECT:QTimer.singleShot(0,lambda:self.selector.emit(*target))

class TagsDialog(QDialog):
    def __init__(self,store,selected,parent=None):
        super().__init__(parent); self.setWindowTitle("Tagy"); root=QVBoxLayout(self); row=QHBoxLayout(); self.bs=[]
        for x in store.catalog("tag"):
            b=QPushButton(x["name"],self); b.setCheckable(True); b.setChecked(x["name"] in selected)
            b.setStyleSheet(f"QPushButton{{background:{x['color']};padding:7px;border:1px solid #999}} QPushButton:checked{{border:2px solid #2767a5}}")
            row.addWidget(b); self.bs.append(b)
        row.addStretch(1); root.addLayout(row); root.addStretch(1)
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel,self); bb.button(QDialogButtonBox.Save).setText("Uložit"); bb.button(QDialogButtonBox.Cancel).setText("Zrušit")
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); root.addWidget(bb)
    def values(self):return [b.text() for b in self.bs if b.isChecked()]

class LinksDialog(QDialog):
    def __init__(self,store,gid,parent=None):
        super().__init__(parent); self.store=store; self.gid=gid; self.setWindowTitle("Odkazy"); self.resize(720,560)
        self.root=QVBoxLayout(self); self.saved=QVBoxLayout(); self.root.addLayout(self.saved); self.root.addWidget(QLabel("Přidat odkazy:",self))
        self.new=QVBoxLayout(); self.root.addLayout(self.new); self.rows=[]
        for _ in range(10):self.addrow()
        add=QPushButton("+ Přidat řádek",self); add.clicked.connect(self.addrow); self.root.addWidget(add,0,Qt.AlignLeft)
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel,self); bb.accepted.connect(self.save); bb.rejected.connect(self.reject); self.root.addWidget(bb); self.refresh()
    def combo(self):
        c=QComboBox(self); c.setEditable(True); c.addItem("Automaticky"); c.addItems(self.store.names("platform")); return c
    def refresh(self):
        while self.saved.count():
            it=self.saved.takeAt(0)
            if it.widget():it.widget().deleteLater()
        for l in self.store.links(self.gid):
            w=QWidget(self); h=QHBoxLayout(w); h.setContentsMargins(0,0,0,0)
            name=QPushButton(l["site"],w); name.clicked.connect(lambda _,u=l["url"]:QMessageBox.information(self,"Adresa",u))
            delete=QPushButton("×",w); delete.setFixedWidth(30); delete.clicked.connect(lambda _,i=l["id"]:self.remove(i))
            h.addWidget(name,1); h.addWidget(delete); self.saved.addWidget(w)
    def remove(self,lid):
        if QMessageBox.question(self,"Smazat","Chcete odkaz smazat?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:self.store.del_link(lid);self.refresh()
    def addrow(self):
        w=QWidget(self); h=QHBoxLayout(w); h.setContentsMargins(0,0,0,0); c=self.combo(); u=QLineEdit(w); u.setPlaceholderText("https://…")
        u.textChanged.connect(lambda t,cc=c:cc.setCurrentText(platform(t)) if t else cc.setCurrentText("Automaticky"))
        h.addWidget(c,1); h.addWidget(u,3); self.new.addWidget(w); self.rows.append((c,u))
    def save(self):
        for c,u in self.rows:
            if s(u.text()):self.store.add_link(self.gid,c.currentText(),u.text())
        self.accept()

class BulkLinks(QDialog):
    def __init__(self,store,girls,parent=None):
        super().__init__(parent); self.store=store; self.setWindowTitle("Hromadně přidat odkazy"); self.resize(850,420)
        root=QVBoxLayout(self); self.t=QTableWidget(len(girls),3,self); self.t.setHorizontalHeaderLabels(["Herečka","Zdroj / platforma","URL"]); self.t.horizontalHeader().setStretchLastSection(True); self.rows=[]
        for r,g in enumerate(girls):
            it=QTableWidgetItem(g["name"]); it.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable); self.t.setItem(r,0,it)
            c=QComboBox(self.t); c.setEditable(True); c.addItem("Automaticky"); c.addItems(store.names("platform")); u=QLineEdit(self.t)
            u.textChanged.connect(lambda t,cc=c:cc.setCurrentText(platform(t)) if t else cc.setCurrentText("Automaticky"))
            self.t.setCellWidget(r,1,c); self.t.setCellWidget(r,2,u); self.rows.append((g["id"],c,u))
        root.addWidget(self.t); bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel,self); bb.accepted.connect(self.save); bb.rejected.connect(self.reject); root.addWidget(bb)
    def save(self):
        for gid,c,u in self.rows:
            if s(u.text()):self.store.add_link(gid,c.currentText(),u.text())
        self.accept()

class CatalogPage(QWidget):
    changed=Signal()
    def __init__(self,store,kind,color=False,parent=None):
        super().__init__(parent); self.store=store; self.kind=kind; self.color=color; root=QVBoxLayout(self)
        h=QHBoxLayout(); a=QPushButton("+ Přidat",self); d=QPushButton("− Smazat",self); h.addWidget(a);h.addWidget(d);h.addStretch(1);root.addLayout(h)
        self.t=QTableWidget(self); self.t.setColumnCount(2 if color else 1); self.t.setHorizontalHeaderLabels(["Název","Barva"] if color else ["Název"]); self.t.horizontalHeader().setStretchLastSection(True);root.addWidget(self.t)
        a.clicked.connect(self.add);d.clicked.connect(self.delete);self.t.itemChanged.connect(self.save);self.reload()
    def reload(self):
        self.t.blockSignals(True); rows=self.store.catalog(self.kind);self.t.setRowCount(len(rows))
        for r,x in enumerate(rows):
            self.t.setItem(r,0,QTableWidgetItem(x["name"]))
            if self.color:self.t.setItem(r,1,QTableWidgetItem(x["color"]))
        self.t.blockSignals(False)
    def values(self):
        out=[]
        for r in range(self.t.rowCount()):
            n=self.t.item(r,0).text() if self.t.item(r,0) else ""; c=self.t.item(r,1).text() if self.color and self.t.item(r,1) else "#d7e9ff";out.append((n,c))
        return out
    def save(self,*_):self.store.replace_catalog(self.kind,self.values());self.changed.emit()
    def add(self):self.t.insertRow(0);self.t.setItem(0,0,QTableWidgetItem(""))
    def delete(self):
        for r in sorted({i.row() for i in self.t.selectedIndexes()},reverse=True):self.t.removeRow(r)
        self.save()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.store=Store(); self.category="Girls"; self.rows=[]; self.visible=[]; self.current=None; self.filters={}; self.rowlevel=1
        self.setWindowTitle(APP_NAME+" – PROTOTYP"); self.resize(1450,820); self._ui(); self._style(); self.load("Girls")
    def _ui(self):
        for x in ["Soubor","Úpravy","Nástroje","Zobrazení","Nastavení","Nápověda"]:self.menuBar().addMenu(x)
        rootw=QWidget(self); root=QHBoxLayout(rootw); root.setContentsMargins(4,4,4,4)
        side=QWidget(rootw);side.setFixedWidth(150);sl=QVBoxLayout(side);self.sb={}
        for n in ["Přehled","Girls","Oblíbené","Odkazy","Videa","Super","Studia"]:
            b=QPushButton(n,side);b.setCheckable(True);b.clicked.connect(lambda _,x=n:self.load(x));sl.addWidget(b);self.sb[n]=b
        sl.addStretch(1)
        for n in ["Stavy","Kvality","Tagy","Typy","Národnosti"]:
            b=QPushButton(n,side);b.setCheckable(True);b.clicked.connect(lambda _,x=n:self.load(x));sl.addWidget(b);self.sb[n]=b
        root.addWidget(side);self.stack=QStackedWidget(rootw);root.addWidget(self.stack,1)
        page=QWidget(self.stack);pv=QVBoxLayout(page);pv.setContentsMargins(0,0,0,0);pv.setSpacing(5)
        self.detail=QFrame(page);self.detail.setFixedHeight(136);dh=QHBoxLayout(self.detail)
        self.photo=QPushButton("FOTKA",self.detail);self.photo.setFixedSize(76,118);self.photo.clicked.connect(self.photo_choose);dh.addWidget(self.photo)
        mid=QWidget(self.detail);mv=QVBoxLayout(mid);head=QHBoxLayout();self.dname=QLabel("Vyber herečku",mid);self.dname.setObjectName("dname");self.fav=QPushButton("☆ Oblíbené",mid);self.fav.setCheckable(True);self.fav.clicked.connect(self.toggle_fav);head.addWidget(self.dname);head.addWidget(self.fav);head.addStretch(1);mv.addLayout(head)
        meta=QHBoxLayout();self.dage=QLabel("Věk: —",mid);self.docc=QLabel("Počet výskytů: 0",mid);meta.addWidget(self.dage);meta.addWidget(self.docc);meta.addStretch(1);mv.addLayout(meta)
        self.chips=QHBoxLayout();mv.addLayout(self.chips);mv.addStretch(1);dh.addWidget(mid,1)
        av=QVBoxLayout();self.links=QPushButton("Odkazy",self.detail);self.detailb=QPushButton("Detail",self.detail);self.showlinks=QPushButton("Zobrazit odkazy",self.detail);self.links.clicked.connect(self.open_links);self.detailb.clicked.connect(self.open_detail);self.showlinks.clicked.connect(self.show_links);av.addWidget(self.links);av.addWidget(self.detailb);av.addWidget(self.showlinks);av.addStretch(1);dh.addLayout(av);pv.addWidget(self.detail)
        self.toolbar=QWidget(page);th=QHBoxLayout(self.toolbar);th.setContentsMargins(0,0,0,0)
        add=QToolButton(self.toolbar);add.setText("Přidat");add.setPopupMode(QToolButton.MenuButtonPopup);am=QMenu(add);am.addAction("Přidat 5 řádků",lambda:self.add(5));am.addAction("Přidat 10 řádků",lambda:self.add(10));add.setMenu(am);add.clicked.connect(lambda:self.add(1));th.addWidget(add)
        delete=QPushButton("Smazat",self.toolbar);delete.clicked.connect(self.delete);th.addWidget(delete)
        bulk=QToolButton(self.toolbar);bulk.setText("Hromadné akce");bulk.setPopupMode(QToolButton.InstantPopup);bm=QMenu(bulk);bm.addAction("Přidat do oblíbených",lambda:self.bulkfav(True));bm.addAction("Odebrat z oblíbených",lambda:self.bulkfav(False));bm.addSeparator();bm.addAction("Hromadně přidat odkazy",self.bulklinks);bulk.setMenu(bm);th.addWidget(bulk)
        self.search=QLineEdit(self.toolbar);self.search.setPlaceholderText("Hledat…");self.search.setFixedWidth(205);self.search.textChanged.connect(self.apply);th.addWidget(self.search)
        trash=QToolButton(self.toolbar);trash.setText("🗑");trash.clicked.connect(self.search.clear);th.addWidget(trash)
        self.fb={}
        for n in ["Národnost","Typ","Stav","Sex","Nahota","Obličej","Profilovka"]:
            b=QToolButton(self.toolbar);b.setText(n);b.setPopupMode(QToolButton.InstantPopup);self.fb[n]=b;th.addWidget(b)
        th.addStretch(1);clear=QPushButton("Vyčistit",self.toolbar);clear.clicked.connect(self.clear);th.addWidget(clear);pv.addWidget(self.toolbar)
        self.table=GirlTable(page);self.table.selector.connect(self.selector);self.table.tags.connect(self.tags);self.table.note.connect(self.note);self.table.copy_name.connect(self.copy);self.table.committed.connect(self.commit);self.table.cellClicked.connect(self.cellclick);self.table.selectionModel().selectionChanged.connect(self.selected);pv.addWidget(self.table,1)
        self.stack.addWidget(page);self.girlpage=page
        self.placeholder=QLabel("Tato sekce je v prototypu zatím pouze připravená.",self.stack);self.placeholder.setAlignment(Qt.AlignCenter);self.stack.addWidget(self.placeholder)
        self.catalogs={"Typy":CatalogPage(self.store,"type"),"Národnosti":CatalogPage(self.store,"nationality"),"Tagy":CatalogPage(self.store,"tag",True)}
        for p in self.catalogs.values():p.changed.connect(lambda:self.load(self.category) if self.category in {"Girls","Oblíbené"} else None);self.stack.addWidget(p)
        self.linkpage=QWidget(self.stack);lv=QVBoxLayout(self.linkpage);self.linktitle=QLabel("Odkazy",self.linkpage);lv.addWidget(self.linktitle);self.linktable=QTableWidget(self.linkpage);self.linktable.setColumnCount(3);self.linktable.setHorizontalHeaderLabels(["Herečka","Zdroj","URL"]);self.linktable.horizontalHeader().setStretchLastSection(True);lv.addWidget(self.linktable);self.stack.addWidget(self.linkpage)
        self.setCentralWidget(rootw);self.count=QLabel(self);self.avg=QLabel(self);self.statusBar().addWidget(self.count);self.statusBar().addWidget(self.avg,1)
    def _style(self):
        self.setStyleSheet("""QWidget{font-size:13px;background:#f1f1f1;color:#222} QPushButton,QToolButton{min-height:27px;padding:2px 7px;border:1px solid #aaa;border-radius:3px;background:#fafafa} QPushButton:hover,QToolButton:hover{background:#e5f0fb} QFrame{background:white;border:1px solid #bbb;border-radius:4px} QLabel#dname{font-size:22px;font-weight:700;background:white;border:0} QTableWidget{background:white;gridline-color:#d5d5d5;selection-background-color:#dcecff;selection-color:#111} QHeaderView::section{background:#ececec;border:0;border-right:1px solid #ccc;border-bottom:1px solid #aaa;padding:4px} QLineEdit,QComboBox,QTextEdit{background:white;border:1px solid #aaa;padding:3px}""")
    def load(self,n):
        if n!=self.category:self.store.cleanup()
        self.category=n
        for k,b in self.sb.items():b.setChecked(k==n)
        if n in {"Girls","Oblíbené"}:self.stack.setCurrentWidget(self.girlpage);self.reload()
        elif n=="Odkazy":self.stack.setCurrentWidget(self.linkpage);self.reload_links()
        elif n in self.catalogs:self.catalogs[n].reload();self.stack.setCurrentWidget(self.catalogs[n])
        else:self.stack.setCurrentWidget(self.placeholder)
        self.setWindowTitle(f"{APP_NAME} – PROTOTYP – {n}")
    def reload(self,preserve=None):
        self.rows=self.store.girls(self.category=="Oblíbené"); self.rebuild_filters();self.autocomplete();self.apply(preserve=preserve or self.current)
    def autocomplete(self):
        vals=[]
        for g in sorted(self.store.girls(self.category=="Oblíbené"),key=lambda x:(-int(x["occurrences"]),s(x["name"]).casefold())):
            if s(g["name"]):vals.append(g["name"])
            vals+=json.loads(g["aliases"] or "[]")
        cp=QCompleter(vals,self.search);cp.setCaseSensitivity(Qt.CaseInsensitive);cp.setFilterMode(Qt.MatchContains);cp.popup().setStyleSheet("QListView{font-size:15px} QListView::item{height:30px} QListView::item:hover{background:#2877c7;color:white}");self.search.setCompleter(cp);self.table.suggestions=vals
    def match(self,g):
        for n,w in self.filters.items():
            if not w:continue
            if n=="Profilovka":v="Ano" if s(g["profile"]) else "Ne"
            else:v=s(g[{"Národnost":"nationality","Typ":"typ","Stav":"status","Sex":"sex","Nahota":"nahota","Obličej":"face"}[n]])
            if v!=w:return False
        return True
    def apply(self,*_,preserve=None):
        q=s(self.search.text()).casefold();out=[]
        for g in self.rows:
            if not self.match(g):continue
            vals=[g["name"],g["face"],g["sex"],g["typ"],g["nahota"],age(g["age_source"]),g["nationality"]," ".join(json.loads(g["tags"] or "[]")),g["last_check"],g["note"],g["status"]]+json.loads(g["aliases"] or "[]")
            if q and not any(q in s(v).casefold() for v in vals):continue
            out.append(g)
        self.visible=out;self.fill(preserve);self.status()
    def fill(self,preserve=None):
        self.table.setSortingEnabled(False);self.table.setRowCount(len(self.visible))
        for r,g in enumerate(self.visible):
            lk=QTableWidgetItem("🔒" if g["locked"] else "🔓");lk.setData(Qt.UserRole,g["id"]);lk.setData(Qt.UserRole+1,int(g["locked"]));lk.setTextAlignment(Qt.AlignCenter);self.table.setItem(r,0,lk)
            num=QTableWidgetItem(str(r+1));num.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable);self.table.setItem(r,1,num)
            vals=[g["name"],g["face"],g["sex"],g["typ"],g["nahota"],age(g["age_source"]),g["nationality"],", ".join(json.loads(g["tags"] or "[]")),g["tracking"],g["last_check"],g["occurrences"],g["note"],g["status"]]
            for c,(n,v) in enumerate(zip(COLS,vals),2):
                it=QTableWidgetItem(str(v));it.setData(Qt.UserRole,g["id"])
                if n=="Věk":it.setData(Qt.UserRole+2,g["age_source"])
                it.setBackground(QColor("#edf6ff" if r%2==0 else "#effbef"));self.table.setItem(r,c,it)
        self.table.setSortingEnabled(True);self.table.setColumnWidth(0,42);self.table.setColumnWidth(1,42);self.table.setColumnWidth(2,190)
        target=next((r for r,g in enumerate(self.visible) if g["id"]==preserve),0 if self.visible else None)
        if target is not None:self.table.selectRow(target)
    def selected_rows(self):
        ids=[]
        for i in self.table.selectionModel().selectedRows():
            it=self.table.item(i.row(),0)
            if it:ids.append(it.data(Qt.UserRole))
        by={g["id"]:g for g in self.rows};return [by[i] for i in ids if i in by]
    def selected(self,*_):
        gs=self.selected_rows();g=gs[0] if gs else None;self.current=g["id"] if g else None;self.show(g)
    def show(self,g):
        while self.chips.count():
            it=self.chips.takeAt(0)
            if it.widget():it.widget().deleteLater()
        if not g:self.dname.setText("Vyber herečku");return
        g=self.store.girl(g["id"]);self.dname.setText(g["name"] or "(bez jména)");self.dage.setText("Věk: "+(age(g["age_source"]) or "—"));self.docc.setText(f"Počet výskytů: {g['occurrences']}");self.fav.setChecked(bool(g["favorite"]));self.fav.setText("★ V oblíbených" if g["favorite"] else "☆ Oblíbené")
        p=s(g["profile"])
        if p and Path(p).exists():
            pm=QPixmap(p);self.photo.setIcon(pm);self.photo.setText("")
        else:self.photo.setIcon(QPixmap());self.photo.setText("FOTKA")
        groups=defaultdict(list)
        for l in self.store.links(g["id"]):groups[l["site"] or "Odkaz"].append(l["url"])
        rank=self.store.link_rank()
        for site,urls in sorted(groups.items(),key=lambda x:(rank.get(x[0].casefold(),9999),x[0].casefold())):
            b=QPushButton(site+(f" ({len(urls)})" if len(urls)>1 else ""),self.detail);b.clicked.connect(lambda _,us=list(urls):[webbrowser.open(u) for u in us]);self.chips.addWidget(b)
        self.chips.addStretch(1)
    def rebuild_filters(self):
        data={"Typ":self.store.names("type"),"Stav":STATUS,"Sex":YES,"Nahota":YES,"Obličej":FACE,"Profilovka":["Ano","Ne"]}
        alln=self.store.names("nationality");rank=self.store.nat_rank();data["Národnost"]=rank+[x for x in alln if x not in rank]
        for n,b in self.fb.items():
            m=QMenu(b);m.addAction("Vše",lambda _,x=n:self.setfilter(x,""));vals=data[n]
            if n=="Národnost" and len(vals)>10:
                for v in vals[:10]:m.addAction(v,lambda _,x=n,y=v:self.setfilter(x,y))
                m.addSeparator();more=m.addMenu("Další")
                for v in vals[10:]:more.addAction(v,lambda _,x=n,y=v:self.setfilter(x,y))
            else:
                for v in vals:m.addAction(v,lambda _,x=n,y=v:self.setfilter(x,y))
            b.setMenu(m);b.setText(n+(f": {self.filters[n]}" if self.filters.get(n) else ""))
    def setfilter(self,n,v):self.filters[n]=v;self.rebuild_filters();self.apply()
    def clear(self):self.filters.clear();self.search.blockSignals(True);self.search.clear();self.search.blockSignals(False);self.rebuild_filters();self.apply()
    def add(self,n):
        ids=self.store.add(n)
        if self.category=="Oblíbené":
            for gid in ids:self.store.set(gid,"favorite",1)
        self.reload(ids[0] if ids else None)
        if ids:
            r=next((i for i,g in enumerate(self.visible) if g["id"]==ids[0]),None)
            if r is not None:QTimer.singleShot(0,lambda:self.table.edit(r,2))
    def delete(self):
        gs=[g for g in self.selected_rows() if not g["locked"]]
        if gs and QMessageBox.question(self,"Smazat",f"Smazat {len(gs)} řádků?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:self.store.delete([g["id"] for g in gs]);self.reload()
    def cellclick(self,r,c):
        if c==0 and r<len(self.visible):
            g=self.visible[r];self.store.set(g["id"],"locked",0 if g["locked"] else 1);self.reload(g["id"])
    def commit(self,r,c,v):
        if r>=len(self.visible):return
        g=self.visible[r];field={"Jméno":"name","Věk":"age_source","Posl. kontrola":"last_check"}.get(COLS[c-2])
        if field:self.store.set(g["id"],field,v);g[field]=v;self.current=g["id"];self.show(g)
    def selector(self,r,c):
        if r>=len(self.visible):return
        g=self.visible[r];n=COLS[c-2];opts={"Obličej":FACE,"Sex":YES,"Typ":self.store.names("type"),"Nahota":YES,"Národnost":self.store.names("nationality"),"Stav":STATUS}[n]
        m=QMenu(self)
        for v in opts:m.addAction(v,lambda _,x=v,nn=n,gid=g["id"]:self.selset(gid,nn,x))
        m.exec(self.table.viewport().mapToGlobal(self.table.visualItemRect(self.table.item(r,c)).bottomLeft()))
    def selset(self,gid,n,v):
        self.store.set(gid,{"Obličej":"face","Sex":"sex","Typ":"typ","Nahota":"nahota","Národnost":"nationality","Stav":"status"}[n],v);self.reload(gid)
    def tags(self,r,c):
        g=self.visible[r];d=TagsDialog(self.store,json.loads(g["tags"] or "[]"),self)
        if d.exec()==QDialog.Accepted:self.store.set(g["id"],"tags",json.dumps(d.values(),ensure_ascii=False));self.reload(g["id"])
    def note(self,r,c):
        g=self.visible[r];d=QDialog(self);d.setWindowTitle("Poznámka");v=QVBoxLayout(d);e=QTextEdit(d);e.setPlainText(g["note"]);v.addWidget(e);bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel,d);bb.accepted.connect(d.accept);bb.rejected.connect(d.reject);v.addWidget(bb)
        if d.exec()==QDialog.Accepted:self.store.set(g["id"],"note",e.toPlainText());self.reload(g["id"])
    def copy(self,r,c):QApplication.clipboard().setText(self.table.item(r,c).text());self.statusBar().showMessage("Zkopírováno",1200)
    def bulkfav(self,val):
        gs=self.selected_rows()
        if not gs:return
        if not val and QMessageBox.question(self,"Oblíbené","Odebrat vybrané z oblíbených?",QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        for g in gs:self.store.set(g["id"],"favorite",1 if val else 0)
        self.reload()
    def bulklinks(self):
        gs=self.selected_rows()
        if gs:
            d=BulkLinks(self.store,gs,self)
            if d.exec()==QDialog.Accepted:self.reload(self.current)
    def open_links(self):
        if self.current:
            d=LinksDialog(self.store,self.current,self)
            if d.exec()==QDialog.Accepted:self.reload(self.current)
    def open_detail(self):
        if not self.current:return
        g=self.store.girl(self.current);d=QDialog(self);d.setWindowTitle("Detail");f=QFormLayout(d)
        fields={"Jméno":QLineEdit(g["name"],d),"Aliasy":QLineEdit(", ".join(json.loads(g["aliases"] or "[]")),d),"Věk / rok narození":QLineEdit(g["age_source"],d),"Posl. kontrola":QLineEdit(g["last_check"],d)}
        for n,w in fields.items():f.addRow(n,w)
        nt=QTextEdit(d);nt.setPlainText(g["note"]);f.addRow("Poznámka",nt);bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel,d);bb.accepted.connect(d.accept);bb.rejected.connect(d.reject);f.addRow(bb)
        if d.exec()==QDialog.Accepted:
            self.store.set(g["id"],"name",fields["Jméno"].text());self.store.set(g["id"],"aliases",json.dumps([x.strip() for x in fields["Aliasy"].text().split(",") if x.strip()],ensure_ascii=False));self.store.set(g["id"],"age_source",fields["Věk / rok narození"].text());self.store.set(g["id"],"last_check",fields["Posl. kontrola"].text());self.store.set(g["id"],"note",nt.toPlainText());self.reload(g["id"])
    def show_links(self):
        if self.current:self.linkfilter=self.current;self.load("Odkazy")
    def reload_links(self):
        rows=self.store.all_links();gid=getattr(self,"linkfilter",None)
        if gid:rows=[x for x in rows if x["girl_id"]==gid];g=self.store.girl(gid);self.linktitle.setText("Odkazy – "+(g["name"] if g else ""))
        else:self.linktitle.setText("Odkazy")
        self.linktable.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,v in enumerate([x["girl"],x["site"],x["url"]]):self.linktable.setItem(r,c,QTableWidgetItem(v))
    def toggle_fav(self):
        if self.current:
            g=self.store.girl(self.current);self.store.set(g["id"],"favorite",0 if g["favorite"] else 1);self.reload(g["id"])
    def photo_choose(self):
        if not self.current:return
        p,_=QFileDialog.getOpenFileName(self,"Vybrat profilovku",str(Path.home()/"Plocha"),"Obrázky (*.png *.jpg *.jpeg *.webp *.bmp)")
        if p:self.store.set(self.current,"profile",p);self.reload(self.current)
    def status(self):
        self.count.setText(f"Záznamů: {len(self.visible)} / {len(self.rows)}")
        arr=[]
        for g in self.rows:
            if self.match(g):
                a=age(g["age_source"])
                if a.isdigit() and 1<=int(a)<=100:arr.append(int(a))
        self.avg.setText(f"Průměrný věk: {sum(arr)/len(arr):.1f}" if arr else "Průměrný věk: —")
    def closeEvent(self,e):self.store.cleanup();super().closeEvent(e)

def run():
    app=QApplication(sys.argv);app.setApplicationName(APP_NAME);app.setOrganizationName("Latflix")
    w=MainWindow();w.showMaximized();return app.exec()
