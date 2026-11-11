import streamlit as st
import graphviz

# 1. ตั้งค่าหน้า Streamlit และ Header
st.set_page_config(page_title="Procurement Process Flowchart", layout="wide")

st.markdown("""
<div style='text-align: center; margin-bottom: 30px;'>
    <h2 style='color: #1B2631; margin-bottom: 5px; font-weight: bold;'>Procurement Process Flowchart (SOR-to-Pay)</h2>
    <p style='color: #7F8C8D; font-size: 18px;'>กระบวนการจัดซื้อจัดจ้างพร้อมการจัดการกรณีไม่ผ่านอนุมัติ (Exception Handling)</p>
</div>
""", unsafe_allow_html=True)

# 2. สร้าง Graph และตั้งค่าพื้นฐาน
dot = graphviz.Digraph('ProcurementFlowchart', comment='SOR-to-Pay')
dot.attr(rankdir='TB', splines='ortho', nodesep='0.6', ranksep='0.6')
dot.attr('node', fontname='Tahoma, Arial Unicode MS, sans-serif')
dot.attr('edge', color='#95A5A6', penwidth='2.5', arrowsize='0.8', fontname='Tahoma', fontsize='11')

# ==========================================
# 3. ฟังก์ชันสำหรับสร้างรูปแบบกล่อง (Nodes)
# ==========================================

# ฟังก์ชันสร้างกล่องขั้นตอนปกติ (สีฟ้า)
def create_stage_node(node_id, stage_num, eng_title, th_title):
    eng_title = eng_title.replace("&", "&amp;")
    th_title = th_title.replace("&", "&amp;")
    label = f'''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">
    <TR><TD><FONT COLOR="#3498DB" POINT-SIZE="10"><B>{stage_num}</B></FONT></TD></TR>
    <TR><TD><FONT POINT-SIZE="12" COLOR="#1C2833"><B>{eng_title}</B></FONT></TD></TR>
    <TR><TD><FONT COLOR="#7F8C8D" POINT-SIZE="10">{th_title}</FONT></TD></TR>
    </TABLE>>'''
    dot.node(node_id, label, shape='box', style='filled,rounded', 
             color='#3498DB', fillcolor='#F4FAFF', penwidth='2.5', margin='0.15')

# ฟังก์ชันสร้างกล่องกรณีไม่ผ่าน (สีแดง/เส้นประ)
def create_exc_node(node_id, title, th_title):
    label = f'''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">
    <TR><TD><FONT COLOR="#C0392B" POINT-SIZE="11"><B>{title}</B></FONT></TD></TR>
    <TR><TD><FONT COLOR="#E74C3C" POINT-SIZE="9">{th_title}</FONT></TD></TR>
    </TABLE>>'''
    dot.node(node_id, label, shape='rect', style='filled,rounded,dashed', 
             color='#E74C3C', fillcolor='#FDEDEC', penwidth='2')

# ==========================================
# 4. กำหนด Nodes ทั้งหมด
# ==========================================

# Start & End
dot.node('START', '<<B>START</B>>', shape='box', style='filled,rounded', 
         color='#2ECC71', fillcolor='#EAFAF1', fontcolor='#1E8449', penwidth='2.5', width='1', height='0.6')
dot.node('END', '<<B>END</B>>', shape='box', style='filled,rounded', 
         color='#E74C3C', fillcolor='#FDEDEC', fontcolor='#C0392B', penwidth='2.5', width='1', height='0.6')

# แถวที่ 1
create_stage_node('STAGE_01', 'STAGE 01', 'Draft SOR', 'จัดทำข้อกำหนดความต้องการ')
dot.node('DEC_01', '<<B>SOR &amp;<BR/>Budget<BR/>Approved?</B>>', shape='diamond', style='filled', 
         color='#F39C12', fillcolor='#FEF9E7', penwidth='2.5', fontcolor='#B9770E')
create_stage_node('STAGE_02', 'STAGE 02', 'Submit PR', 'เปิดใบขอซื้อในระบบ ERP')
dot.node('DEC_02', '<<B>PR<BR/>Approved?</B>>', shape='diamond', style='filled', 
         color='#F39C12', fillcolor='#FEF9E7', penwidth='2.5', fontcolor='#B9770E')
create_stage_node('STAGE_03', 'STAGE 03', 'Issue RFQ / RFP', 'ส่งเทียบราคา/ประมูลแนบ SOR')

# แถวที่ 2
create_stage_node('STAGE_04', 'STAGE 04', 'Bids / Proposals', 'ผู้ขายยื่นข้อเสนอเทคนิค+ราคา')
dot.node('DEC_03', '<<B>Technical<BR/>Pass<BR/>SOR?</B>>', shape='diamond', style='filled', 
         color='#F39C12', fillcolor='#FEF9E7', penwidth='2.5', fontcolor='#B9770E')
create_stage_node('STAGE_05', 'STAGE 05', 'Commercial Eval', 'เจรจาต่อรอง & สรุปราคา')
create_stage_node('STAGE_06', 'STAGE 06', 'Issue PO / Contract', 'ออกใบสั่งซื้อ/สัญญาตาม SOR')
create_stage_node('STAGE_07', 'STAGE 07', 'Signed Agreement', 'คู่ค้าลงนามผูกพันสัญญา')

