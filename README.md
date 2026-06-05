# back-skills

Agent skills สำหรับงาน horoacademy ติดตั้งผ่าน [`npx skills`](https://github.com/vercel-labs/skills)

## ติดตั้ง

```bash
npx skills add thannnp/back-skills
```

คำสั่งนี้จะสแกนหา skill ทั้งหมดใน repo แล้วขึ้นเมนูให้เลือกติดตั้ง

ดูรายการ skill ที่มีโดยยังไม่ติดตั้ง:

```bash
npx skills add thannnp/back-skills --list
```

ติดตั้งเฉพาะ skill ที่ต้องการ:

```bash
npx skills add thannnp/back-skills --skill horo-db
```

## Skills ที่มี

| Skill | หน้าที่ |
|---|---|
| `horo-db` | ผู้ช่วยตอบคำถามเรื่องโครงสร้างและความสัมพันธ์ของฐานข้อมูล horoacademy สองตัว (`horoacademy-backoffice` และ `horoacademy-wpe-service`) — มีตารางอะไร, column อะไร, เชื่อมกันยังไง, cross-DB references, polymorphic relations |

## โครงสร้าง repo

```
back-skills/
└── skills/
    └── horo-db/
        ├── SKILL.md                              # instruction (อังกฤษ, ตอบผู้ใช้เป็นไทย)
        ├── HORO_BACKOFFICE_DATABASE_DIAGRAM.md   # Mermaid ER diagram — backoffice
        └── WPE_SERVICE_DATABASE_DIAGRAM.md       # Mermaid ER diagram — wpe-service
```

เพิ่ม skill ใหม่ได้โดยสร้างโฟลเดอร์ `skills/<ชื่อ>/SKILL.md` แล้ว `npx skills` จะเจอเอง
