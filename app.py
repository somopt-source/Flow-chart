import streamlit as st
import graphviz
import pandas as pd
import io

# ==========================================
# 1. ตั้งค่าหน้า Streamlit (ย้ายแผงควบคุมไป Sidebar)
# ==========================================
st.set_page_config(
    page_title="Interactive Procurement Flow", 
    layout="wide",
    initial_sidebar_state="expanded" # ตั้งค่าให้ Sidebar เปิดเป็นค่าเริ่มต้น
)

st.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h2 style='color: #1B2631; margin-bottom: 5px; font-weight: bold;'>Interactive Procurement Flowchart (SOR-to-Pay)</h2>
    <p style='color: #7F8C8D; font-size: 16px;'>ระบบจำลองขั้นตอนการจัดซื้อจัดจ้าง สามารถปรับเปลี่ยนมุมมองได้</p>
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

if 'current_node' not in st.session_state:
    st.session_state.current_node = 'START'

# ==========================================
# 3. ฟังก์ชันวาดกราฟ (รองรับ แนวนอน และ แนวตั้ง)
# ==========================================
def generate_graph(active_node, layout_mode):
    dot = graphviz.Digraph('ProcurementFlow', comment='Interactive Flow')
    
    dot.attr(rankdir='TB', splines='ortho', nodesep='0.4', ranksep='0.6')
    dot.attr('node', fontname='Tahoma, Arial Unicode MS, sans-serif')
    dot.attr('edge', color='#BDC3C7', penwidth='2', fontname='Tahoma', fontsize='10')

    def get_node_style(node_id, base_color, fill_color, shape, style):
        is_active = (node_id == active_node)
        pw = '4' if is_active else '2'
        c = '#F1C40F' if is_active else base_color
        f = '#FCF3CF' if is_active else fill_color
        return {'shape': shape, 'style': style, 'color': c, 'fillcolor': f, 'penwidth': pw}

    dot.node('START', '<<B>START</B>>', **get_node_style('START', '#2ECC71', '#EAFAF1', 'box', 'filled,rounded'))
    dot.node('END', '<<B>END</B>>', **get_node_style('END', '#E74C3C', '#FDEDEC', 'box', 'filled,rounded'))

    def create_stage_node(node_id, stage_num, eng_title, th_title):
        is_active = (node_id == active_node)
        pw = '4' if is_active else '2.5'
        c = '#F1C40F' if is_active else '#3498DB'
        f = '#FCF3CF' if is_active else '#F4FAFF'
        
        eng_title = eng_title.replace("&", "&amp;")
        th_title = th_title.replace("&", "&amp;")
        
        label = f'''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">
        <TR><TD><FONT COLOR="{c}" POINT-SIZE="10"><B>{stage_num}</B></FONT></TD></TR>
        <TR><TD><FONT POINT-SIZE="12" COLOR="#1C2833"><B>{eng_title}</B></FONT></TD></TR>
        <TR><TD><FONT COLOR="#7F8C8D" POINT-SIZE="10">{th_title}</FONT></TD></TR>
        </TABLE>>'''
        dot.node(node_id, label, shape='box', style='filled,rounded', color=c, fillcolor=f, penwidth=pw, margin='0.15')

    create_stage_node('STAGE_01', 'STAGE 01', 'Draft SOR', 'จัดทำข้อกำหนดความต้องการ')
    create_stage_node('STAGE_02', 'STAGE 02', 'Submit PR', 'เปิดใบขอซื้อในระบบ ERP')
    create_stage_node('STAGE_03', 'STAGE 03', 'Issue RFQ / RFP', 'ส่งเทียบราคา/ประมูลแนบ SOR')
    create_stage_node('STAGE_04', 'STAGE 04', 'Bids / Proposals', 'ผู้ขายยื่นข้อเสนอเทคนิค+ราคา')
    create_stage_node('STAGE_05', 'STAGE 05', 'Commercial Eval', 'เจรจาต่อรอง & สรุปราคา')
    create_stage_node('STAGE_06', 'STAGE 06', 'Issue PO / Contract', 'ออกใบสั่งซื้อ/สัญญาตาม SOR')
    create_stage_node('STAGE_07', 'STAGE 07', 'Signed Agreement', 'คู่ค้าลงนามผูกพันสัญญา')
    create_stage_node('STAGE_08', 'STAGE 08', 'Execution & Delivery', 'ส่งมอบงานตามงวดใน SOR')
    create_stage_node('STAGE_09', 'STAGE 09', '3-Way Matching', 'ตรวจ PO + ตรวจรับ + Invoice')
    create_stage_node('STAGE_10', 'STAGE 10', 'Payment', 'จ่ายเงินตามงวด/เครดิตเทอม')
    create_stage_node('STAGE_11', 'STAGE 11', 'KPI & Closeout', 'ประเมินผลงาน & ปิดโครงการ')

    decs = [
        ('DEC_01', '<<B>SOR &amp;<BR/>Budget<BR/>Approved?</B>>'), 
        ('DEC_02', '<<B>PR<BR/>Approved?</B>>'),
        ('DEC_03', '<<B>Technical<BR/>Pass<BR/>SOR?</B>>'), 
        ('DEC_04', '<<B>Inspection<BR/>on<BR/>FAT/SAT<BR/>Pass?</B>>')
    ]
    for d_id, d_lbl in decs:
        dot.node(d_id, d_lbl, **get_node_style(d_id, '#F39C12', '#FEF9E7', 'diamond', 'filled'))

    excs = [
        ('EXC_01', 'Revise SOR', 'ทบทวนสเปก/ขอเพิ่มงบ'), 
        ('EXC_02', 'Return to Requester', 'ตีกลับเพื่อแก้ไข PR'),
        ('EXC_03', 'Disqualify / Clarify', 'ตัดสิทธิ์ / ขอคำชี้แจงเพิ่ม'), 
        ('EXC_04', 'Rectify / Penalty', 'แจ้งแก้ไข / ปรับตามสัญญา')
    ]
    for e_id, e_title, e_th in excs:
        is_active = (e_id == active_node)
        pw = '4' if is_active else '2'
        c = '#F1C40F' if is_active else '#E74C3C'
        f = '#FCF3CF' if is_active else '#FDEDEC'
        label = f'''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">
        <TR><TD><FONT COLOR="{c}" POINT-SIZE="11"><B>{e_title}</B></FONT></TD></TR>
        <TR><TD><FONT COLOR="#E74C3C" POINT-SIZE="9">{e_th}</FONT></TD></TR>
        </TABLE>>'''
        dot.node(e_id, label, shape='rect', style='filled,rounded,dashed', color=c, fillcolor=f, penwidth=pw)

    # ตรรกะการลากเส้น
    if layout_mode == "แนวนอน (S-Curve)":
        with dot.subgraph() as s1:
            s1.attr(rank='same')
            s1.edges([('START', 'STAGE_01'), ('STAGE_01', 'DEC_01')])
            s1.edge('DEC_01', 'STAGE_02', label=' Yes', fontcolor='#2ECC71')
            s1.edges([('STAGE_02', 'DEC_02')])
            s1.edge('DEC_02', 'STAGE_03', label=' Yes', fontcolor='#2ECC71')
        
        with dot.subgraph() as s2:
            s2.attr(rank='same')
            s2.edge('STAGE_07', 'STAGE_06', dir='back')
            s2.edge('STAGE_06', 'STAGE_05', dir='back')
            s2.edge('STAGE_05', 'DEC_03', dir='back', label=' Yes', fontcolor='#2ECC71')
            s2.edge('DEC_03', 'STAGE_04', dir='back')

        with dot.subgraph() as s3:
            s3.attr(rank='same')
            s3.edge('STAGE_08', 'DEC_04')
            s3.edge('DEC_04', 'STAGE_09', label=' Yes', fontcolor='#2ECC71')
            s3.edges([('STAGE_09', 'STAGE_10'), ('STAGE_10', 'STAGE_11'), ('STAGE_11', 'END')])

        dot.edge('STAGE_03', 'STAGE_04', weight='100')
        dot.edge('STAGE_07', 'STAGE_08', weight='100')

    else:
        # แนวตั้ง
        dot.edge('START', 'STAGE_01')
        dot.edge('STAGE_01', 'DEC_01')
        dot.edge('DEC_01', 'STAGE_02', label=' Yes', fontcolor='#2ECC71')
        dot.edge('STAGE_02', 'DEC_02')
        dot.edge('DEC_02', 'STAGE_03', label=' Yes', fontcolor='#2ECC71')
        dot.edge('STAGE_03', 'STAGE_04')
        dot.edge('STAGE_04', 'DEC_03')
        dot.edge('DEC_03', 'STAGE_05', label=' Yes', fontcolor='#2ECC71')
        dot.edge('STAGE_05', 'STAGE_06')
        dot.edge('STAGE_06', 'STAGE_07')
        dot.edge('STAGE_07', 'STAGE_08')
        dot.edge('STAGE_08', 'DEC_04')
        dot.edge('DEC_04', 'STAGE_09', label=' Yes', fontcolor='#2ECC71')
        dot.edge('STAGE_09', 'STAGE_10')
        dot.edge('STAGE_10', 'STAGE_11')
        dot.edge('STAGE_11', 'END')

    # เส้นทาง Exception (No)
    dot.edge('DEC_01', 'EXC_01', label=' No', color='#E74C3C', fontcolor='#E74C3C', style='bold')
    dot.edge('EXC_01', 'STAGE_01', style='dashed', constraint='false', color='#E74C3C')
    dot.edge('DEC_02', 'EXC_02', label=' No', color='#E74C3C', fontcolor='#E74C3C', style='bold')
    dot.edge('EXC_02', 'STAGE_02', style='dashed', constraint='false', color='#E74C3C')
    dot.edge('DEC_03', 'EXC_03', label=' No', color='#E74C3C', fontcolor='#E74C3C', style='bold')
    dot.edge('EXC_03', 'STAGE_04', style='dashed', constraint='false', color='#E74C3C')
    dot.edge('DEC_04', 'EXC_04', label=' No', color='#E74C3C', fontcolor='#E74C3C', style='bold')
    dot.edge('EXC_04', 'STAGE_08', style='dashed', constraint='false', color='#E74C3C')

    return dot