# แถวที่ 3
create_stage_node('STAGE_08', 'STAGE 08', 'Execution & Delivery', 'ส่งมอบงานตามงวดใน SOR')
dot.node('DEC_04', '<<B>Inspection<BR/>on<BR/>FAT/SAT<BR/>Pass?</B>>', shape='diamond', style='filled', 
         color='#F39C12', fillcolor='#FEF9E7', penwidth='2.5', fontcolor='#B9770E')
create_stage_node('STAGE_09', 'STAGE 09', '3-Way Matching', 'ตรวจ PO + ตรวจรับ + Invoice')
create_stage_node('STAGE_10', 'STAGE 10', 'Payment', 'จ่ายเงินตามงวด/เครดิตเทอม')
create_stage_node('STAGE_11', 'STAGE 11', 'KPI & Closeout', 'ประเมินผลงาน & ปิดโครงการ')

# กล่อง Exception (กรณี No)
create_exc_node('EXC_01', 'Revise SOR/Budget', 'ทบทวนสเปก/ขอเพิ่มงบ')
create_exc_node('EXC_02', 'Return to Requester', 'ตีกลับเพื่อแก้ไข PR')
create_exc_node('EXC_03', 'Disqualify / Clarify', 'ตัดสิทธิ์ / ขอคำชี้แจงเพิ่ม')
create_exc_node('EXC_04', 'Rectify / Penalty', 'แจ้งแก้ไข / ปรับตามสัญญา')

# ==========================================
# 5. การเชื่อมโยงเส้น (Main Flow & Exception Loopbacks)
# ==========================================

# กลุ่มที่ 1: วิ่งจาก ซ้าย ไป ขวา (แถวบนสุด)
with dot.subgraph() as s1:
    s1.attr(rank='same')
    s1.edge('START', 'STAGE_01')
    s1.edge('STAGE_01', 'DEC_01')
    s1.edge('DEC_01', 'STAGE_02', label=' Yes', fontcolor='#2ECC71')
    s1.edge('STAGE_02', 'DEC_02')
    s1.edge('DEC_02', 'STAGE_03', label=' Yes', fontcolor='#2ECC71')

# กลุ่มที่ 2: วิ่งจาก ขวา กลับมา ซ้าย (แถวกลาง - ลูกศรวิ่งย้อน)
with dot.subgraph() as s2:
    s2.attr(rank='same')
    s2.edge('STAGE_07', 'STAGE_06', dir='back')
    s2.edge('STAGE_06', 'STAGE_05', dir='back')
    # กำหนด label Yes บนเส้นที่วิ่งออกจาก DEC_03 ไปยัง STAGE_05
    s2.edge('STAGE_05', 'DEC_03', dir='back', label=' Yes', fontcolor='#2ECC71')
    s2.edge('DEC_03', 'STAGE_04', dir='back')

# กลุ่มที่ 3: วิ่งจาก ซ้าย ไป ขวา (แถวล่างสุด)
with dot.subgraph() as s3:
    s3.attr(rank='same')
    s3.edge('STAGE_08', 'DEC_04')
    s3.edge('DEC_04', 'STAGE_09', label=' Yes', fontcolor='#2ECC71')
    s3.edge('STAGE_09', 'STAGE_10')
    s3.edge('STAGE_10', 'STAGE_11')
    s3.edge('STAGE_11', 'END')

# ทางเชื่อมระหว่างชั้นแนวตั้ง
dot.edge('STAGE_03', 'STAGE_04', weight='100')
dot.edge('STAGE_07', 'STAGE_08', weight='100')

# ------------------------------------------
# เส้นทาง Exception (No) และการวนลูป (Loopback)
# constraint='false' ช่วยป้องกันไม่ให้ Layout หลักเสียทรง
# ------------------------------------------

# 1. No -> Revise SOR
dot.edge('DEC_01', 'EXC_01', label=' No', fontcolor='#E74C3C', color='#E74C3C', style='bold')
dot.edge('EXC_01', 'STAGE_01', style='dashed', color='#E74C3C', constraint='false')

# 2. No -> Return PR
dot.edge('DEC_02', 'EXC_02', label=' No', fontcolor='#E74C3C', color='#E74C3C', style='bold')
dot.edge('EXC_02', 'STAGE_02', style='dashed', color='#E74C3C', constraint='false')

# 3. No -> Disqualify/Clarify
dot.edge('DEC_03', 'EXC_03', label=' No', fontcolor='#E74C3C', color='#E74C3C', style='bold')
dot.edge('EXC_03', 'STAGE_04', style='dashed', color='#E74C3C', constraint='false')

# 4. No -> Rectify Defect
dot.edge('DEC_04', 'EXC_04', label=' No', fontcolor='#E74C3C', color='#E74C3C', style='bold')
dot.edge('EXC_04', 'STAGE_08', style='dashed', color='#E74C3C', constraint='false')

# ==========================================
# 6. แสดงผลบน Streamlit
# ==========================================
st.graphviz_chart(dot, use_container_width=True)
