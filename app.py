import streamlit as st
import graphviz

# ==========================================
# 1. ตั้งค่าหน้า Streamlit
# ==========================================
st.set_page_config(page_title="Interactive Procurement Flow", layout="wide")

st.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h2 style='color: #1B2631; margin-bottom: 5px; font-weight: bold;'>Interactive Procurement Flowchart</h2>
    <p style='color: #7F8C8D; font-size: 16px;'>ระบบจำลองขั้นตอนการจัดซื้อจัดจ้าง (คลิกปุ่มด้านขวาเพื่อดูการไหลของกระบวนการ)</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฐานข้อมูลขั้นตอน (Flow Logic)
# ==========================================
FLOW_DATA = {
    'START': {'title': 'เริ่มต้น', 'type': 'start', 'next': 'STAGE_01'},
    'STAGE_01': {'title': 'STAGE 01: Draft SOR', 'desc': 'หน่วยงานจัดทำข้อกำหนดความต้องการ (SOR) และงบประมาณ', 'type': 'stage', 'next': 'DEC_01'},
    'DEC_01': {'title': 'ตรวจสอบ SOR & Budget', 'desc': 'สเปกและงบประมาณเหมาะสมหรือไม่?', 'type': 'decision', 'yes': 'STAGE_02', 'no': 'EXC_01'},
    'EXC_01': {'title': 'ทบทวนสเปก/งบประมาณ', 'desc': 'ปรับปรุง SOR หรือขออนุมัติงบประมาณเพิ่มเติม', 'type': 'exception', 'next': 'STAGE_01'},
    
    'STAGE_02': {'title': 'STAGE 02: Submit PR', 'desc': 'เปิดใบขอซื้อ (PR) ในระบบ ERP', 'type': 'stage', 'next': 'DEC_02'},
    'DEC_02': {'title': 'อนุมัติ PR', 'desc': 'ผู้มีอำนาจอนุมัติใบขอซื้อหรือไม่?', 'type': 'decision', 'yes': 'STAGE_03', 'no': 'EXC_02'},
    'EXC_02': {'title': 'ตีกลับเพื่อแก้ไข PR', 'desc': 'ส่งคืนให้ผู้ขอซื้อแก้ไขข้อมูลในระบบ', 'type': 'exception', 'next': 'STAGE_02'},
    
    'STAGE_03': {'title': 'STAGE 03: Issue RFQ / RFP', 'desc': 'จัดซื้อส่งเอกสารเชิญชวนเสนอราคา/ประมูล', 'type': 'stage', 'next': 'STAGE_04'},
    'STAGE_04': {'title': 'STAGE 04: Bids / Proposals', 'desc': 'ผู้ขายยื่นซองข้อเสนอทางเทคนิคและราคา', 'type': 'stage', 'next': 'DEC_03'},
    
    'DEC_03': {'title': 'ตรวจสอบคุณสมบัติทางเทคนิค', 'desc': 'ผู้ขายผ่านเกณฑ์เทคนิคตาม SOR หรือไม่?', 'type': 'decision', 'yes': 'STAGE_05', 'no': 'EXC_03'},
    'EXC_03': {'title': 'ตัดสิทธิ์ / ขอคำชี้แจง', 'desc': 'ตัดสิทธิ์ผู้เสนอราคา หรือขอเอกสารเพิ่มเติม', 'type': 'exception', 'next': 'STAGE_04'},
    
    'STAGE_05': {'title': 'STAGE 05: Commercial Eval', 'desc': 'เปิดซองราคา เจรจาต่อรอง และสรุปผล', 'type': 'stage', 'next': 'STAGE_06'},
    'STAGE_06': {'title': 'STAGE 06: Issue PO / Contract', 'desc': 'ออกใบสั่งซื้อหรือร่างสัญญา', 'type': 'stage', 'next': 'STAGE_07'},
    'STAGE_07': {'title': 'STAGE 07: Signed Agreement', 'desc': 'คู่ค้าลงนามผูกพันตามสัญญา', 'type': 'stage', 'next': 'STAGE_08'},
    'STAGE_08': {'title': 'STAGE 08: Execution & Delivery', 'desc': 'คู่ค้าดำเนินงานและส่งมอบตามงวด', 'type': 'stage', 'next': 'DEC_04'},
    
    'DEC_04': {'title': 'ตรวจรับงาน (FAT/SAT)', 'desc': 'ผลการตรวจรับผ่านตามเกณฑ์หรือไม่?', 'type': 'decision', 'yes': 'STAGE_09', 'no': 'EXC_04'},
    'EXC_04': {'title': 'แจ้งแก้ไข / ปรับตามสัญญา', 'desc': 'ให้คู่ค้าแก้ไขงาน หรือดำเนินการปรับล่าช้า', 'type': 'exception', 'next': 'STAGE_08'},
    
    'STAGE_09': {'title': 'STAGE 09: 3-Way Matching', 'desc': 'บัญชีตรวจสอบ PO, ใบตรวจรับ และ Invoice', 'type': 'stage', 'next': 'STAGE_10'},
    'STAGE_10': {'title': 'STAGE 10: Payment', 'desc': 'จ่ายเงินตามเครดิตเทอม', 'type': 'stage', 'next': 'STAGE_11'},
    'STAGE_11': {'title': 'STAGE 11: KPI & Closeout', 'desc': 'ประเมินผลงานคู่ค้าและปิดโครงการ', 'type': 'stage', 'next': 'END'},
    'END': {'title': 'สิ้นสุดกระบวนการ', 'desc': 'Procurement Cycle Completed', 'type': 'end'}
}

