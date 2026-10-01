# DrinkGraph Recommendation System

ระบบแนะนำเครื่องดื่มด้วย **Graph Database** พัฒนาด้วย **Streamlit + Neo4j Aura + Cypher**
แนะนำเครื่องดื่มใหม่จากคนที่ชอบเครื่องดื่มคล้ายกัน (Collaborative Filtering) และอธิบายเหตุผลของคำแนะนำได้
รองรับการ **เพิ่ม / แก้ไข / ลบ** ข้อมูล และ deploy ผ่าน **GitHub → Streamlit Community Cloud**

## 1. Graph Schema

```text
(:User {name})-[:LIKES]->(:Drink {name})
(:User {name})-[:DISLIKES]->(:Drink {name})
```

- ผู้ใช้หนึ่งคนไม่สามารถทั้งชอบและไม่ชอบเครื่องดื่มเดียวกัน (ระบบบังคับในหน้า Like / Dislike และ Manage Data)
- มี Unique Constraint บน `User.name` และ `Drink.name`

## 2. หลักการแนะนำ

```cypher
MATCH (u:User {name:$name})
MATCH (d:Drink)
WHERE NOT (u)-[:LIKES]->(d) AND NOT (u)-[:DISLIKES]->(d)
OPTIONAL MATCH (u)-[:LIKES]->(sd:Drink)<-[:LIKES]-(o:User)-[:LIKES]->(d)
WHERE o <> u
RETURN d.name, count(o) AS score
ORDER BY score DESC
```

1. หาเครื่องดื่มที่ผู้ใช้ชอบ
2. หาผู้ใช้คนอื่นที่ชอบเครื่องดื่มเดียวกัน
3. ดูเครื่องดื่มอื่นที่คนกลุ่มนั้นชอบ (ตัดที่ผู้ใช้ชอบหรือไม่ชอบอยู่แล้ว)
4. **score = จำนวนเส้นทาง** ยิ่งมีเส้นทางมากยิ่งแนะนำน้ำหนักมาก

ตัวอย่าง ผู้ใช้ Guy (ชอบ Bubble Milk Tea, Cocoa / ไม่ชอบ Americano)

| อันดับ | เครื่องดื่ม | score | เหตุผล |
|---|---|---|---|
| 1 | Green Tea | 4 | May, Min, Nut ชอบด้วย |
| 2 | Fresh Milk | 3 | Fah, Min ชอบด้วย |
| 3 | มัทฉะLatte | 1 | Nut ชอบด้วย |

## 3. เมนูในแอป

| เมนู | หน้าที่ |
|---|---|
| Dashboard | สรุปจำนวน User / Drink / LIKES / DISLIKES, กราฟความนิยม, ความชอบของผู้ใช้ |
| Recommendations | เครื่องดื่มที่แนะนำ พร้อม score และเหตุผล |
| Drink Search | ค้นหาเครื่องดื่ม ดูจำนวนคนที่ชอบ/ไม่ชอบ |
| Like / Dislike | ตั้งค่า ชอบ / ไม่ชอบ / ล้างความรู้สึก ให้ผู้ใช้กับเครื่องดื่ม |
| Graph Explorer | วาดกราฟรอบผู้ใช้ (เส้นเขียว = LIKES, เส้นแดงประ = DISLIKES) |
| Manage Data (CRUD) | เพิ่ม/เปลี่ยนชื่อ/ลบ ผู้ใช้และเครื่องดื่ม (พร้อมอัปโหลด/เปลี่ยน/ลบรูป), แก้ความชอบทั้งชุด |
| Admin / Setup | สร้าง Constraint + ข้อมูลตัวอย่าง (กดซ้ำได้), ล้างข้อมูล User/Drink |

## 3.1 รูปเครื่องดื่ม

ทุกรูปถูกครอปกลางภาพเป็นสี่เหลี่ยมจัตุรัส 400×400 พิกเซลให้เท่ากันอัตโนมัติ ลำดับการเลือกรูป

