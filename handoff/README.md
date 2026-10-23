# ย้ายโปรเจกต์ไปเครื่องใหม่

ชุดนี้เป็น snapshot ส่วนตัวของ workspace วันที่ 24 ตุลาคม 2026 รวมไฟล์โค้ด ข้อมูล ผลทดลอง และงานที่ค้างใน Git ณ เวลาสำรอง

1. ติดตั้ง Git และ Git LFS แล้ว clone repository ส่วนตัว `PGTNiiZ/Project-for-Work-private-backup` ที่ branch `transfer/2026-10-24-full` จากนั้นรัน `git lfs pull`
2. ติดตั้ง Python 3.11 แล้วติดตั้ง dependencies จาก `pyproject.toml`/`uv.lock` ในเครื่องใหม่ ไม่คัดลอก `.venv` จากเครื่องเดิม
3. ย้าย `.env.local` ด้วยช่องทางส่วนตัวแยกต่างหาก เพราะมีค่าลับและไม่อยู่ใน Git
4. ไฟล์ที่ยังไม่ได้ commit จาก 7 worktree เดิมอยู่ใต้ `handoff/worktrees/<ชื่อ worktree>/` พร้อม SHA-256 ใน `handoff/worktree_manifest.json` ให้นำไปเทียบและรวมกับงานหลักเมื่อพร้อม

Repository สาธารณะเดิมคือ `PGTNiiZ/Project-for-Work` และมี Git history ก่อน snapshot นี้ หากต้องการประวัติเดิมบนเครื่องใหม่ ให้เพิ่มเป็น remote อีกตัวแล้ว fetch ตามต้องการ งานที่มีข้อมูลส่วนบุคคลให้เก็บใน repository ส่วนตัวเท่านั้น
