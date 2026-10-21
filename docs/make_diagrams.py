#!/usr/bin/env python3
"""Схемы пояснительной записки: PNG для Word и исходники draw.io."""

import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(OUT, "img")
DRW = os.path.join(OUT, "diagrams")
os.makedirs(IMG, exist_ok=True)
os.makedirs(DRW, exist_ok=True)

FONT_R = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
FONT_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


class Diagram:
    def __init__(self, filename, width, height, title=None):
        self.filename = filename
        self.w = width
        self.h = height
        self.nodes = []
        self.edges = []
        self.lines = []

    def box(self, nid, text, x, y, w, h, kind="process"):
        self.nodes.append({"id": nid, "text": text, "x": x, "y": y, "w": w, "h": h, "kind": kind})
        self.w = max(self.w, x + w + 36)
        self.h = max(self.h, y + h + 36)
        return nid

    def link(self, a, b, label="", start="s", end="n", arrow=True, route=None):
        self.edges.append({
            "a": a, "b": b, "label": label, "start": start, "end": end,
            "arrow": arrow, "route": route,
        })

    def node(self, nid):
        for n in self.nodes:
            if n["id"] == nid:
                return n
        raise KeyError(nid)

    def save(self):
        for e in self.edges:
            for x, y in (e["route"] or []):
                self.w = max(self.w, x + 28)
                self.h = max(self.h, y + 28)
        self._png(os.path.join(IMG, self.filename + ".png"))
        self._drawio(os.path.join(DRW, self.filename + ".drawio"))
        return os.path.join(IMG, self.filename + ".png")

    def _port(self, n, side):
        x, y, w, h = n["x"], n["y"], n["w"], n["h"]
        return {
            "n": (x + w / 2, y),
            "s": (x + w / 2, y + h),
            "e": (x + w, y + h / 2),
            "w": (x, y + h / 2),
        }[side]

    def _route(self, e):
        if e["route"]:
            return e["route"]
        a = self._port(self.node(e["a"]), e["start"])
        b = self._port(self.node(e["b"]), e["end"])
        if e["start"] == "s" and e["end"] == "n":
            if abs(a[0] - b[0]) < 3:
                return [a, b]
            mid = (a[1] + b[1]) / 2
            return [a, (a[0], mid), (b[0], mid), b]
        if e["start"] == "e" and e["end"] == "w":
            if abs(a[1] - b[1]) < 3:
                return [a, b]
            mid = (a[0] + b[0]) / 2
            return [a, (mid, a[1]), (mid, b[1]), b]
        if e["start"] == "e" and e["end"] == "n":
            return [a, (b[0], a[1]), b]
        if e["start"] == "e" and e["end"] == "s":
            return [a, (b[0], a[1]), b]
        if e["start"] == "w" and e["end"] == "w":
            x = min(a[0], b[0]) - 42
            return [a, (x, a[1]), (x, b[1]), b]
        if e["start"] == "e" and e["end"] == "e":
            x = max(a[0], b[0]) + 36
            return [a, (x, a[1]), (x, b[1]), b]
        if e["start"] == "w" and e["end"] == "e":
            if abs(a[1] - b[1]) < 6:
                return [a, b]
            mid = (a[0] + b[0]) / 2
            return [a, (mid, a[1]), (mid, b[1]), b]
        if e["start"] == "s" and e["end"] == "w":
            return [a, (a[0], b[1]), b]
        if e["start"] == "w" and e["end"] == "n":
            return [a, (b[0], a[1]), b]
        if e["start"] == "n" and e["end"] == "n":
            y = min(a[1], b[1]) - 28
            return [a, (a[0], y), (b[0], y), b]
        return [a, b]

    def _png(self, path):
        im = Image.new("RGB", (int(self.w), int(self.h)), "white")
        dr = ImageDraw.Draw(im)
        for e in self.edges:
            pts = self._route(e)
            dr.line(pts, fill="black", width=2)
            if e["arrow"] and len(pts) >= 2:
                _arrow(dr, pts[-2], pts[-1])
            if e["label"]:
                x = pts[0][0] + 8
                y = pts[0][1] - 22
                if e["start"] == "e":
                    x = pts[0][0] + 6
                    y = pts[0][1] - 26
                dr.text((x, y), e["label"], fill="black", font=font(22, True))
        for n in self.nodes:
            _shape(dr, n)
            _text(dr, n)
        im.save(path, "PNG")

    def _drawio(self, path):
        cells = [
            '<mxCell id="0"/>',
            '<mxCell id="1" parent="0"/>',
        ]
        for i, n in enumerate(self.nodes, start=2):
            style = _dio_style(n["kind"])
            text = _xml(n["text"]).replace("\n", "&#10;")
            cells.append(
                f'<mxCell id="{n["id"]}" value="{text}" style="{style}" vertex="1" parent="1">'
                f'<mxGeometry x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" as="geometry"/>'
                f"</mxCell>"
            )
        eid = 1000
        for e in self.edges:
            pts = self._route(e)
            label = _xml(e["label"])
            arr = "block" if e["arrow"] else "none"
            style = (
                "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=%s;"
                "fontFamily=Times New Roman;fontSize=14;labelBackgroundColor=#ffffff;"
            ) % arr
            extra = ""
            if len(pts) > 2:
                bits = []
                for x, y in pts[1:-1]:
                    bits.append(f'<mxPoint x="{x:.0f}" y="{y:.0f}"/>')
                extra = '<Array as="points">' + "".join(bits) + "</Array>"
            cells.append(
                f'<mxCell id="e{eid}" value="{label}" style="{style}" edge="1" parent="1" '
                f'source="{e["a"]}" target="{e["b"]}">'
                f'<mxGeometry relative="1" as="geometry">{extra}</mxGeometry></mxCell>'
            )
            eid += 1
        page_w = max(827, int(self.w) + 40)
        page_h = max(1169, int(self.h) + 40)
        xml = (
            '<mxfile host="app.diagrams.net" type="device">\n'
            '  <diagram name="Схема" id="page1">\n'
            f'    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" '
            f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{page_w}" '
            f'pageHeight="{page_h}" math="0" shadow="0">\n'
            "      <root>\n        "
            + "\n        ".join(cells)
            + "\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n"
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(xml)


def _xml(text):
    amp = chr(38)
    raw = text or ""
    return (
        raw.replace(amp, amp + "amp;")
        .replace(chr(60), amp + "lt;")
        .replace(chr(62), amp + "gt;")
        .replace(chr(34), amp + "quot;")
    )


def _arrow(dr, p1, p2, size=14):
    import math
    x1, y1 = p1
    x2, y2 = p2
    ang = math.atan2(y2 - y1, x2 - x1)
    left = (x2 - size * math.cos(ang - 0.4), y2 - size * math.sin(ang - 0.4))
    right = (x2 - size * math.cos(ang + 0.4), y2 - size * math.sin(ang + 0.4))
    dr.polygon([(x2, y2), left, right], fill="black")


def _wrap(dr, text, fnt, max_w):
    lines = []
    for part in text.split("\n"):
        words = part.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for word in words[1:]:
            trial = cur + " " + word
            if dr.textlength(trial, font=fnt) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def _text(dr, n):
    kind = n["kind"]
    pad = 18 if kind != "decision" else 36
    max_w = n["w"] - pad * 2
    if kind == "decision":
        max_w = n["w"] * 0.52
    fnt = font(24 if kind != "decision" else 22, bold=(kind in ("term", "header")))
    lines = _wrap(dr, n["text"], fnt, max_w)
    line_h = 28
    total = line_h * len(lines)
    y = n["y"] + (n["h"] - total) / 2
    if kind == "store":
        y += 8
    for line in lines:
        tw = dr.textlength(line, font=fnt)
        x = n["x"] + (n["w"] - tw) / 2
        dr.text((x, y), line, fill="black", font=fnt)
        y += line_h


def _shape(dr, n):
    x, y, w, h = n["x"], n["y"], n["w"], n["h"]
    kind = n["kind"]
    box = [x, y, x + w, y + h]
    if kind in ("process", "header", "card"):
        dr.rectangle(box, fill="white", outline="black", width=2)
    elif kind == "predef":
        dr.rectangle(box, fill="white", outline="black", width=2)
        dr.line([(x + 14, y), (x + 14, y + h)], fill="black", width=2)
        dr.line([(x + w - 14, y), (x + w - 14, y + h)], fill="black", width=2)
    elif kind == "term":
        dr.rounded_rectangle(box, radius=h / 2, fill="white", outline="black", width=2)
    elif kind == "decision":
        cx, cy = x + w / 2, y + h / 2
        dr.polygon([(cx, y), (x + w, cy), (cx, y + h), (x, cy)], fill="white", outline="black")
        dr.line([(cx, y), (x + w, cy), (cx, y + h), (x, cy), (cx, y)], fill="black", width=2)
    elif kind == "data":
        skew = 22
        dr.polygon(
            [(x + skew, y), (x + w, y), (x + w - skew, y + h), (x, y + h)],
            fill="white", outline="black",
        )
        dr.line([(x + skew, y), (x + w, y), (x + w - skew, y + h), (x, y + h), (x + skew, y)], fill="black", width=2)
    elif kind == "input":
        skew = 22
        dr.polygon([(x, y + skew), (x + w, y), (x + w, y + h), (x, y + h)], fill="white", outline="black")
        dr.line([(x, y + skew), (x + w, y), (x + w, y + h), (x, y + h), (x, y + skew)], fill="black", width=2)
    elif kind == "display":
        dr.rounded_rectangle(box, radius=18, fill="white", outline="black", width=2)
        inset = 16
        dr.arc([x - 10, y, x + inset, y + h], 270, 90, fill="black", width=2)
    elif kind == "store":
        ry = 14
        dr.ellipse([x, y, x + w, y + ry * 2], fill="white", outline="black", width=2)
        dr.rectangle([x, y + ry, x + w, y + h - ry], fill="white", outline="white")
        dr.line([(x, y + ry), (x, y + h - ry)], fill="black", width=2)
        dr.line([(x + w, y + ry), (x + w, y + h - ry)], fill="black", width=2)
        dr.arc([x, y + h - ry * 2, x + w, y + h], 0, 180, fill="black", width=2)
        dr.arc([x, y, x + w, y + ry * 2], 180, 360, fill="black", width=2)
    elif kind == "document":
        dr.rectangle([x, y, x + w, y + h - 16], fill="white", outline="black", width=2)
        dr.polygon([(x, y + h - 16), (x, y + h - 4), (x + w / 2, y + h - 18), (x + w, y + h), (x + w, y + h - 16)], fill="white")
        dr.line([(x, y), (x + w, y), (x + w, y + h - 16)], fill="black", width=2)
        dr.line([(x, y), (x, y + h - 8)], fill="black", width=2)
        dr.arc([x, y + h - 28, x + w / 2, y + h], 0, 180, fill="black", width=2)
        dr.arc([x + w / 2, y + h - 28, x + w, y + h], 180, 360, fill="black", width=2)
    else:
        dr.rectangle(box, fill="white", outline="black", width=2)


def _dio_style(kind):
    base = "whiteSpace=wrap;html=1;fontFamily=Times New Roman;fontSize=14;strokeColor=#000000;fillColor=#ffffff;strokeWidth=1.5;"
    return {
        "process": base,
        "header": base + "fontStyle=1;",
        "card": base,
        "predef": base + "shape=process;",
        "term": base + "rounded=1;arcSize=50;",
        "decision": base + "rhombus;",
        "data": base + "shape=parallelogram;perimeter=parallelogramPerimeter;",
        "input": base + "shape=manualInput;",
        "display": base + "shape=display;",
        "store": base + "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=12;",
        "document": base + "shape=document;boundedLbl=1;",
    }.get(kind, base)


def flow_order():
    d = Diagram("Блок-схема_оформление_заказа", 1100, 1500)
    cx = 250
    bw, bh = 460, 78
    d.box("s", "Начало", cx + 130, 24, 200, 52, "term")
    d.box("cat", "Вывод каталога услуг", cx, 110, bw, bh, "display")
    d.box("pick", "Выбор услуги", cx, 220, bw, 70, "input")
    d.box("role", "Пользователь\nявляется клиентом?", cx + 50, 330, 360, 150, "decision")
    d.box("login", "Вывод страницы\nвхода", 820, 360, 250, 78, "display")
    d.box("elogin", "Конец", 865, 480, 160, 48, "term")
    d.box("add", "Добавление позиции\nв корзину", cx, 520, bw, 86, "process")
    d.box("more", "Оформить\nзаказ?", cx + 70, 640, 320, 140, "decision")
    d.box("cart", "Вывод корзины", cx, 820, bw, bh, "display")
    d.box("empty", "Корзина\nпуста?", cx + 70, 930, 320, 140, "decision")
    d.box("mempty", "Сообщение\n«Корзина пуста»", 820, 960, 250, 78, "display")
    d.box("eempty", "Конец", 865, 1080, 160, 48, "term")
    d.box("form", "Ввод телефона, связи\nи комментария", cx, 1110, bw, 86, "input")
    d.box("ok", "Данные\nкорректны?", cx + 70, 1230, 320, 140, "decision")
    d.box("db", "Запись заказа\nи позиций", cx, 1410, bw, 90, "store")
    d.box("clear", "Очистка корзины", cx, 1530, bw, 70, "process")
    d.box("done", "Сообщение\nо номере заказа", cx, 1630, bw, 78, "display")
    d.box("e", "Конец", cx + 130, 1740, 200, 52, "term")
    d.link("s", "cat")
    d.link("cat", "pick")
    d.link("pick", "role")
    d.link("role", "add", "Да")
    d.link("role", "login", "Нет", "e", "w")
    d.link("login", "elogin")
    d.link("add", "more")
    d.link("more", "cart", "Да")
    d.link("more", "cat", "Нет", "w", "w")
    d.link("cart", "empty")
    d.link("empty", "form", "Нет")
    d.link("empty", "mempty", "Да", "e", "w")
    d.link("mempty", "eempty")
    d.link("form", "ok")
    d.link("ok", "db", "Да")
    d.link("ok", "form", "Нет", "w", "w")
    d.link("db", "clear")
    d.link("clear", "done")
    d.link("done", "e")
    return d


def flow_manage_orders():
    d = Diagram("Блок-схема_управление_заказами", 1180, 1400)
    cx = 340
    d.box("s", "Начало", cx + 110, 20, 200, 52, "term")
    d.box("role", "Какая роль\nу пользователя?", cx + 30, 110, 360, 150, "decision")
    d.box("deny", "Отказ в доступе", 900, 140, 240, 70, "display")
    d.box("edeny", "Конец", 940, 250, 160, 48, "term")
    d.box("mgr", "Вывод всех заказов\nклиентов", 40, 320, 300, 86, "display")
    d.box("status", "Ввод нового статуса", 40, 440, 300, 70, "input")
    d.box("save", "Обновление статуса\nв базе", 40, 540, 300, 86, "store")
    d.box("em", "Конец", 110, 660, 160, 48, "term")
    d.box("cli", "Вывод заказов\nэтого клиента", 560, 320, 300, 86, "display")
    d.box("act", "Какое\nдействие?", 590, 440, 240, 140, "decision")
    d.box("can", "Заказ ещё\nможно менять?", 860, 620, 340, 170, "decision")
    d.box("edit", "Ввод телефона,\nсвязи и комментария", 520, 680, 300, 86, "input")
    d.box("upd", "Сохранение заказа", 520, 800, 300, 70, "store")
    d.box("dele", "Удаление заказа\nи позиций", 860, 840, 280, 80, "process")
    d.box("no", "Сообщение\nо запрете", 1260, 666, 230, 78, "display")
    d.box("ec", "Конец", 620, 960, 160, 48, "term")
    d.link("s", "role")
    d.link("role", "mgr", "Менеджер", "w", "n")
    d.link("role", "cli", "Клиент", "e", "n")
    d.link("role", "deny", "Иная", "e", "w")
    d.link("deny", "edeny")
    d.link("mgr", "status")
    d.link("status", "save")
    d.link("save", "em")
    d.link("cli", "act")
    d.link("act", "edit", "Изменить", "s", "n")
    d.link("act", "can", "Удалить", "e", "n")
    d.link("can", "dele", "Да")
    d.link("can", "no", "Нет", "e", "w")
    d.link("edit", "upd")
    d.link("upd", "ec")
    d.link("dele", "ec", "", "s", "n")
    return d


def flow_users():
    """Три колонки под общим решением; создание и удаление — отдельной полосой снизу."""
    d = Diagram("Блок-схема_управление_пользователями", 1500, 1500)
    d.box("s", "Начало", 640, 16, 180, 48, "term")
    d.box("act", "Какая\nоперация?", 580, 88, 300, 140, "decision")

    d.box("reg", "Ввод логина, почты,\nпароля и имени", 70, 300, 330, 84, "input")
    d.box("vreg", "Логин свободен\nи пароль допустим?", 80, 420, 340, 170, "decision")
    d.box("creg", "Роль «Клиент»\nи профиль", 100, 630, 300, 76, "store")
    d.box("lin", "Открытие сессии", 100, 736, 300, 60, "process")
    d.box("e1", "Конец", 170, 830, 160, 46, "term")

    d.box("elog", "Ввод логина\nи пароля", 520, 300, 300, 78, "input")
    d.box("auth", "Учётные данные\nверны?", 510, 420, 320, 140, "decision")
    d.box("bad", "Сообщение\nоб ошибке", 880, 452, 220, 74, "display")
    d.box("sess", "Сессия по роли\nпрофиля", 530, 610, 280, 74, "process")
    d.box("e2", "Конец", 590, 720, 160, 46, "term")

    d.box("man", "Это\nадминистратор?", 1160, 300, 300, 140, "decision")
    d.box("deny", "Отказ в доступе", 1180, 480, 260, 68, "display")
    d.box("e3", "Конец", 1230, 580, 160, 46, "term")
    d.box("mop", "Что сделать\nс записью?", 1160, 670, 300, 140, "decision")

    d.box("mform", "Ввод данных\nменеджера", 70, 980, 280, 78, "input")
    d.box("msave", "Запись роли\n«Менеджер»", 70, 1090, 280, 72, "store")
    d.box("e4", "Конец", 130, 1196, 160, 46, "term")

    d.box("urole", "Клиент\nили менеджер?", 520, 960, 300, 146, "decision")
    d.box("ustop", "Администратора\nудалить нельзя", 900, 990, 280, 78, "display")
    d.box("e6", "Конец", 960, 1104, 160, 46, "term")
    d.box("udel", "Удаление\nпользователя", 540, 1160, 260, 70, "process")
    d.box("e5", "Конец", 590, 1266, 160, 46, "term")

    d.link("s", "act")
    d.link("act", "reg", "Регистрация", "w", "n")
    d.link("act", "elog", "Вход", "s", "n")
    d.link("act", "man", "Управление", "e", "n", route=[
        (880, 158), (1310, 158), (1310, 300),
    ])
    d.link("reg", "vreg")
    d.link("vreg", "creg", "Да")
    d.link("vreg", "reg", "Нет", "w", "w")
    d.link("creg", "lin")
    d.link("lin", "e1")
    d.link("elog", "auth")
    d.link("auth", "sess", "Да")
    d.link("auth", "bad", "Нет", "e", "w")
    d.link("bad", "elog", "", "n", "e", route=[
        (990, 452), (990, 250), (820, 250), (820, 339),
    ])
    d.link("sess", "e2")
    d.link("man", "deny", "Нет")
    d.link("deny", "e3")
    d.link("man", "mop", "Да", "e", "n", route=[
        (1460, 370), (1520, 370), (1520, 640), (1310, 640), (1310, 670),
    ])
    d.link("mop", "mform", "Создать", "s", "n", route=[
        (1310, 810), (1310, 900), (210, 900), (210, 980),
    ])
    d.link("mop", "urole", "Удалить", "s", "n", route=[
        (1310, 810), (1310, 900), (670, 900), (670, 960),
    ])
    d.link("mform", "msave")
    d.link("msave", "e4")
    d.link("urole", "udel", "Да")
    d.link("urole", "ustop", "Нет", "e", "w")
    d.link("ustop", "e6")
    d.link("udel", "e5")
    return d


def flow_catalog():
    d = Diagram("Блок-схема_управление_каталогом", 1560, 1360)
    d.box("s", "Начало", 620, 16, 180, 48, "term")
    d.box("who", "Пользователь —\nадминистратор?", 530, 90, 360, 148, "decision")
    d.box("view", "Вывод каталога\nуслуг из базы", 40, 112, 330, 84, "display")
    d.box("eview", "Конец", 125, 230, 160, 46, "term")
    d.box("what", "Что\nизменяем?", 570, 280, 280, 136, "decision")

    d.box("cact", "Действие\nс категорией?", 80, 480, 300, 140, "decision")
    d.box("cname", "Ввод названия\nкатегории", 70, 680, 280, 76, "input")
    d.box("cdup", "Название\nуже есть?", 60, 800, 300, 140, "decision")
    d.box("cerr", "Категория уже\nсуществует", 70, 990, 270, 76, "display")
    d.box("csave", "Запись категории", 430, 834, 250, 72, "store")
    d.box("e1", "Конец", 475, 940, 160, 46, "term")

    d.box("chas", "В категории\nесть услуги?", 400, 1100, 310, 140, "decision")
    d.box("cdeny", "Отказ: сначала\nуберите услуги", 60, 1130, 270, 78, "display")
    d.box("cdel", "Удаление\nкатегории", 780, 1134, 240, 70, "process")
    d.box("e2", "Конец", 820, 1240, 160, 46, "term")

    d.box("sact", "Действие\nс услугой?", 1080, 480, 310, 140, "decision")
    d.box("pin", "Ввод карточки\nи изображения", 960, 690, 290, 82, "input")
    d.box("psave", "Запись услуги\nв категорию", 960, 810, 290, 76, "store")
    d.box("e3", "Конец", 1025, 920, 160, 46, "term")
    d.box("pdel", "Удаление услуги.\nНазвание и цена\nв записи остаются", 1280, 680, 320, 116, "process")
    d.box("e4", "Конец", 1360, 840, 160, 46, "term")

    d.link("s", "who")
    d.link("who", "view", "Нет", "w", "e")
    d.link("view", "eview")
    d.link("who", "what", "Да")
    d.link("what", "cact", "Категория", "w", "n")
    d.link("what", "sact", "Услуга", "e", "n")
    d.link("cact", "cname", "Добавить")
    d.link("cact", "chas", "Удалить", "e", "n", route=[
        (380, 550), (740, 550), (740, 1060), (555, 1060), (555, 1100),
    ])
    d.link("cname", "cdup")
    d.link("cdup", "cerr", "Да")
    d.link("cerr", "cname", "", "w", "w")
    d.link("cdup", "csave", "Нет", "e", "w")
    d.link("csave", "e1")
    d.link("chas", "cdeny", "Да", "w", "e")
    d.link("chas", "cdel", "Нет", "e", "w")
    d.link("cdel", "e2")
    d.link("sact", "pin", "Добавить", "s", "n", route=[
        (1235, 620), (1235, 655), (1105, 655), (1105, 690),
    ])
    d.link("sact", "pdel", "Удалить", "s", "n", route=[
        (1235, 620), (1235, 655), (1440, 655), (1440, 680),
    ])
    d.link("pin", "psave")
    d.link("psave", "e3")
    d.link("pdel", "e4")
    return d


def flow_news():
    d = Diagram("Блок-схема_управление_новостями", 1180, 1180)
    d.box("s", "Начало", 470, 16, 180, 48, "term")
    d.box("who", "Пользователь —\nадминистратор?", 400, 90, 340, 146, "decision")
    d.box("list", "Вывод новостей\nпо убыванию даты", 30, 110, 300, 80, "display")
    d.box("one", "Вывод выбранной\nновости", 30, 220, 300, 74, "display")
    d.box("elist", "Конец", 100, 326, 160, 46, "term")
    d.box("op", "Какая\nоперация?", 440, 280, 280, 136, "decision")
    d.box("form", "Ввод заголовка,\nтекста и даты", 860, 200, 280, 82, "input")
    d.box("save", "Запись новости", 860, 320, 280, 68, "store")
    d.box("esave_end", "Конец", 920, 420, 160, 46, "term")
    d.box("edit", "Выбор новости\nи правка полей", 860, 520, 280, 80, "input")
    d.box("esave", "Обновление записи", 860, 630, 280, 68, "store")
    d.box("eedit", "Конец", 920, 730, 160, 46, "term")
    d.box("conf", "Подтвердить\nудаление?", 440, 480, 280, 140, "decision")
    d.box("dele", "Удаление новости", 450, 670, 260, 68, "process")
    d.box("e", "Конец", 500, 780, 160, 46, "term")
    d.link("s", "who")
    d.link("who", "list", "Нет", "w", "e")
    d.link("list", "one")
    d.link("one", "elist")
    d.link("who", "op", "Да")
    d.link("op", "form", "Добавить", "e", "w")
    d.link("form", "save")
    d.link("save", "esave_end")
    d.link("op", "edit", "Изменить", "e", "n", route=[
        (720, 348), (800, 348), (800, 560), (860, 560),
    ])
    d.link("edit", "esave")
    d.link("esave", "eedit")
    d.link("op", "conf", "Удалить")
    d.link("conf", "dele", "Да")
    d.link("conf", "e", "Нет", "w", "w")
    d.link("dele", "e")
    return d


def sitemap(filename, root, items):
    """items: list of (text, children or None)."""
    d = Diagram(filename, 1100, 80)
    d.box("root", root, 24, 24, 250, 64, "process")
    y = 120
    for i, (text, children) in enumerate(items):
        nid = f"n{i}"
        d.box(nid, text, 360, y, 320, 68, "process")
        d.link("root", nid, arrow=False, start="s", end="w")
        if children:
            cy = y
            for j, child in enumerate(children):
                cid = f"n{i}c{j}"
                d.box(cid, child, 760, cy, 340, 64, "process")
                d.link(nid, cid, arrow=False, start="e", end="w")
                cy += 76
            y = max(y + 84, cy + 10)
        else:
            y += 84
    d.h = max(d.h, y + 24)
    return d


def er():
    d = Diagram("Схема_базы_данных", 1680, 1180)
    specs = [
        ("user", "USER", ["PK id", "username", "password", "email", "first_name", "last_name", "is_superuser", "is_staff", "is_active"], 30, 30),
        ("profile", "PROFILE", ["PK id", "FK user_id", "role", "phone"], 430, 40),
        ("category", "CATEGORY", ["PK id", "name", "UK name_key", "UK slug", "description", "position"], 820, 30),
        ("news", "NEWS", ["PK id", "title", "text", "published_at"], 1240, 40),
        ("cart", "CART", ["PK id", "FK user_id", "created_at"], 30, 430),
        ("citem", "CART_ITEM", ["PK id", "FK cart_id", "FK service_id", "quantity"], 400, 450),
        ("product", "SERVICE", ["PK id", "FK category_id", "name", "price", "duration", "method", "description", "image", "available"], 780, 400),
        ("video", "MATERIAL_VIDEO", ["PK id", "title", "description", "video", "created_at"], 1240, 360),
        ("order", "ORDER", ["PK id", "FK user_id", "status", "total", "phone", "contact", "comment", "created_at"], 30, 780),
        ("oitem", "ORDER_ITEM", ["PK id", "FK order_id", "FK service_id", "service_name", "quantity", "price"], 460, 800),
    ]
    for nid, title, fields, x, y in specs:
        lines = 1 + len(fields)
        h = 20 + 30 * lines
        d.box(nid, title + "\n" + "\n".join(fields), x, y, 340, h, "header")
    d.link("user", "profile", "1 — 1", "e", "w", arrow=False)
    d.link("user", "cart", "1 — 1", "s", "n", arrow=False)
    d.link("user", "order", "1 — N", "s", "n", arrow=False)
    d.link("cart", "citem", "1 — N", "e", "w", arrow=False)
    d.link("category", "product", "1 — N", "s", "n", arrow=False)
    d.link("product", "citem", "1 — N", "w", "e", arrow=False)
    d.link("product", "oitem", "1 — N", "s", "e", arrow=False)
    d.link("order", "oitem", "1 — N", "e", "w", arrow=False)
    return d


def wire(filename, blocks, w=1040, h=720):
    d = Diagram(filename, w, h)
    for i, (x, y, bw, bh, text, kind) in enumerate(blocks):
        d.box(f"b{i}", text, x, y, bw, bh, kind)
    return d


def header_blocks():
    return [(24, 16, 992, 52, "ПСИ-ЭКСПЕРТ    Главная | О центре | Каталог | Новости | Материалы | Контакты    Вход / роль", "header")]


def footer_blocks(h=720):
    return [(24, h - 56, 992, 40, "Пси-Эксперт · Псков · телефон · разработчик сайта", "process")]


def build_wires():
    h = header_blocks()
    f = footer_blocks()
    pages = []
    pages.append(wire("Шаблон_главная", h + [
        (24, 84, 992, 230, "Название «Пси-Эксперт»\nАннотация центра и кнопка «Смотреть каталог»\nФото спокойного кабинета", "display"),
        (24, 330, 316, 150, "Категория\nИндивидуальная терапия", "card"),
        (364, 330, 316, 150, "Категория\nСпециальные методы", "card"),
        (700, 330, 316, 150, "Категория\nФорматы консультаций", "card"),
        (24, 496, 316, 150, "Новость 1\nдата и заголовок", "card"),
        (364, 496, 316, 150, "Новость 2", "card"),
        (700, 496, 316, 150, "Новость 3", "card"),
    ] + footer_blocks(720)))
    pages.append(wire("Шаблон_каталог", h + [
        (24, 84, 992, 54, "Заголовок «Каталог» и пояснение иерархии", "process"),
        (24, 152, 150, 56, "Все", "card"),
        (186, 152, 270, 56, "Индивидуальная терапия", "card"),
        (468, 152, 250, 56, "Специальные методы", "card"),
        (730, 152, 286, 56, "Форматы консультаций", "card"),
        (24, 224, 992, 36, "Название категории и описание", "process"),
        (24, 276, 230, 250, "Изображение\nНазвание\nСтоимость\nВ корзину", "card"),
        (270, 276, 230, 250, "Карточка услуги", "card"),
        (516, 276, 230, 250, "Карточка услуги", "card"),
        (762, 276, 230, 250, "Карточка услуги", "card"),
        (24, 542, 992, 40, "Следующая категория — такой же блок из пяти позиций", "process"),
    ] + footer_blocks()))
    pages.append(wire("Шаблон_карточка_услуги", h + [
        (24, 84, 992, 32, "Каталог / категория", "process"),
        (24, 128, 500, 470, "Изображение услуги", "display"),
        (544, 128, 472, 50, "Категория", "process"),
        (544, 190, 472, 64, "Название услуги", "header"),
        (544, 266, 472, 48, "Стоимость", "process"),
        (544, 326, 472, 110, "Описание запроса", "process"),
        (544, 448, 472, 70, "Длительность и метод", "process"),
        (544, 532, 220, 48, "В корзину", "card"),
    ] + footer_blocks()))
    pages.append(wire("Шаблон_новости", h + [
        (24, 84, 992, 56, "Новости — список по убыванию даты", "header"),
        (24, 156, 992, 110, "Дата\nЗаголовок\nТекст новости", "card"),
        (24, 280, 992, 110, "Следующая новость", "card"),
        (24, 404, 992, 110, "Следующая новость", "card"),
        (24, 528, 992, 110, "Следующая новость", "card"),
    ] + footer_blocks()))
    pages.append(wire("Шаблон_видео", h + [
        (24, 84, 992, 70, "Полезные материалы — видео из базы", "header"),
        (24, 170, 992, 220, "Видеоплеер", "display"),
        (24, 404, 992, 90, "Название и описание ролика", "process"),
        (24, 508, 992, 140, "Следующий ролик", "card"),
    ] + footer_blocks()))
    pages.append(wire("Шаблон_контакты", h + [
        (24, 84, 992, 56, "Контакты", "header"),
        (24, 160, 480, 280, "Телефон\nWhatsApp и Telegram\nПсков, очно и онлайн\nЧасы записи", "card"),
        (528, 160, 488, 280, "Разработчик сайта\nЧуров А. А., группа 0434-03\nDjango, SQLite, HTML, CSS", "card"),
    ] + footer_blocks()))
    pages.append(wire("Шаблон_корзина", h + [
        (24, 84, 992, 50, "Корзина записи (только клиент)", "header"),
        (24, 150, 992, 90, "Услуга | Категория | Количество | Сумма | Убрать", "process"),
        (24, 252, 992, 90, "Следующая позиция", "process"),
        (24, 356, 992, 90, "Следующая позиция", "process"),
        (560, 470, 456, 70, "Итого и кнопка «Оформить запись»", "card"),
    ] + footer_blocks()))
    pages.append(wire("Шаблон_мои_заказы", h + [
        (24, 84, 992, 56, "Мои заказы (клиент)", "header"),
        (24, 156, 992, 160, "№ записи, статус, дата, сумма\nТелефон и способ связи\nПозиции\nИзменить | Удалить", "card"),
        (24, 332, 992, 160, "Следующая запись", "card"),
    ] + footer_blocks()))
    pages.append(wire("Шаблон_заказы_менеджера", h + [
        (24, 84, 992, 56, "Заказы клиентов (менеджер)", "header"),
        (24, 156, 992, 180, "№, клиент, статус, связь, состав\nСписок статусов и кнопка «Сохранить статус»", "card"),
        (24, 352, 992, 180, "Следующий заказ", "card"),
    ] + footer_blocks()))
    pages.append(wire("Шаблон_регистрация", h + [
        (24, 84, 992, 56, "Регистрация клиента", "header"),
        (220, 170, 600, 420, "Логин\nИмя и фамилия\nПочта\nТелефон\nПароль и повтор\nКнопка «Создать учётную запись»\nСсылка на вход", "input"),
    ] + footer_blocks()))
    pages.append(wire("Шаблон_панель", h + [
        (24, 84, 992, 48, "Обзор | Категории | Каталог | Новости | Видео | Пользователи", "header"),
        (24, 150, 300, 120, "Категории\nсчётчик", "card"),
        (344, 150, 300, 120, "Услуги", "card"),
        (664, 150, 300, 120, "Новости", "card"),
        (24, 290, 992, 300, "Список выбранного раздела\nДобавить / Изменить / Удалить\nПроверка уникальности названия категории\nРегистрация менеджера и удаление клиента или менеджера", "process"),
    ] + footer_blocks()))
    return pages


def main():
    diagrams = [
        sitemap("Карта_сайта_гость", "Главная", [
            ("О центре", None),
            ("Новости", None),
            ("Контакты", None),
            ("Каталог", ["Индивидуальная терапия", "Специальные методы", "Форматы консультаций", "Карточка услуги"]),
            ("Полезные материалы", None),
            ("Вход", None),
            ("Регистрация", None),
        ]),
        sitemap("Карта_сайта_клиент", "Главная", [
            ("Каталог", ["Карточка услуги"]),
            ("Корзина", ["Изменение количества", "Удаление позиции"]),
            ("Оформление записи", None),
            ("Мои заказы", ["Просмотр", "Изменение", "Удаление"]),
            ("Новости", None),
            ("Полезные материалы", None),
            ("Контакты", None),
            ("Выход", None),
        ]),
        sitemap("Карта_сайта_менеджер", "Главная", [
            ("Каталог", None),
            ("Новости", None),
            ("Полезные материалы", None),
            ("Контакты", None),
            ("Заказы клиентов", ["Просмотр состава", "Смена статуса"]),
            ("Выход", None),
        ]),
        sitemap("Карта_сайта_администратор", "Главная", [
            ("Каталог", None),
            ("Новости", None),
            ("Полезные материалы", None),
            ("Контакты", None),
            ("Панель", ["Категории", "Услуги", "Новости", "Видео", "Пользователи"]),
            ("Выход", None),
        ]),
        er(),
        flow_order(),
        flow_manage_orders(),
        flow_users(),
        flow_catalog(),
        flow_news(),
    ]
    diagrams.extend(build_wires())
    for d in diagrams:
        path = d.save()
        print(d.filename, d.w, d.h, os.path.getsize(path))


if __name__ == "__main__":
    main()