# กำหนด State เริ่มต้น
if 'current_node' not in st.session_state:
    st.session_state.current_node = 'START'

# ==========================================
# 3. ฟังก์ชันวาดกราฟ (รับค่าสถานะปัจจุบันเพื่อไฮไลท์)
# ==========================================
def generate_graph(active_node):
    dot = graphviz.Digraph('ProcurementFlow', comment='Interactive Flow')
    dot.attr(rankdir='TB', splines='ortho', nodesep='0.4', ranksep='0.6')
    dot.attr('node', fontname='Tahoma, sans-serif')
    dot.attr('edge', color='#BDC3C7', penwidth='2')

    # ฟังก์ชันช่วยสร้างกล่องแบบมีสีไฮไลท์
    def get_node_style(node_id, base_color, fill_color, shape, style):
        is_active = (node_id == active_node)
        # ถ้า Active ให้เปลี่ยนกรอบเป็นสีเหลืองทองหนาๆ และพื้นหลังสว่าง
        pw = '4' if is_active else '2'
        c = '#F1C40F' if is_active else base_color
        f = '#FCF3CF' if is_active else fill_color
        return {'shape': shape, 'style': style, 'color': c, 'fillcolor': f, 'penwidth': pw}

    # สร้าง Nodes ทั้งหมด
    dot.node('START', 'START', **get_node_style('START', '#2ECC71', '#EAFAF1', 'box', 'filled,rounded'))
    dot.node('END', 'END', **get_node_style('END', '#E74C3C', '#FDEDEC', 'box', 'filled,rounded'))

    stages = [
        ('STAGE_01', 'STAGE 01\nDraft SOR'), ('STAGE_02', 'STAGE 02\nSubmit PR'),
        ('STAGE_03', 'STAGE 03\nIssue RFQ/RFP'), ('STAGE_04', 'STAGE 04\nBids/Proposals'),
        ('STAGE_05', 'STAGE 05\nCommercial Eval'), ('STAGE_06', 'STAGE 06\nIssue PO/Contract'),
        ('STAGE_07', 'STAGE 07\nSigned Agreement'), ('STAGE_08', 'STAGE 08\nExecution & Delivery'),
        ('STAGE_09', 'STAGE 09\n3-Way Matching'), ('STAGE_10', 'STAGE 10\nPayment'),
        ('STAGE_11', 'STAGE 11\nKPI & Closeout')
    ]
    for s_id, s_lbl in stages:
        dot.node(s_id, s_lbl, **get_node_style(s_id, '#3498DB', '#F4FAFF', 'box', 'filled,rounded'))

    decs = [
        ('DEC_01', 'SOR/Budget\nApproved?'), ('DEC_02', 'PR\nApproved?'),
        ('DEC_03', 'Technical\nPass?'), ('DEC_04', 'Inspection\nPass?')
    ]
    for d_id, d_lbl in decs:
        dot.node(d_id, d_lbl, **get_node_style(d_id, '#F39C12', '#FEF9E7', 'diamond', 'filled'))

    excs = [
        ('EXC_01', 'Revise SOR'), ('EXC_02', 'Return PR'),
        ('EXC_03', 'Disqualify'), ('EXC_04', 'Penalty/Rectify')
    ]
    for e_id, e_lbl in excs:
        dot.node(e_id, e_lbl, **get_node_style(e_id, '#E74C3C', '#FDEDEC', 'rect', 'filled,dashed'))

    # วาดเส้น Main Flow
    with dot.subgraph() as s1:
        s1.attr(rank='same')
        s1.edges([('START', 'STAGE_01'), ('STAGE_01', 'DEC_01'), ('DEC_01', 'STAGE_02'), ('STAGE_02', 'DEC_02'), ('DEC_02', 'STAGE_03')])
    
    with dot.subgraph() as s2:
        s2.attr(rank='same')
        s2.edge('STAGE_07', 'STAGE_06', dir='back')
        s2.edge('STAGE_06', 'STAGE_05', dir='back')
        s2.edge('STAGE_05', 'DEC_03', dir='back')
        s2.edge('DEC_03', 'STAGE_04', dir='back')

    with dot.subgraph() as s3:
        s3.attr(rank='same')
        s3.edges([('STAGE_08', 'DEC_04'), ('DEC_04', 'STAGE_09'), ('STAGE_09', 'STAGE_10'), ('STAGE_10', 'STAGE_11'), ('STAGE_11', 'END')])

    dot.edge('STAGE_03', 'STAGE_04', weight='100')
    dot.edge('STAGE_07', 'STAGE_08', weight='100')

    # วาดเส้น Exception (No)
    dot.edge('DEC_01', 'EXC_01', label='No', color='#E74C3C', fontcolor='#E74C3C')
    dot.edge('EXC_01', 'STAGE_01', style='dashed', constraint='false', color='#E74C3C')
    
    dot.edge('DEC_02', 'EXC_02', label='No', color='#E74C3C', fontcolor='#E74C3C')
    dot.edge('EXC_02', 'STAGE_02', style='dashed', constraint='false', color='#E74C3C')
    
    dot.edge('DEC_03', 'EXC_03', label='No', color='#E74C3C', fontcolor='#E74C3C')
    dot.edge('EXC_03', 'STAGE_04', style='dashed', constraint='false', color='#E74C3C')
    
    dot.edge('DEC_04', 'EXC_04', label='No', color='#E74C3C', fontcolor='#E74C3C')
    dot.edge('EXC_04', 'STAGE_08', style='dashed', constraint='false', color='#E74C3C')

    # ใส่ Label Yes
    dot.edge('DEC_01', 'STAGE_02', label='Yes', fontcolor='#2ECC71')
    dot.edge('DEC_02', 'STAGE_03', label='Yes', fontcolor='#2ECC71')
    dot.edge('STAGE_05', 'DEC_03', dir='back', label='Yes', fontcolor='#2ECC71')
    dot.edge('DEC_04', 'STAGE_09', label='Yes', fontcolor='#2ECC71')

    return dot

