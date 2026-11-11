import streamlit as st
import graphviz

# ตั้งค่าหน้า Streamlit
st.set_page_config(page_title="Procurement Process Flowchart Map", layout="wide")

st.title("Procurement Process Flowchart Map (SOR-to-Pay)")
st.caption("สัญลักษณ์: ■ สี่เหลี่ยม (Process) | ◆ สี่เหลี่ยมข้าวหลามตัด (Decision) | ▲▼ สามเหลี่ยม (Exception / Loopback)")

# สร้าง Graph แบบ Directed Graph (digraph) ด้วยภาษา DOT
# ใช้ rankdir="TB" (หรือปล่อยเป็นดีฟอลต์) ร่วมกับการจัดกลุ่มและการเชื่อมต่อแบบมีทิศทาง
dot = graphviz.Digraph('ProcurementFlowchart', comment='SOR-to-Pay Flowchart')

# ตั้งค่าทั่วไปสำหรับกราฟ
dot.attr(rankdir='TB', size='12,12', splines='ortho')
dot.attr('node', fontname='Angsana New, Cordia New, Arial, sans-serif', fontsize='12')

# ==========================================
# 1. นิยามรูปแบบของ Node (Styles)
# ==========================================

# Start Node
dot.node('START', 'START\n(เริ่มต้น)', shape='box', style='filled,bold', color='#2ECC71', fillcolor='#E8F8F5', fontcolor='#196F3D')

# Process Nodes (STAGE 01 - 11) - กรอบสีน้ำเงิน/ฟอนต์ปกติ
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
    dot.node(name, label, shape='box', style='filled', color='#0073C2', fillcolor='#EBF5FB', penwidth='2')

# Decision Nodes (สี่เหลี่ยมข้าวหลามตัด - สีส้ม)
decisions = {
    'DEC_01': "◆ SOR & Budget Approved?\n[ ทบทวนสเปก & งบ ]",
    'DEC_02': "◆ PR Approved?\n[ อนุมัติใบขอซื้อ ]",
    'DEC_03': "◆ Technical Pass SOR?\n[ ตรวจสเปกเทคนิค ]",
    'DEC_04': "◆ Inspection FAT/SAT Pass?\n[ ตรวจรับตามเกณฑ์ SOR ]"
}
for name, label in decisions.items():
    dot.node(name, label, shape='polygon', sides='4', orientation='45', style='filled', color='#D35400', fillcolor='#FEF9E7', penwidth='2', fontcolor='#A04000')

# Exception / Loopback Nodes (สามเหลี่ยม - สีแดง)
exceptions = {
    'REV_01': "▲ สามเหลี่ยม (Revise)\n[ แก้ไข SOR / งบประมาณ ]",
    'REJ_02': "▲ สามเหลี่ยม (Reject)\n[ ปฏิเสธ / ส่งกลับ PR ]",
    'DISQ_03': "▼ สามเหลี่ยม (Disqualify)\n[ ตัดสิทธิ์ไม่เปิดซองราคา ]",
    'CLAIM_04': "▼ สามเหลี่ยม (Claim/Penalty)\n[ แจ้งแก้ไข / เคลม / ปรับ ]"
}
for name, label in exceptions.items():
    dot.node(name, label, shape='triangle', style='filled', color='#E74C3C', fillcolor='#FDEDEC', penwidth='2', fontcolor='#C0392B')

# End Node
dot.node('END', 'END\n(สิ้นสุด)', shape='box', style='filled,bold', color='#E74C3C', fillcolor='#FDEDEC', fontcolor='#C0392B')


# ==========================================
# 2. การเชื่อมโยงเส้น (Edges & Flow)
# ==========================================

# แถวแรก (START -> STAGE 01 -> DEC_01 -> STAGE 02 -> DEC_02 -> STAGE 03)
dot.edge('START', 'STAGE_01')
dot.edge('STAGE_01', 'DEC_01')

# แถวแรก: กรณี No (ขึ้นไป Revise)
dot.edge('DEC_01', 'REV_01', label='No: ปรับปรุง', color='#E74C3C', fontcolor='#E74C3C')
dot.edge('REV_01', 'STAGE_01', style='dashed', constraint='false') # ย้อนกลับไปทำกระบวนการแรก

# แถวแรก: กรณี Yes (ไปต่อ STAGE 02)
dot.edge('DEC_01', 'STAGE_02', label='(Yes)', color='#2ECC71', fontcolor='#2ECC71')
dot.edge('STAGE_02', 'DEC_02')

# แถวแรก: PR Approved Decision
dot.edge('DEC_02', 'REJ_02', label='No: ส่งกลับ', color='#E74C3C', fontcolor='#E74C3C')
dot.edge('REJ_02', 'STAGE_01', style='dashed', constraint='false') # ย้อนกลับจุดเริ่มต้น

dot.edge('DEC_02', 'STAGE_03', label='(Yes)', color='#2ECC71', fontcolor='#2ECC71')


# แถวสอง (STAGE 03 -> STAGE 04 -> DEC_03 -> STAGE 05 -> STAGE 06 -> STAGE 07)
dot.edge('STAGE_03', 'STAGE_04')
dot.edge('STAGE_04', 'DEC_03')

# การตัดสินใจ Technical Pass
dot.edge('DEC_03', 'DISQ_03', label='No: ตกสเปก', color='#E74C3C', fontcolor='#E74C3C')
dot.edge('DEC_03', 'STAGE_05', label='(Yes)', color='#2ECC71', fontcolor='#2ECC71')

dot.edge('STAGE_05', 'STAGE_06')
dot.edge('STAGE_06', 'STAGE_07')


# แถวสาม (STAGE 07 -> STAGE 08 -> DEC_04 -> STAGE 09 -> STAGE 10 -> STAGE 11 -> END)
dot.edge('STAGE_07', 'STAGE_08')
dot.edge('STAGE_08', 'DEC_04')

# การตัดสินใจ Inspection FAT/SAT
dot.edge('DEC_04', 'CLAIM_04', label='No: ไม่ผ่านเกณฑ์', color='#E74C3C', fontcolor='#E74C3C')
dot.edge('CLAIM_04', 'STAGE_08', style='dashed', constraint='false') # เคลมแล้วกลับมาส่งมอบใหม่

dot.edge('DEC_04', 'STAGE_09', label='(Yes)', color='#2ECC71', fontcolor='#2ECC71')
dot.edge('STAGE_09', 'STAGE_10')
dot.edge('STAGE_10', 'STAGE_11')
dot.edge('STAGE_11', 'END')


# ==========================================
# 3. แสดงผลบน Streamlit
# ==========================================
st.graphviz_chart(dot, use_container_width=True)

# เพิ่มคำอธิบายการใช้งานด้านล่าง
st.info("💡 หมายเหตุ: คุณสามารถขยายภาพ ซูมเข้า-ออก หรือบันทึกภาพจากหน้าต่าง Streamlit ได้โดยตรง")
