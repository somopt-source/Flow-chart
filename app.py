import streamlit as st
import graphviz
import pandas as pd
import io

# ==========================================
# 1. ตั้งค่าหน้า Streamlit 
# ==========================================
st.set_page_config(
    page_title="Interactive Procurement Flow", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h2 style='color: #2C3E50; margin-bottom: 5px; font-weight: bold;'>Interactive Procurement Flowchart (SOR-to-Pay)</h2>
    <p style='color: #7F8C8D; font-size: 16px;'>ระบบจำลองขั้นตอนการจัดซื้อจัดจ้าง (Professional View)</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฐานข้อมูลขั้นตอน (Flow Logic)
# ==========================================
FLOW_DATA = {
    'START': {'title': 'เริ่มต้น', 'type': 'start', 'next': 'STAGE_01'},
    'STAGE_01': {'title': 'STAGE 01: Draft SOR', 'desc': 'หน่วยงานผู้ใช้จัดทำข้อกำหนดความต้องการ (SOR) และประเมินงบประมาณ', 'type': 'stage', 'next': 'DEC_01'},
    'DEC_01': {'title': 'ตรวจสอบ SOR & Budget', 'desc': 'สเปกและงบประมาณเหมาะสมและได้รับการอนุมัติหรือไม่?', 'type': 'decision', 'yes': 'STAGE_02', 'no': 'EXC_01'},
    'EXC_01': {'title': 'ทบทวนสเปก/งบประมาณ', 'desc': 'ปรับปรุง SOR หรือดำเนินการขออนุมัติงบประมาณเพิ่มเติม', 'type': 'exception', 'next': 'STAGE_01'},
    
    'STAGE_02': {'title': 'STAGE 02: Submit PR', 'desc': 'สร้างและอนุมัติใบขอซื้อ (Purchase Requisition) ในระบบ', 'type': 'stage', 'next': 'DEC_02'},
    'DEC_02': {'title': 'อนุมัติ PR', 'desc': 'ใบขอซื้อได้รับการอนุมัติตามสายงานบังคับบัญชาหรือไม่?', 'type': 'decision', 'yes': 'STAGE_03', 'no': 'EXC_02'},
    'EXC_02': {'title': 'ตีกลับเพื่อแก้ไข PR', 'desc': 'ส่งคืนให้ผู้ขอซื้อแก้ไขข้อมูลในระบบให้ถูกต้อง', 'type': 'exception', 'next': 'STAGE_02'},
    
    'STAGE_03': {'title': 'STAGE 03: Issue RFQ / RFP', 'desc': 'ฝ่ายจัดซื้อออกเอกสารเชิญชวนเสนอราคา หรือจัดประมูล', 'type': 'stage', 'next': 'STAGE_04'},
    'STAGE_04': {'title': 'STAGE 04: Bids / Proposals', 'desc': 'ผู้ขายยื่นซองข้อเสนอทางเทคนิคและข้อเสนอทางพาณิชย์', 'type': 'stage', 'next': 'DEC_03'},
    
    'DEC_03': {'title': 'ตรวจสอบคุณสมบัติทางเทคนิค', 'desc': 'ข้อเสนอของผู้ขายผ่านเกณฑ์เทคนิคตามที่ระบุใน SOR หรือไม่?', 'type': 'decision', 'yes': 'STAGE_05', 'no': 'EXC_03'},
    'EXC_03': {'title': 'ตัดสิทธิ์ / ขอคำชี้แจง', 'desc': 'ตัดสิทธิ์ผู้เสนอราคา หรือขอให้ส่งเอกสารชี้แจงเพิ่มเติม', 'type': 'exception', 'next': 'STAGE_04'},
    
    'STAGE_05': {'title': 'STAGE 05: Commercial Eval', 'desc': 'เปิดซองราคา ประเมินความคุ้มค่า และเจรจาต่อรอง', 'type': 'stage', 'next': 'STAGE_06'},
    'STAGE_06': {'title': 'STAGE 06: Issue PO / Contract', 'desc': 'จัดทำและออกใบสั่งซื้อ (PO) หรือร่างสัญญาผูกพัน', 'type': 'stage', 'next': 'STAGE_07'},
    'STAGE_07': {'title': 'STAGE 07: Signed Agreement', 'desc': 'คู่ค้าลงนามยอมรับเงื่อนไขและผูกพันตามสัญญา', 'type': 'stage', 'next': 'STAGE_08'},
    'STAGE_08': {'title': 'STAGE 08: Execution & Delivery', 'desc': 'คู่ค้าดำเนินงานและส่งมอบสินค้า/บริการตามงวด', 'type': 'stage', 'next': 'DEC_04'},
    
    'DEC_04': {'title': 'ตรวจรับงาน (FAT/SAT)', 'desc': 'ผลการส่งมอบและตรวจรับผ่านตามเกณฑ์หรือไม่?', 'type': 'decision', 'yes': 'STAGE_09', 'no': 'EXC_04'},
    'EXC_04': {'title': 'แจ้งแก้ไข / ปรับตามสัญญา', 'desc': 'แจ้งให้คู่ค้าแก้ไขงานให้สมบูรณ์ หรือดำเนินการปรับตามเงื่อนไข', 'type': 'exception', 'next': 'STAGE_08'},
    
    'STAGE_09': {'title': 'STAGE 09: 3-Way Matching', 'desc': 'ฝ่ายบัญชีกระทบยอดเอกสาร PO, ใบรับสินค้า (GR) และใบแจ้งหนี้ (Invoice)', 'type': 'stage', 'next': 'STAGE_10'},
    'STAGE_10': {'title': 'STAGE 10: Payment', 'desc': 'ดำเนินการจ่ายเงินให้คู่ค้าตามรอบเครดิตเทอม', 'type': 'stage', 'next': 'STAGE_11'},
    'STAGE_11': {'title': 'STAGE 11: KPI & Closeout', 'desc': 'ประเมินผลการทำงานของคู่ค้า (Vendor Eval) และปิดโครงการ', 'type': 'stage', 'next': 'END'},
    'END': {'title': 'สิ้นสุดกระบวนการ', 'desc': 'Procurement Cycle Completed', 'type': 'end'}
}

if 'current_node' not in st.session_state:
    st.session_state.current_node = 'START'

# ==========================================
# 3. ฟังก์ชันวาดกราฟ (จัดระเบียบขนาดและแนวตั้ง)
# ==========================================
def generate_graph(active_node, layout_mode):
    dot = graphviz.Digraph('ProcurementFlow', comment='Interactive Flow')
    
    dot.attr(dpi='120')
    
    if layout_mode == "แนวนอน (S-Curve)":
        dot.attr(rankdir='TB', splines='ortho', nodesep='0.3', ranksep='0.4')
    else:
        # แนวตั้ง: ปรับระยะห่างให้พอดี ไม่ยาวหรือห่างจนเกินไป
        dot.attr(rankdir='TB', splines='polyline', nodesep='0.4', ranksep='0.4')
        
    dot.attr('node', fontname='Segoe UI, Tahoma, Arial Unicode MS, sans-serif')
    dot.attr('edge', color='#BDC3C7', penwidth='2', fontname='Segoe UI, Tahoma', fontsize='9')

    def get_node_style(node_id, base_color, fill_color, shape, style):
        is_active = (node_id == active_node)
        pw = '3' if is_active else '1.5'
        c = '#F39C12' if is_active else base_color
        f = '#FEF9E7' if is_active else fill_color
        return {'shape': shape, 'style': style, 'color': c, 'fillcolor': f, 'penwidth': pw}

    dot.node('START', '<<B>START</B>>', **get_node_style('START', '#27AE60', '#EAFAF1', 'box', 'filled,rounded'))
    dot.node('END', '<<B>END</B>>', **get_node_style('END', '#C0392B', '#FDEDEC', 'box', 'filled,rounded'))

    def create_stage_node(node_id, stage_num, eng_title, th_title):
        is_active = (node_id == active_node)
        pw = '2.5' if is_active else '1.5'
        c_box = '#F39C12' if is_active else '#3498DB'
        f_box = '#FEF9E7' if is_active else '#F4FAFF'
        
        c_num = '#E67E22' if is_active else '#2980B9'
        c_eng = '#2C3E50'
        c_th = '#7F8C8D'
        
        eng_title = eng_title.replace("&", "&amp;")
        th_title = th_title.replace("&", "&amp;")
        
        # 🌟 จัดกึ่งกลางด้วย ALIGN="CENTER" และปรับขนาดฟอนต์ให้พอดีตา (เล็กกำลังดี)
        label = f'''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">
        <TR><TD ALIGN="CENTER"><FONT COLOR="{c_num}" POINT-SIZE="8"><B>{stage_num}</B></FONT></TD></TR>
        <TR><TD ALIGN="CENTER"><FONT COLOR="{c_eng}" POINT-SIZE="10"><B>{eng_title}</B></FONT></TD></TR>
        <TR><TD ALIGN="CENTER"><FONT COLOR="{c_th}" POINT-SIZE="8">{th_title}</FONT></TD></TR>
        </TABLE>>'''
        dot.node(node_id, label, shape='box', style='filled,rounded', color=c_box, fillcolor=f_box, penwidth=pw, margin='0.1,0.08')

    create_stage_node('STAGE_01', 'STAGE 01', 'Draft SOR', 'จัดทำข้อกำหนดความต้องการ (SOR)')
    create_stage_node('STAGE_02', 'STAGE 02', 'Submit PR', 'สร้างใบขอซื้อ (PR) ในระบบ')
    create_stage_node('STAGE_03', 'STAGE 03', 'Issue RFQ / RFP', 'ออกเอกสารเชิญชวนเสนอราคา')
    create_stage_node('STAGE_04', 'STAGE 04', 'Bids / Proposals', 'รับซองข้อเสนอเทคนิคและราคา')
    create_stage_node('STAGE_05', 'STAGE 05', 'Commercial Eval', 'ประเมินราคาและเจรจาต่อรอง')
    create_stage_node('STAGE_06', 'STAGE 06', 'Issue PO / Contract', 'ออกใบสั่งซื้อ / จัดทำสัญญา')
    create_stage_node('STAGE_07', 'STAGE 07', 'Signed Agreement', 'คู่ค้าลงนามผูกพันสัญญา')
    create_stage_node('STAGE_08', 'STAGE 08', 'Execution & Delivery', 'ดำเนินงานและส่งมอบตามงวด')
    create_stage_node('STAGE_09', 'STAGE 09', '3-Way Matching', 'กระทบยอดเอกสาร (3-Way Match)')
    create_stage_node('STAGE_10', 'STAGE 10', 'Payment', 'ดำเนินการจ่ายเงินตามเครดิต')
    create_stage_node('STAGE_11', 'STAGE 11', 'KPI & Closeout', 'ประเมินผลงานและปิดโครงการ')

    decs = [
        ('DEC_01', '<<FONT POINT-SIZE="9"><B>SOR &amp;<BR/>Budget<BR/>Approved?</B></FONT>>'), 
        ('DEC_02', '<<FONT POINT-SIZE="9"><B>PR<BR/>Approved?</B></FONT>>'),
        ('DEC_03', '<<FONT POINT-SIZE="9"><B>Technical<BR/>Pass<BR/>SOR?</B></FONT>>'), 
        ('DEC_04', '<<FONT POINT-SIZE="9"><B>Inspection<BR/>on<BR/>FAT/SAT<BR/>Pass?</B></FONT>>')
    ]
    for d_id, d_lbl in decs:
        dot.node(d_id, d_lbl, **get_node_style(d_id, '#F39C12', '#FEF9E7', 'diamond', 'filled'))

    excs = [
        ('EXC_01', 'Revise SOR / Budget', 'ทบทวนสเปก / ขอเพิ่มงบ'), 
        ('EXC_02', 'Return to Requester', 'ตีกลับ PR ให้ผู้ขอซื้อแก้ไข'),
        ('EXC_03', 'Disqualify / Clarify', 'ตัดสิทธิ์ / ขอเอกสารชี้แจง'), 
        ('EXC_04', 'Rectify / Penalty', 'แจ้งแก้ไขงาน / ปรับตามสัญญา')
    ]
    for e_id, e_title, e_th in excs:
        is_active = (e_id == active_node)
        pw = '2' if is_active else '1.2'
        c = '#F39C12' if is_active else '#E74C3C'
        f = '#FEF9E7' if is_active else '#FDEDEC'
        label = f'''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2">
        <TR><TD ALIGN="CENTER"><FONT COLOR="{c}" POINT-SIZE="9"><B>{e_title}</B></FONT></TD></TR>
        <TR><TD ALIGN="CENTER"><FONT COLOR="#C0392B" POINT-SIZE="8">{e_th}</FONT></TD></TR>
        </TABLE>>'''
        dot.node(e_id, label, shape='rect', style='filled,rounded,dashed', color=c, fillcolor=f, penwidth=pw)

    # ตรรกะการลากเส้น
    if layout_mode == "แนวนอน (S-Curve)":
        with dot.subgraph() as s1:
            s1.attr(rank='same')
            s1.edges([('START', 'STAGE_01'), ('STAGE_01', 'DEC_01')])
            s1.edge('DEC_01', 'STAGE_02', label=' Yes', fontcolor='#27AE60')
            s1.edges([('STAGE_02', 'DEC_02')])
            s1.edge('DEC_02', 'STAGE_03', label=' Yes', fontcolor='#27AE60')
        
        with dot.subgraph() as s2:
            s2.attr(rank='same')
            s2.edge('STAGE_07', 'STAGE_06', dir='back')
            s2.edge('STAGE_06', 'STAGE_05', dir='back')
            s2.edge('STAGE_05', 'DEC_03', dir='back', label=' Yes', fontcolor='#27AE60')
            s2.edge('DEC_03', 'STAGE_04', dir='back')

        with dot.subgraph() as s3:
            s3.attr(rank='same')
            s3.edge('STAGE_08', 'DEC_04')
            s3.edge('DEC_04', 'STAGE_09', label=' Yes', fontcolor='#27AE60')
            s3.edges([('STAGE_09', 'STAGE_10'), ('STAGE_10', 'STAGE_11'), ('STAGE_11', 'END')])

        dot.edge('STAGE_03', 'STAGE_04', weight='100')
        dot.edge('STAGE_07', 'STAGE_08', weight='100')

    else:
        # แนวตั้ง: จัดระเบียบให้อยู่ในแกนกลาง และจัดกล่อง No ให้อยู่ด้านข้างในระดับเดียวกัน
        with dot.subgraph() as r1:
            r1.attr(rank='same')
            r1.node('DEC_01')
            r1.node('EXC_01')
        with dot.subgraph() as r2:
            r2.attr(rank='same')
            r2.node('DEC_02')
            r2.node('EXC_02')
        with dot.subgraph() as r3:
            r3.attr(rank='same')
            r3.node('DEC_03')
            r3.node('EXC_03')
        with dot.subgraph() as r4:
            r4.attr(rank='same')
            r4.node('DEC_04')
            r4.node('EXC_04')

        dot.edge('START', 'STAGE_01', weight='10')
        dot.edge('STAGE_01', 'DEC_01', weight='10')
        dot.edge('DEC_01', 'STAGE_02', label=' Yes', fontcolor='#27AE60', weight='10')
        dot.edge('STAGE_02', 'DEC_02', weight='10')
        dot.edge('DEC_02', 'STAGE_03', label=' Yes', fontcolor='#27AE60', weight='10')
        dot.edge('STAGE_03', 'STAGE_04', weight='10')
        dot.edge('STAGE_04', 'DEC_03', weight='10')
        dot.edge('DEC_03', 'STAGE_05', label=' Yes', fontcolor='#27AE60', weight='10')
        dot.edge('STAGE_05', 'STAGE_06', weight='10')
        dot.edge('STAGE_06', 'STAGE_07', weight='10')
        dot.edge('STAGE_07', 'STAGE_08', weight='10')
        dot.edge('STAGE_08', 'DEC_04', weight='10')
        dot.edge('DEC_04', 'STAGE_09', label=' Yes', fontcolor='#27AE60', weight='10')
        dot.edge('STAGE_09', 'STAGE_10', weight='10')
        dot.edge('STAGE_10', 'STAGE_11', weight='10')
        dot.edge('STAGE_11', 'END', weight='10')

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
# 5. ออกแบบ UI 
# ==========================================

current_node_id = st.session_state.current_node
node_info = FLOW_DATA.get(current_node_id, {})

layout_choice = st.radio(
    "🔄 เลือกรูปแบบการแสดงผลกราฟ (Layout Mode):",
    options=["แนวนอน (S-Curve)", "แนวตั้ง (Top-to-Bottom)"],
    horizontal=True
)
st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# --- ส่วนของ SIDEBAR ---
with st.sidebar:
    st.markdown("### 📍 แผงควบคุม (Control Panel)")
    st.info(f"**สถานะปัจจุบัน:**\n### {node_info.get('title', '')}")
    if 'desc' in node_info:
        st.write(f"📝 *{node_info['desc']}*")
    
    st.markdown("---")
    
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

    st.caption("หมายเหตุ: กล่องที่ถูกไฮไลท์ (สีเหลือง/ส้ม) คือขั้นตอนที่ระบบกำลังทำงานอยู่")
    
    st.markdown("---")
    st.markdown("### 📥 ดาวน์โหลด")
    
    clean_graph = generate_graph(None, layout_choice)
    
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
        st.warning(f"⚠️ ไม่สามารถสร้างไฟล์ PNG ได้ (Error: {e})")

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
        st.warning(f"⚠️ ไม่สามารถสร้างไฟล์ SVG ได้ (Error: {e})")
    
    excel_data = generate_excel()
    st.download_button(
        label="📊 ดาวน์โหลด Process Table (.xlsx)",
        data=excel_data,
        file_name="Procurement_Process_Flow.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# --- ส่วนของพื้นที่หลัก (MAIN AREA) ---
st.graphviz_chart(generate_graph(current_node_id, layout_choice), use_container_width=True)