# ==========================================
# 4. ออกแบบ UI (แบ่งซ้าย-ขวา)
# ==========================================
col1, col2 = st.columns([7, 3])

# ดึงข้อมูลโหนดปัจจุบัน
current_node_id = st.session_state.current_node
node_info = FLOW_DATA.get(current_node_id, {})

with col1:
    # แสดงกราฟ
    st.graphviz_chart(generate_graph(current_node_id), use_container_width=True)

with col2:
    st.markdown("### 📍 แผงควบคุม (Control Panel)")
    st.info(f"**สถานะปัจจุบัน:**\n### {node_info.get('title', '')}")
    if 'desc' in node_info:
        st.write(f"📝 *{node_info['desc']}*")
    
    st.markdown("---")
    
    # สร้างปุ่มกดตามประเภทของกล่อง
    node_type = node_info.get('type')
    
    if node_type == 'decision':
        st.write("**โปรดตัดสินใจ:**")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ ผ่าน / อนุมัติ", use_container_width=True):
                st.session_state.current_node = node_info['yes']
                st.rerun()
        with col_no:
            if st.button("❌ ไม่อนุมัติ / ไม่ผ่าน", use_container_width=True):
                st.session_state.current_node = node_info['no']
                st.rerun()
                
    elif node_type in ['start', 'stage', 'exception']:
        if st.button("➡️ ดำเนินการต่อ (Next)", type="primary", use_container_width=True):
            st.session_state.current_node = node_info['next']
            st.rerun()
            
    elif node_type == 'end':
        st.success("🎉 กระบวนการเสร็จสมบูรณ์!")
        if st.button("🔄 เริ่มต้นกระบวนการใหม่", use_container_width=True):
            st.session_state.current_node = 'START'
            st.rerun()

    st.caption("หมายเหตุ: กล่องที่ถูกไฮไลท์ (สีเหลือง) คือขั้นตอนที่ระบบกำลังทำงานอยู่")
