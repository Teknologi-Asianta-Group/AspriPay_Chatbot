"""
Rapikan jawaban berbentuk daftar, dan ambil butirnya buat tombol pintasan.

Kenapa dirapikan di sini, bukan cuma lewat prompt: jawaban datang dari DUA sumber
dengan gaya berbeda. Mistral menurut aturan 9 di SYSTEM_PROMPT, tapi Cognee punya
prompt sendiri yang tidak bisa kita atur - dia menulis "- **Label** : detail" lengkap
dengan penebalan markdown dan kadang sub-poin bertingkat "•". Menyeragamkannya di
sini bersifat deterministik: hasilnya sama persis setiap kali, tanpa bergantung pada
kemauan model.

Bentuk baku yang dihasilkan:

    Berikut cara top-up saldo AspriPay:

    1. Virtual Account: transfer ke nomor VA yang ditampilkan.
    2. QRIS: scan kode QR lewat aplikasi pembayaran.
    3. E-wallet: pilih GoPay, OVO, atau DANA.

    Silakan pilih metode yang sesuai.

Tidak ada isi yang dibuang - hanya disusun ulang. Kalau bentuknya tidak dikenali,
jawaban asli dikembalikan apa adanya.
"""

import re
from dataclasses import dataclass, field

# butir utama: "1. ", "2) ", "- ", "* "
_BULLET_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+(.+)$")
# sub-poin bertingkat: "• ", "· ", atau butir yang menjorok masuk
_SUBBULLET_RE = re.compile(r"^\s*[•·]\s+(.+)$|^\s{2,}[-*]\s+(.+)$")
# label yang ditebalkan markdown (gaya Cognee)
_BOLD_LABEL_RE = re.compile(r"^\*\*(.+?)\*\*\s*(.*)$")
# pemisah label dan penjelasan pada butir tanpa penebalan
_SEPARATOR_RE = re.compile(r"\s*[:–—]\s+|\s+-\s+")

MIN_ITEMS = 3
MAX_ITEMS = 12
# Tombol pintasan baru berguna waktu butirnya banyak - daftar pendek sudah enak
# dibaca sebagai teks, tombolnya cuma bikin tampilan dobel.
MIN_ITEMS_FOR_BUTTONS = 5

MAX_LABEL_WORDS = 5
MAX_LABEL_CHARS = 40


@dataclass
class MenuItem:
    # `body` = kalimat utuh satu baris, dipakai buat teks bernomor DAN isi tombol.
    # `label` = judul pendek buat tulisan di tombol; None kalau tidak ada yang layak.
    body: str
    label: str | None = None


@dataclass
class ParsedList:
    intro: str
    items: list[MenuItem]
    closing: str = ""
    _subs: list[list[str]] = field(default_factory=list, repr=False)


def _clean(text: str) -> str:
    """Buang penanda markdown dan rapikan spasi."""
    return " ".join(text.replace("**", "").replace("__", "").split()).strip()


def _as_label(text: str) -> str | None:
    """Judul tombol kalau cukup pendek, None kalau kepanjangan buat dijadikan tombol."""
    label = _clean(text).strip(" :;-–—")
    if not label or len(label) > MAX_LABEL_CHARS or len(label.split()) > MAX_LABEL_WORDS:
        return None
    return label


def _parse_item(raw: str) -> MenuItem:
    """
    Susun satu butir jadi kalimat utuh + judul pendek.

    Penebalan markdown TIDAK selalu berarti label. Cognee menulis
    "**Pilih metode top-up** yang diinginkan:" - di situ teks tebal cuma penekanan di
    tengah kalimat. Kalau dipaksa jadi label, hasilnya "Pilih metode top-up: yang
    diinginkan:" yang rusak. Jadi teks tebal baru dianggap label kalau memang diikuti
    tanda pemisah; kalau tidak, kalimatnya dibiarkan mengalir apa adanya.
    """
    raw = raw.strip()
    bold = _BOLD_LABEL_RE.match(raw)
    if bold:
        head, rest = _clean(bold.group(1)), _clean(bold.group(2))
        if rest[:1] in {":", "-", "–", "—"}:
            detail = rest.lstrip(":-–— ").strip()
            body = f"{head}: {detail}" if detail else head
        else:
            body = f"{head} {rest}".strip()
        return MenuItem(body=body, label=_as_label(head))

    parts = _SEPARATOR_RE.split(raw, maxsplit=1)
    if len(parts) == 2:
        head, detail = _clean(parts[0]), _clean(parts[1])
        return MenuItem(body=f"{head}: {detail}", label=_as_label(head))

    return MenuItem(body=_clean(raw), label=None)


def parse_list(answer: str) -> ParsedList | None:
    """Baca jawaban jadi (pembuka, butir, penutup). None kalau bukan daftar yang dikenali."""
    intro_lines: list[str] = []
    closing_lines: list[str] = []
    items: list[MenuItem] = []
    subs: list[list[str]] = []

    for line in (answer or "").splitlines():
        sub = _SUBBULLET_RE.match(line)
        if sub and items:
            subs[-1].append(_clean(sub.group(1) or sub.group(2)).strip(" .,;"))
            continue

        bullet = _BULLET_RE.match(line)
        if bullet:
            if closing_lines:
                return None  # daftar tersambung lagi sesudah penutup - bentuknya tak terduga
            items.append(_parse_item(bullet.group(1)))
            subs.append([])
        elif not line.strip():
            continue
        elif items:
            closing_lines.append(_clean(line))
        else:
            intro_lines.append(_clean(line))

    if not (MIN_ITEMS <= len(items) <= MAX_ITEMS):
        return None

    # Sub-poin dilipat masuk ke kalimat induknya - satu butir tetap satu baris.
    for item, daftar_sub in zip(items, subs):
        if daftar_sub:
            gabung = ", ".join(s for s in daftar_sub if s)
            pemisah = " " if item.body.endswith(":") else ": "
            item.body = f"{item.body}{pemisah}{gabung}"
        item.body = item.body.strip(" ,;")
        if not item.body:
            return None

    return ParsedList(
        intro=" ".join(intro_lines).strip(),
        items=items,
        closing=" ".join(closing_lines).strip(),
    )


def normalize_list_answer(answer: str) -> str:
    """
    Susun ulang jawaban berbentuk daftar jadi format bernomor yang baku.
    Jawaban yang bukan daftar dikembalikan apa adanya.
    """
    parsed = parse_list(answer)
    if parsed is None:
        return answer

    baris: list[str] = []
    if parsed.intro:
        baris.append(parsed.intro.rstrip(" .:") + ":")
        baris.append("")
    for nomor, item in enumerate(parsed.items, start=1):
        titik = "" if item.body.endswith((".", "!", "?", ")")) else "."
        baris.append(f"{nomor}. {item.body}{titik}")
    if parsed.closing:
        baris.append("")
        baris.append(parsed.closing)
    return "\n".join(baris)


def extract_menu_items(answer: str) -> list[MenuItem]:
    """
    Butir yang layak dijadikan tombol pintasan. Kosong artinya tidak perlu tombol.

    Semua butir harus punya judul pendek - kalau ada satu saja yang tidak, tombolnya
    ditiadakan seluruhnya daripada sebagian butir tidak terwakili.
    """
    parsed = parse_list(answer)
    if parsed is None or len(parsed.items) < MIN_ITEMS_FOR_BUTTONS:
        return []
    if any(item.label is None for item in parsed.items):
        return []
    return parsed.items
