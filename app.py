import streamlit as st
import graphviz

# ตั้งค่าหน้า Streamlit
st.set_page_config(page_title="Procurement Process Flowchart Map", layout="wide")

st.title("Procurement Process Flowchart Map (SOR-to-Pay)")
st.caption("สัญลักษณ์: ■ สี่เหลี่ยม (Process) | ◆ สี่เหลี่ยมขนมเปียกปูน (Decision) | ▲▼ สามเหลี่ยม (Exception / Loopback)")

# สร้าง Graph แบบ Directed Graph
dot = graphviz.Digraph('ProcurementFlowchart', comment='SOR-to-Pay Flowchart')

# ตั้งค่าทั่วไปสำหรับกราฟ (จัดเรียงบนลงล่าง, เส้นแบบหักมุม)
dot.attr(rankdir='TB', splines='ortho', nodesep='0.5', ranksep='0.5')
# แนะนำให้ใช้ฟอนต์ Tahoma หรือ Arial เพื่อให้ภาษาไทยไม่เพี้ยน
dot.attr('node', fontname='Tahoma, Arial, sans-serif', fontsize='12')

# ==========================================
# 1. นิยามรูปแบบของ Node (Styles)
# ==========================================

# Start Node
dot.node('START', 'START\n(เริ่มต้น)', shape='box', style='filled,bold', color='#2ECC71', fillcolor='#E8F8F5', fontcolor='#196F3D')

# Process Nodes (STAGE 01 - 11) - กรอบสีน้ำเงิน
stages = {
    'STAGE_01': "■ STAGE 01\nDraft SOR\nจัดทำข้อกำหนดความต้องการ",
    'STAGE_02': "■ STAGE 02\nSubmit PR in ERP\nเปิดใบขอซื้อในระบบ ERP",
    'STAGE_03': "■ STAGE 03\nIssue RFQ / RFP with SOR\nส่งเทียบราคา/ประมูลแนบ SOR",
    'STAGE_04': "■ STAGE 04\nBids & Proposals\nผู้ขายยื่นซองเทคนิค+ราคา",
    'STAGE_05': "■ STAGE 05\nCommercial Eval\nเจรจาต่อรอง & สรุปราคา",
    'STAGE_06': "■ STAGE 06\nIssue PO / Contract\nออกใบสั่งซื้อ/สัญญาตาม SOR",
    'STAGE_07': "■ STAGE 07\nSigned Agreement\nคู่ค้าลงนามสัญญาผูกพัน",
    'STAGE_08': "■ STAGE 08\nExecution & Delivery\nดำเนินงาน / ส่งมอบตามงวด",
    'STAGE_09': "■ STAGE 09\n3-Way Matching\nตรวจ PO + ตรวจรับ + Invoice",
    'STAGE_10': "■ STAGE 10\nPayment\nโอนจ่ายเงินตามงวด/เครดิต",
    'STAGE_11': "■ STAGE 11\nKPI & Closeout\nประเมินผลงาน & ปิดโครงการ"
}
for name, label in stages.items():
    dot.node(name, label, shape='box', style='filled', color='#0073C2', fillcolor='#EBF5FB', penwidth='2', margin='0.2')

# Decision Nodes (สี่เหลี่ยมขนมเปียกปูน - ใช้ shape='diamond') 
# เพิ่ม \n ตัดบรรทัดเพื่อให้ขนมเปียกปูนไม่ยืดออกข้างมากเกินไป
decisions = {
    'DEC_01': "◆ SOR & Budget\nApproved?\n[ ทบทวนสเปก & งบ ]",
    'DEC_02': "◆ PR Approved?\n[ อนุมัติใบขอซื้อ ]",
    'DEC_03': "◆ Technical\nPass SOR?\n[ ตรวจสเปกเทคนิค ]",
    'DEC_04': "◆ Inspection\nFAT/SAT Pass?\n[ ตรวจรับตามเกณฑ์ ]"
}
for name, label in decisions.items():
    dot.node(name, label, shape='diamond', style='filled', color='#D35400', fillcolor='#FEF9E7', penwidth='2', fontcolor='#A04000')