1. รูปที่อัปโหลดผ่านหน้า **Manage Data → เครื่องดื่ม** (เก็บใน Neo4j เป็นคุณสมบัติ `image` ของ node Drink จึงไม่หายเมื่อแอปรีสตาร์ท)
2. ไฟล์ในโฟลเดอร์ `images/photos/` หรือ `images/` (ชื่อไฟล์ไม่สนตัวพิมพ์ใหญ่เล็ก เช่น `Latte.jpg`, `green_tea.jpg`; `มัทฉะLatte` ใช้ไฟล์ `Matcha_Latte.jpg`)
3. ภาพวาดไอคอน (.png) ในโฟลเดอร์ `images/`

## 4. โครงสร้างไฟล์

```text
drink_graph/
├── app.py              # หน้าจอ Streamlit
├── neo4j_service.py    # Cypher + การเชื่อมต่อ Neo4j (แยกจาก UI)
├── requirements.txt
└── README.md
```

## 5. สร้าง Neo4j Aura

1. สร้าง AuraDB instance
2. เก็บ Connection URI (รูปแบบ `neo4j+s://xxxxxxxx.databases.neo4j.io`), username และ password
3. ตรวจว่า instance อยู่ในสถานะ **Running** (Aura ฟรีจะถูก pause ถ้าไม่ได้ใช้นาน)

## 6. รันในเครื่อง

```bash
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

สร้างไฟล์ `.streamlit/secrets.toml` (อย่า commit ไฟล์นี้)

```toml
[neo4j]
uri = "neo4j+s://xxxxxxxx.databases.neo4j.io"
username = "neo4j"
password = "รหัสผ่านจริง"
# database = "..."   # ไม่ต้องใส่ก็ได้ จะใช้ database หลักของ instance
```

จากนั้นรัน

```bash
streamlit run app.py
```

## 7. ครั้งแรกที่เปิดระบบ

1. เข้าเมนู **Admin / Setup**
2. กด **สร้าง Constraint + Demo Data** (ใช้ `MERGE` จึงกดซ้ำได้)
3. ทดลองเมนู Dashboard, Recommendations และ Manage Data

ข้อมูลตัวอย่างมี 10 ผู้ใช้ (Guy, May, Nut, Min, Ball, Fah, Beam, Praew, Ton, Fon), 10 เครื่องดื่ม, 29 LIKES และ 10 DISLIKES

## 8. Deploy: GitHub → Streamlit Community Cloud

1. สร้าง GitHub repository แล้ว push ไฟล์ทั้งหมด **ยกเว้น `.streamlit/secrets.toml`**
2. เข้า Streamlit Community Cloud → Create app → เลือก repository, branch และ entrypoint = `app.py`
3. ที่ Advanced settings → Secrets ใส่ค่าเดียวกับหัวข้อ 6
4. กด Deploy

## 9. การแก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| `DatabaseNotFound ... database 'neo4j' does not exist` | instance ใช้ชื่อ database อื่น ให้ลบบรรทัด `database` ออกจาก Secrets หรือใส่ชื่อจริงของ instance |
| เชื่อมต่อไม่สำเร็จ / timeout | ตรวจ `uri` และ `password` ใน Secrets, ตรวจว่า instance ไม่ถูก pause |
| ไม่มีผู้ใช้ให้เลือก | ไปที่ Admin / Setup แล้วกดสร้างข้อมูลตัวอย่าง |
| ปุ่มล้างข้อมูลลบอะไรบ้าง | ลบเฉพาะ node `:User` และ `:Drink` เท่านั้น ข้อมูลอื่นใน database ไม่ถูกแตะ |

## 10. แนวทางต่อยอด

เพิ่มหมวดเครื่องดื่ม (กาแฟ/ชา/นม), ให้คะแนนความชอบ 1–5, Login, Graph Data Science (similarity, PageRank, community detection) และวัดผลด้วย Precision@K / Recall@K