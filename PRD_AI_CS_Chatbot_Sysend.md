# PRD: AI Customer Service Chatbot (Codename: Sysend)
**Versi:** 0.3 (Draft)
**Tanggal:** 28 Agustus 2026
**Status:** Draft untuk review internal

---

## 1. Ringkasan Eksekutif

Sysend adalah chatbot AI customer service (CS) berbasis RAG (Retrieval-Augmented Generation) yang dirancang khusus untuk **web live chat di situs aspripay**. Chatbot ini menjawab pertanyaan pengunjung/pelanggan aspripay secara otomatis langsung dari widget chat yang tertanam di website, menggunakan basis pengetahuan (knowledge base) milik aspripay.

Berbeda dari pemain omnichannel seperti HaloAI atau Cekat.ai yang menyasar sebanyak mungkin channel (WhatsApp, Instagram, Facebook, LiveChat, dll) dan bergantung pada LLM cloud pihak ketiga (mis. GPT-4), Sysend sengaja dibatasi hanya untuk satu channel — web chat aspripay — dan menjalankan inferensi LLM secara lokal. Fokus sesempit ini memungkinkan produk lebih cepat matang di channel yang paling relevan untuk aspripay, dengan biaya operasional dan risiko privasi data yang lebih rendah.

## 2. Latar Belakang & Masalah

- Pengunjung situs aspripay perlu jalur bantuan cepat langsung di website, tanpa harus berpindah aplikasi (WhatsApp/Telegram) untuk mendapat jawaban.
- Solusi seperti HaloAI dan Cekat.ai menyediakan CS otomatis omnichannel dengan CRM, broadcast, dan human handoff — namun harga berlangganan mengikuti biaya LLM cloud per pesan, dan datanya diproses di server pihak ketiga.
- Untuk kebutuhan aspripay saat ini, cukup satu channel (web chat) yang perlu dilayani dengan baik — sehingga tidak perlu kompleksitas dan biaya integrasi banyak channel sekaligus.
- Ada celah untuk chatbot yang fokus, lebih murah dioperasikan (inferensi lokal), dan basis pengetahuannya (RAG) dikustomisasi khusus untuk kebutuhan aspripay.

## 3. Tujuan Produk

**Goals:**
1. Menyediakan chatbot CS berbasis AI khusus untuk **web widget chat di situs aspripay**, yang bisa menjawab pertanyaan pengunjung secara akurat menggunakan basis pengetahuan (knowledge base) milik aspripay.
2. Memberikan dashboard bagi tim aspripay untuk memantau percakapan web chat dan mengambil alih (human handoff) saat AI tidak bisa menjawab.
3. Menjaga biaya operasional rendah dengan inferensi LLM lokal (Ollama + Qwen 7B), bukan API LLM cloud berbayar per-token.
4. Menjadi solusi CS otomatis yang benar-benar disesuaikan dengan kebutuhan, produk, dan alur pelanggan aspripay — bukan produk generik multi-klien maupun omnichannel.

**Non-Goals (di luar cakupan versi ini):**
- Menjadi produk multi-tenant/multi-klien yang dijual ke bisnis lain — versi ini didedikasikan khusus untuk aspripay.
- Integrasi WhatsApp Business API, Telegram, Instagram DM, Facebook Messenger, TikTok, atau channel lain di luar web widget — dipertimbangkan sebagai kandidat fase berikutnya, bukan bagian dari versi ini.
- Fitur e-commerce penuh (katalog produk, checkout, pembayaran di dalam chat) kecuali relevan langsung dengan alur aspripay.
- Voice/telepon.

## 4. Target Pengguna

- **Primary:** Pengunjung/pelanggan situs **aspripay** yang menghubungi CS lewat web chat widget di website aspripay.
- **Pengguna internal:** Tim CS/agent aspripay yang memakai dashboard untuk memantau percakapan web chat dan mengambil alih dari AI saat diperlukan.

## 5. Diferensiasi vs HaloAI / Cekat.ai

