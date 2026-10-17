"""Private-chat order menus. Identity always comes from the linked account."""

import json
import re
import time
from . import orders, service as svc


def keyboard(rows):
    return {
        "reply_markup": {
            "keyboard": [[{"text": text} for text in row] for row in rows],
            "resize_keyboard": True,
        }
    }


def menu(user):
    return keyboard(
        [["Order baharu", "Order saya"], ["Bantuan"]]
        if user["role"] == "recipient"
        else [["Tugasan"], ["Bantuan"]]
    )


def help_text(user):
    if user["role"] == "recipient":
        return "Order parcel dari sini: tekan Order baharu atau /order.\n/orders — status order\n/code ORD-ID — kod pengambilan semasa\n/cancel_order ORD-ID — batal order yang belum diterima\n/cancel — batal draf\n/stop — putuskan Telegram\n\nKod diberi selepas pekerja mengesahkan simpanan."
    return "Tugasan pekerja PAP:\n/tasks — senarai order masuk\n/accept ORD-ID — terima tugasan\n/store ORD-ID [S/M/L/XL] — pilih loker automatik; saiz pilihan\n/stored ORD-ID — sahkan parcel disimpan dan pintu ditutup (simulasi sahaja)\n/reject ORD-ID sebab — tolak order dengan sebab\n\nDalam mod peranti, sensor mengesahkan simpanan. /stop memutuskan Telegram."


def draft_save(db, uid, stage, data):
    db.execute(
        "INSERT INTO telegram_drafts VALUES (?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET stage=excluded.stage,data=excluded.data,expires_at=excluded.expires_at",
        (uid, stage, json.dumps(data), int(time.time()) + 1800),
    )


