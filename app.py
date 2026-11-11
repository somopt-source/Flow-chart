import streamlit as st
import graphviz

# 1. ตั้งค่าหน้า Streamlit และ Header แบบมืออาชีพ
st.set_page_config(page_title="Procurement Process Flowchart", layout="wide")

st.markdown("""
<div style='text-align: center; margin-bottom: 30px;'>
    <h2 style='color: #1B2631; margin-bottom: 5px; font-weight: bold;'>Procurement Process Flowchart (SOR-to-Pay)</h2>
    <p style='color: #7F8C8D; font-size: 18px;'>กระบวนการจัดซื้อจัดจ้างเริ่มต้นจาก Statement of Requirements (SOR)</p>
</div>
""", unsafe_allow_html=True)

# 2. สร้าง Graph และตั้งค่าพื้นฐาน
dot = graphviz.Digraph('ProcurementFlowchart', comment='SOR-to-Pay')
dot.attr(rankdir='TB', splines='ortho', nodesep='0.5', ranksep='0.6')

# ** สำคัญ: ตั้งค่าฟอนต์ให้รองรับภาษาไทยใน Graphviz **
dot.attr('node', fontname='Tahoma, Arial Unicode MS, sans-serif')
dot.attr('edge', color='#95A5A6', penwidth='3', arrowsize='0.8')

# ฟังก์ชันช่วยสร้าง HTML Label สำหรับ STAGE ให้ดูสวยงาม
def create_stage_node(node_id, stage_num, eng_title, th_title):
    label = f'''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">
    <TR><TD><FONT COLOR="#3498DB" POINT-SIZE="10"><B>{stage_num}</B></FONT></TD></TR>
    <TR><TD><FONT POINT-SIZE="12" COLOR="#1C2833"><B>{eng_title}</B></FONT></TD></TR>
    <TR><TD><FONT COLOR="#7F8C8D" POINT-SIZE="10">{th_title}</FONT></TD></TR>
    </TABLE>>'''
    dot.node(node_id, label, shape='box', style='filled,rounded', 
             color='#3498DB', fillcolor='#F4FAFF', penwidth='2.5', margin='0.15')

# ==========================================
# 3. กำหนด Nodes ทั้งหมดตามภาพ
# ==========================================

# Start & End
dot.node('START', '<<B>START</B>>', shape='box', style='filled,rounded', 
         color='#2ECC71', fillcolor='#EAFAF1', fontcolor='#1E8449', penwidth='2.5', width='1', height='0.6')
dot.node('END', '<<B>END</B>>', shape='box', style='filled,rounded', 
         color='#E74C3C', fillcolor='#FDEDEC', fontcolor='#C0392B', penwidth='2.5', width='1', height='0.6')

# แถวที่ 1
create_stage_node('STAGE_01', 'STAGE 01', 'Draft SOR', 'จัดทำข้อกำหนดความต้องการ')
dot.node('DEC_01', '<<B>SOR &<BR/>Budget<BR/>Approved?</B>>', shape='diamond', style='filled', 
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

# ==========================================
# 4. การเชื่อมโยงเส้น (บังคับให้ออกมาเป็นรูปตัว S)
# ==========================================

# กลุ่มที่ 1: วิ่งจาก ซ้าย ไป ขวา
with dot.subgraph() as s1:
    s1.attr(rank='same')
    s1.edge('START', 'STAGE_01')
    s1.edge('STAGE_01', 'DEC_01')
    s1.edge('DEC_0