| Aspek | HaloAI / Cekat.ai (omnichannel) | Sysend (khusus web chat aspripay) |
|---|---|---|
| Channel | WhatsApp, Instagram, Facebook, LiveChat, dll | Web chat widget saja, di situs aspripay |
| Model AI | LLM cloud (mis. GPT-4) | LLM lokal (Ollama, Qwen 7B) + RAG |
| Struktur biaya | Umumnya mengikuti volume pesan/API cloud | Biaya infra tetap (server lokal), tanpa biaya per-token ke pihak ketiga |
| Privasi data | Data percakapan diproses di cloud pihak ketiga | Data dan inferensi bisa tetap on-premise/self-hosted |
| Kompleksitas setup | Banyak channel, banyak konfigurasi | Sangat sederhana — hanya satu widget chat untuk di-embed di situs aspripay |

## 6. Ruang Lingkup

**In-scope (MVP):**
- Channel: Web chat widget (embeddable JS) di situs aspripay
- RAG knowledge base khusus aspripay (upload dokumen/FAQ)
- Human handoff (agent bisa ambil alih percakapan dari AI)
- Inbox untuk memantau seluruh percakapan web chat
- Manajemen kontak & riwayat percakapan dasar (CRM-lite)
- Dashboard analitik dasar (volume chat, response time, resolution rate)

**Out-of-scope (MVP, kandidat fase berikutnya):**
- WhatsApp Business API dan Telegram sebagai channel tambahan
- Channel lain (Instagram, Facebook, dll)
- Broadcast/campaign message berskala besar
- Multi-tenant self-service SaaS (signup mandiri, billing otomatis)
- Integrasi payment gateway

## 7. Fitur Utama (Functional Requirements)

### 7.1 Core AI Engine
- RAG pipeline dibangun dengan **Haystack**: dokumen/knowledge base aspripay di-index ke vector store (Qdrant), retrieval dikombinasikan dengan system prompt aspripay untuk menghasilkan jawaban.
- **Cognee** membangun knowledge graph dari data aspripay (entitas & relasi antar topik/produk) sebagai lapisan memory tambahan di luar pencarian vector biasa — membantu untuk pertanyaan yang butuh konteks relasional, bukan sekadar kemiripan teks.
- Inferensi via Ollama dengan model Qwen 7B, berjalan lokal, dipanggil sebagai generator di pipeline Haystack.
- Kemampuan fallback: jika AI tidak yakin dengan jawaban (confidence rendah / topik di luar knowledge base), otomatis eskalasi ke agent manusia.

### 7.2 Web Chat Widget
- Widget chat embeddable (JS snippet) untuk dipasang di halaman-halaman situs aspripay.
- Tampilan yang bisa disesuaikan (warna, logo, posisi widget) agar konsisten dengan branding aspripay.
- Riwayat percakapan tetap tersimpan selama sesi pengunjung berlangsung di website.

### 7.3 Inbox & Human Handoff
- Tampilan inbox untuk memantau seluruh percakapan web chat yang masuk.
- Agent bisa melihat riwayat percakapan lengkap (termasuk yang dijawab AI) sebelum mengambil alih.
- Status percakapan: ditangani AI / menunggu agent / ditangani agent / selesai.

### 7.4 Manajemen Kontak (CRM-lite)
- Profil kontak per pengunjung/pelanggan (nama/kontak jika tersedia, riwayat percakapan, tag/label).
- Pencarian dan filter kontak/percakapan.

### 7.5 Dashboard & Analitik
- Volume percakapan web chat per hari.
- Rata-rata waktu respons AI vs agent.
- Tingkat eskalasi ke manusia (AI resolution rate).
- Topik pertanyaan yang paling sering muncul (berguna untuk memperkaya knowledge base).

### 7.6 Admin & Konfigurasi
- Upload/kelola dokumen knowledge base aspripay.
- Editor system prompt (persona, tone, batasan topik).
- Manajemen jam operasional & pesan auto-reply di luar jam kerja.

## 8. Arsitektur Teknis (Ringkasan)

- **Backend:** FastAPI (Python)
- **RAG orchestration:** Haystack
- **AI memory / knowledge graph:** Cognee
- **Vector store:** Qdrant
- **Database relasional:** MySQL (kontak, percakapan, konfigurasi)
- **LLM inference:** Ollama, model Qwen 7B (lokal)
- **Web widget:** komponen JS embeddable yang berkomunikasi ke backend via WebSocket/REST API, menormalisasi pesan masuk/keluar ke format internal sebelum masuk ke RAG pipeline.
- **Orkestrasi agent handoff:** state machine sederhana per percakapan (AI-handling → escalated → agent-handling → resolved).