# Exception / Loopback Nodes (สามเหลี่ยม - ใช้ shape='triangle')
# เพิ่ม \n ตัดบรรทัดเพื่อให้สามเหลี่ยมสมดุล
exceptions = {
    'REV_01': "▲ (Revise)\n[ แก้ไข SOR /\nงบประมาณ ]",
    'REJ_02': "▲ (Reject)\n[ ปฏิเสธ /\nส่งกลับ PR ]",
    'DISQ_03': "▼ (Disqualify)\n[ ตัดสิทธิ์\nไม่เปิดซองราคา ]",
    'CLAIM_04': "▼ (Claim/Penalty)\n[ แจ้งแก้ไข /\nเคลม / ปรับ ]"
}
for name, label in exceptions.items():
    dot.node(name, label, shape='triangle', style='filled', color='#E74C3C', fillcolor='#FDEDEC', penwidth='2', fontcolor='#C0392B')

# End Node
dot.node('END', 'END\n(สิ้นสุด)', shape='box', style='filled,bold', color='#E74C3C', fillcolor='#FDEDEC', fontcolor='#C0392B')


# ==========================================
# 2. การเชื่อมโยงเส้น (Edges & Flow)
# ==========================================

# กระบวนการหลัก
dot.edge('START', 'STAGE_01')
dot.edge('STAGE_01', 'DEC_01')

# DEC_01 (SOR & Budget)
dot.edge('DEC_01', 'REV_01', label='No: ปรับปรุง', color='#E74C3C', fontcolor='#E74C3C')
dot.edge('REV_01', 'STAGE_01', style='dashed', constraint='false')
dot.edge('DEC_01', 'STAGE_02', label='(Yes)', color='#2ECC71', fontcolor='#2ECC71')

# DEC_02 (PR Approved)
dot.edge('STAGE_02', 'DEC_02')
dot.edge('DEC_02', 'REJ_02', label='No: ส่งกลับ', color='#E74C3C', fontcolor='#E74C3C')
dot.edge('REJ_02', 'STAGE_01', style='dashed', constraint='false')
dot.edge('DEC_02', 'STAGE_03', label='(Yes)', color='#2ECC71', fontcolor='#2ECC71')

# STAGE 03 ไป 04
dot.edge('STAGE_03', 'STAGE_04')
dot.edge('STAGE_04', 'DEC_03')

# DEC_03 (Technical Pass)
dot.edge('DEC_03', 'DISQ_03', label='No: ตกสเปก', color='#E74C3C', fontcolor='#E74C3C')
dot.edge('DEC_03', 'STAGE_05', label='(Yes)', color='#2ECC71', fontcolor='#2ECC71')

# STAGE 05 ไป 08
dot.edge('STAGE_05', 'STAGE_06')
dot.edge('STAGE_06', 'STAGE_07')
dot.edge('STAGE_07', 'STAGE_08')
dot.edge('STAGE_08', 'DEC_04')

# DEC_04 (Inspection)
dot.edge('DEC_04', 'CLAIM_04', label='No: ไม่ผ่านเกณฑ์', color='#E74C3C', fontcolor='#E74C3C')
dot.edge('CLAIM_04', 'STAGE_08', style='dashed', constraint='false')
dot.edge('DEC_04', 'STAGE_09', label='(Yes)', color='#2ECC71', fontcolor='#2ECC71')

# STAGE 09 ไปสิ้นสุด
dot.edge('STAGE_09', 'STAGE_10')
dot.edge('STAGE_10', 'STAGE_11')
dot.edge('STAGE_11', 'END')


# ==========================================
# 3. แสดงผลบน Streamlit
# ==========================================
st.graphviz_chart(dot, use_container_width=True)