def handle(db, user, text, cfg):
    text = text.strip()
    text = {
        "Order baharu": "/order",
        "Order saya": "/orders",
        "Tugasan": "/tasks",
        "Bantuan": "/help",
        "Batal": "/cancel",
    }.get(text, text)
    parts = text.split(maxsplit=2)
    command = parts[0].split("@")[0].lower() if parts else ""
    oid = parts[1].upper() if len(parts) > 1 else ""
    if command in ("/help", "/start"):
        return help_text(user), menu(user)
    if command == "/cancel":
        db.execute("DELETE FROM telegram_drafts WHERE user_id=?", (user["id"],))
        return "Draf dibatalkan. Order yang sudah dihantar tidak berubah.", menu(user)
    if command in ("/orders", "/tasks", "/status"):
        staff = user["role"] != "recipient"
        items = orders.listing(db, user, cfg)
        if staff:
            items = [
                o
                for o in items
                if o["status"] in ("PENDING", "ACCEPTED", "RESERVED", "ISSUE")
            ]
        items = items[:6]
        if not items:
            return (
                "Tiada tugasan terbuka."
                if staff
                else "Belum ada order. Tekan Order baharu untuk bermula."
            ), menu(user)
        chunks, buttons = [], []
        for o in items:
            line = f"{o['id']} · {o['status_label']}\n{o['courier']} · {o['tracking']}"
            if staff:
                line += f"\n{o['recipient_name']} · {o['student_id']}"
                if o["assigned_name"]:
                    line += f"\nPekerja: {o['assigned_name']}"
                if o["status"] == "PENDING":
                    buttons.append([f"/accept {o['id']}"])
                elif o["assigned_to"] == user["id"] and o["status"] == "ACCEPTED":
                    buttons.append([f"/store {o['id']}"])
                elif (
                    o["assigned_to"] == user["id"]
                    and o["status"] == "RESERVED"
                    and cfg.hardware_mode == "simulated"
                ):
                    buttons.append([f"/stored {o['id']}"])
            elif o["pickup_code"]:
                line += f"\nLoker {o['parcel']['locker_id']} · Kod: {o['pickup_code']['otp']}"
            elif o["status"] == "READY":
                buttons.append([f"/code {o['id']}"])
            if o["reason"]:
                line += "\n" + o["reason"][:150]
            chunks.append(line)
        buttons.append(["Tugasan" if staff else "Order saya", "Bantuan"])
        return "\n\n".join(
            chunks
        ) + "\n\nSehingga 6 order dipaparkan. Senarai penuh di web.", keyboard(buttons)
    if command in ("/accept", "/store", "/stored", "/reject", "/cancel_order", "/code"):
        svc.require(
            bool(re.fullmatch(r"ORD-[A-F0-9]{8}", oid)),
            "Masukkan ID order, contoh /accept ORD-12AB34CD.",
            422,
        )
        if command == "/accept":
            orders.accept(db, oid, user)
            return (
                f"Tugasan {oid} diterima. Setelah parcel berada di tangan anda, tekan /store {oid} untuk mula menyimpan.",
                keyboard([[f"/store {oid}"], ["Tugasan"]]),
            )
        if command == "/store":
            o = orders.store(
                db, oid, user, cfg, size=parts[2].upper() if len(parts) > 2 else None
            )
            if o["status"] == "READY":
                return f"{oid} sudah disimpan. Pelanggan telah dimaklumkan.", menu(user)
            message = f"{oid} · Loker {o['parcel']['locker_id']}\nMasukkan parcel {o['tracking']} untuk {o['recipient_name']} dan tutup pintu."
            if cfg.hardware_mode == "simulated":
                return (
                    message
                    + "\nMOD SIMULASI: sahkan hanya selepas parcel diletak dan pintu ditutup.",
                    keyboard([[f"/stored {oid}"], ["Tugasan"]]),
                )
            return (
                message
                + "\nTunggu pintu terbuka sebelum memasukkan parcel. Sensor akan mengesahkan simpanan; semak /tasks.",
                menu(user),
            )
        if command == "/stored":
            orders.confirm_storage(db, oid, user, cfg)
            return (
                f"{oid} sedia diambil. Notifikasi dan kod pengambilan telah dimasukkan dalam giliran pelanggan.",
                menu(user),
            )
        if command == "/reject":
            svc.require(user["role"] != "recipient", "Tindakan ini untuk pekerja.", 403)
            orders.cancel(db, oid, user, parts[2] if len(parts) > 2 else "")
            return f"{oid} ditolak. Pelanggan telah dimaklumkan.", menu(user)
        if command == "/cancel_order":
            svc.require(user["role"] == "recipient", "Arahan ini untuk pelanggan.", 403)
            orders.cancel(db, oid, user)
            return f"{oid} dibatalkan.", menu(user)
        o = orders.get(db, oid, user)
        svc.require(o["recipient_id"] == user["id"], "Kod hanya untuk penerima.", 403)
        svc.require(o["parcel_id"] is not None, "Parcel belum disimpan.")
        p = svc.parcel(db, o["parcel_id"])
        code = svc.ensure_code(db, p, cfg)
        return (
            f"{oid} · Loker {p['locker_id']} · PAP-01\nKod pengambilan: {code['otp']}\nKod ini peribadi. Semak caj dan sahkan pengambilan di kiosk.",
            menu(user),
        )
    if command == "/order":
        svc.require(
            user["role"] == "recipient",
            "Order dibuat oleh pelanggan. Gunakan /tasks untuk tugasan pekerja.",
            403,
        )
        draft_save(db, user["id"], "tracking", {})
        return (
            "Order baharu · 1/4\nMasukkan nombor tracking parcel (4–60 huruf/angka/sengkang).\n/cancel untuk batal.",
            keyboard([["Batal"]]),
        )
    draft = db.execute(
        "SELECT * FROM telegram_drafts WHERE user_id=? AND expires_at>?",
        (user["id"], int(time.time())),
    ).fetchone()
    if not draft:
        return (
            "Pilih menu di bawah atau /help. Draf order tamat selepas 30 minit.",
            menu(user),
        )
    svc.require(user["role"] == "recipient", "Draf ini untuk akaun pelanggan.", 403)
    data = json.loads(draft["data"])
    stage = draft["stage"]
    if stage == "tracking":
        svc.require(
            bool(re.fullmatch(r"[A-Za-z0-9-]{4,60}", text)),
            "Tracking mesti 4–60 huruf, angka atau sengkang.",
            422,
        )
        data["tracking"] = text.upper()
        draft_save(db, user["id"], "courier", data)
        return "2/4 · Pilih atau taip nama syarikat kurier.", keyboard(
            [
                ["SPX Express", "J&T Express"],
                ["Ninja Van", "Pos Laju"],
                ["DHL eCommerce", "Flash Express"],
                ["Batal"],
            ]
        )
    if stage == "courier":
        svc.require(
            2 <= len(text) <= 50 and not any(ord(c) < 32 for c in text),
            "Nama kurier mesti 2–50 aksara.",
            422,
        )
        data["courier"] = text
        draft_save(db, user["id"], "size", data)
        return (
            "3/4 · Anggaran saiz parcel: S / M / L / XL. Pekerja boleh melaraskan saiz loker selepas pemeriksaan.",
            keyboard([["S", "M", "L", "XL"], ["Batal"]]),
        )
    if stage == "size":
        svc.require(
            text.upper() in ("S", "M", "L", "XL"), "Pilih S, M, L atau XL.", 422
        )
        data["size"] = text.upper()
        draft_save(db, user["id"], "notes", data)
        return (
            "4/4 · Catatan untuk pekerja (maksimum 300 aksara), atau tekan Tiada catatan.",
            keyboard([["Tiada catatan"], ["Batal"]]),
        )
    if stage == "notes":
        svc.require(len(text) <= 300, "Catatan maksimum 300 aksara.", 422)
        data["notes"] = "" if text in ("Tiada catatan", "-") else text
        draft_save(db, user["id"], "confirm", data)
        return (
            f"Semak order anda:\n{data['tracking']}\n{data['courier']} · Saiz {data['size']}\nCatatan: {data['notes'] or 'Tiada'}\nLokasi: PAP-01\n\nCaj asas RM0.50–RM1.00; caj lewat bermula selepas 24 jam disimpan. Hantar order?",
            keyboard([["Hantar order"], ["Batal"]]),
        )
    svc.require(
        text == "Hantar order", "Tekan Hantar order untuk sahkan, atau /cancel.", 422
    )
    o = orders.create(db, user, data, "telegram")
    db.execute("DELETE FROM telegram_drafts WHERE user_id=?", (user["id"],))
    return (
        f"Order {o['id']} dihantar. Pekerja telah menerima notifikasi. Tunggu kod pengambilan selepas parcel disimpan.",
        menu(user),
    )