## 9. Non-Functional Requirements

- **Estimasi beban:** ~100–200 kontak/hari, masing-masing 10–20 pertukaran pesan → perkiraan 1.000–4.000 pesan/hari di fase awal. Arsitektur perlu nyaman menangani beban ini di satu instance sebelum mempertimbangkan scaling horizontal.
- **Latensi respons AI:** target respons awal di bawah beberapa detik untuk menjaga pengalaman percakapan tetap natural (perlu diuji dengan Qwen 7B di hardware yang tersedia).
- **Keamanan & privasi data:** data percakapan dan knowledge base disimpan dan diproses secara lokal/self-hosted, tidak dikirim ke LLM API pihak ketiga.
- **Reliabilitas:** widget chat harus tetap graceful jika koneksi WebSocket terputus (auto-reconnect, retry pengiriman pesan).
- **Skalabilitas:** desain modular agar penambahan channel baru (WhatsApp/Telegram di fase berikutnya) tidak memerlukan perombakan core RAG engine.

## 10. Metrik Keberhasilan (KPI)

- % percakapan yang terselesaikan penuh oleh AI tanpa eskalasi (AI resolution rate)
- Rata-rata waktu respons pertama (first response time)
- Tingkat kepuasan pelanggan (bisa diukur lewat rating sederhana pasca-chat)
- Pengurangan beban tim CS aspripay (jumlah percakapan yang tidak perlu ditangani manual)
- Biaya infra per 1.000 percakapan (untuk validasi keunggulan biaya vs kompetitor cloud-based)

## 11. Roadmap Fase

- **Fase 1 (MVP):** RAG engine + web chat widget + inbox + human handoff dasar, khusus untuk situs aspripay.
- **Fase 2:** Tambahan channel WhatsApp dan/atau Telegram untuk aspripay, dashboard analitik lebih lengkap, multi-agent (role & permission).
- **Fase 3:** Evaluasi ekspansi channel lain (Instagram/Facebook) dan/atau evaluasi model multi-tenant self-service jika arah produk menuju SaaS.

## 12. Risiko & Mitigasi

| Risiko | Mitigasi |
|---|---|
| Kualitas jawaban AI kurang akurat untuk pertanyaan di luar knowledge base | Mekanisme fallback ke agent manusia + logging pertanyaan yang gagal dijawab untuk perbaikan knowledge base |
| Performa model lokal (Qwen 7B) lebih lambat/kurang akurat dibanding LLM cloud besar | Benchmark awal & kemungkinan opsi model alternatif jika kualitas tidak memadai |
| Pengunjung mengharapkan channel lain (WhatsApp/Telegram) yang belum tersedia di MVP | Komunikasikan dengan jelas di widget bahwa web chat adalah channel resmi; evaluasi kebutuhan channel tambahan di fase 2 |
| Koneksi WebSocket widget terputus saat traffic tinggi | Mekanisme reconnect otomatis & antrIan pesan sisi klien |

## 13. Pertanyaan Terbuka

- Hardware/infrastruktur untuk hosting Ollama + Qwen 7B — on-premise, VPS, atau cloud GPU?
- Siapa saja yang akan jadi agent/admin di dashboard aspripay, dan bagaimana pembagian aksesnya?
- Dokumen/knowledge base apa saja dari aspripay yang perlu di-index pertama kali untuk RAG?
- Apakah WhatsApp/Telegram tetap direncanakan untuk fase 2, atau web chat akan jadi satu-satunya channel untuk jangka panjang?

## 14. Diagram Terkait

Diagram teknis pendukung dokumen ini dibuat sebagai file terpisah:
- **Flowchart alur percakapan** (`flowchart_alur_chatbot_aspripay.mermaid`) — alur dari pesan masuk, retrieval RAG, hingga fallback ke agent.
- **ERD** (`erd_chatbot_aspripay.mermaid`) — skema entitas database: kontak, percakapan, pesan, knowledge base, dan agent.
- **Diagram arsitektur sistem** (`architecture_chatbot_aspripay.mermaid`) — hubungan antar komponen: web widget, backend, RAG engine, vector store, LLM lokal, dan dashboard.

---
*Dokumen ini adalah draft awal. Bagian ruang lingkup, arsitektur, dan roadmap sebaiknya divalidasi lebih lanjut sebelum masuk tahap development.*