# ==========================================
# 4. ฟังก์ชันสร้างไฟล์ Excel (.xlsx)
# ==========================================
def generate_excel():
    data = []
    for node_id, info in FLOW_DATA.items():
        data.append({
            'Step ID': node_id,
            'Step Type': info.get('type', '').upper(),
            'Title (กระบวนการ)': info.get('title', ''),
            'Description (รายละเอียด)': info.get('desc', ''),
            'Next Step / Yes (ขั้นต่อไป / ผ่าน)': info.get('yes', info.get('next', '')),
            'No / Exception (กรณีไม่ผ่าน)': info.get('no', '-')
        })
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Procurement Process')
    return output.getvalue()


# ==========================================
# 5. ออกแบบ UI (พื้นที่หลัก และ Sidebar)
# ==========================================

current_node_id = st.session_state.current_node
node_info = FLOW_DATA.get(current_node_id, {})

# --- ส่วนของ SIDEBAR (แผงควบคุมด้านซ้าย) ---
with st.sidebar:
    st.markdown("### 📍 แผงควบคุม (Control Panel)")
    st.info(f"**สถานะปัจจุบัน:**\n### {node_info.get('title', '')}")
    if 'desc' in node_info:
        st.write(f"📝 *{node_info['desc']}*")
    
    st.markdown("---")
    
    # ส่วนควบคุม Interactive
    node_type = node_info.get('type')
    if node_type == 'decision':
        st.write("**โปรดตัดสินใจ:**")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ ผ่าน/อนุมัติ", use_container_width=True):
                st.session_state.current_node = node_info['yes']
                st.rerun()
        with col_no:
            if st.button("❌ ไม่อนุมัติ", use_container_width=True):
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
    
    st.markdown("---")
    st.markdown("### 📥 ดาวน์โหลด")
    
    # ดึงกราฟแบบต้นฉบับสำหรับดาวน์โหลด (ดักจับ Error กรณี Backend ประมวลผลภาพไม่ได้)
    clean_graph = generate_graph(None, layout_choice if 'layout_choice' in locals() else "แนวนอน (S-Curve)")
    
    try:
        png_data = clean_graph.pipe(format='png')
        st.download_button(
            label="🖼️ ดาวน์โหลดภาพ Flowchart (.png)",
            data=png_data,
            file_name="Procurement_Flowchart.png",
            mime="image/png",
            use_container_width=True
        )
    except Exception as e:
        st.warning("⚠️ เซิร์ฟเวอร์ไม่พร้อมสำหรับสร้างไฟล์ PNG")

    try:
        svg_data = clean_graph.pipe(format='svg')
        st.download_button(
            label="📐 ดาวน์โหลดไฟล์ Vector (.svg) ไปแก้ใน Excel",
            data=svg_data,
            file_name="Procurement_Flowchart.svg",
            mime="image/svg+xml",
            use_container_width=True
        )
    except Exception as e:
        st.warning("⚠️ เซิร์ฟเวอร์ไม่พร้อมสำหรับสร้างไฟล์ SVG")
    
    # โหลดไฟล์ตาราง (ทำงานได้ 100% ไม่มีปัญหาเรื่อง Font)
    excel_data = generate_excel()
    st.download_button(
        label="📊 ดาวน์โหลด Process Table (.xlsx)",
        data=excel_data,
        file_name="Procurement_Process_Flow.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# --- ส่วนของพื้นที่หลัก (MAIN AREA) ---
# ตัวเลือก Layout ด้านบนกราฟ
layout_choice = st.radio(
    "🔄 เลือกรูปแบบการแสดงผลกราฟ (Layout Mode):",
    options=["แนวนอน (S-Curve)", "แนวตั้ง (Top-to-Bottom)"],
    horizontal=True
)

st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# วาดกราฟบนพื้นที่หลัก (Frontend)
st.graphviz_chart(generate_graph(current_node_id, layout_choice), use_container_width=True)
