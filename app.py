import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF
import io
import json
import os
import locale
from datetime import date

# --- Tenta configurar data para português ---
try:
    locale.setlocale(locale.LC_TIME, "pt_BR.utf-8")
except:
    pass

# --- CONFIGURAÇÕES E PERSISTÊNCIA ---
ARQUIVO_RASCUNHO = "rascunho_dados.json"

def salvar_dados(dados):
    with open(ARQUIVO_RASCUNHO, "w") as f:
        json.dump(dados, f)

def carregar_dados():
    if os.path.exists(ARQUIVO_RASCUNHO):
        with open(ARQUIVO_RASCUNHO, "r") as f:
            return json.load(f)
    return {}

def formatar_documento(n):
    n = "".join(filter(str.isdigit, n))
    if len(n) == 11:  # CPF
        return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"
    elif len(n) == 14:  # CNPJ
        return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"
    return n

# --- INTERFACE ---
st.set_page_config(page_title="Parecer Técnico ABNT", layout="centered")
rascunho = carregar_dados()

st.title("📄 Parecer Técnico (Padrão ABNT)")

# --- CAMPOS OBRIGATÓRIOS ---
st.subheader("Informações Obrigatórias")
car = st.text_input("Número do CAR:", value=rascunho.get("car", ""))
# Aqui o usuário digita só o número, mas no documento sairá "SP-NOT: ..."
sp_not = st.text_input("SP-NOT (Digite o número/ano):", value=rascunho.get("sp_not", ""))
imovel = st.text_input("Nome do Imóvel Rural:", value=rascunho.get("imovel", ""))
nome_pessoa = st.text_input("Nome do Requerente:", value=rascunho.get("nome", ""))
doc_raw = st.text_input("CPF ou CNPJ (apenas números):", value=rascunho.get("doc", ""))
cidade = st.text_input("Cidade:", value=rascunho.get("cidade", "Mogi das Cruzes"))

doc_formatado = formatar_documento(doc_raw)

# --- LISTA COMPLETA DE TÓPICOS ---
opcoes_disponiveis = [
    "Inconsistências em Ficha do imóvel",
    "Inconsistências em Sobreposição com outros IRs",
    "Outras Sobreposições",
    "Inconsistências em Áreas embargadas",
    "Inconsistências em Assentamentos",
    "Inconsistências em UC",
    "Inconsistências em Cobertura do solo",
    "Inconsistências em Infraestrutura e utilidade pública",
    "Inconsistências em Reservatório para abastecimento ou geração de energia",
    "Inconsistências em APP hidrografia",
    "Inconsistências em APP Relevo",
    "Inconsistências em Uso restrito",
    "Inconsistências em outras APPs",
    "Inconsistências em RL averbada, RL aprovada e não averbada",
    "Inconsistências em Área de RL exigida por lei",
    "Inconsistências em Localização e cobertura do solo",
    "Inconsistências em Regularidade do IR",
    "Observação"
]

# --- LÓGICA DE SELEÇÃO E ORDEM ---
st.subheader("Tópicos de Inconsistência")
st.info("💡 A ordem que você selecionar as caixas abaixo será a ordem numérica (1, 2, 3...) no documento final.")

lista_selecionados = rascunho.get("selecionados", [])
novas_respostas = {}

for opcao in opcoes_disponiveis:
    ja_estava_marcado = opcao in lista_selecionados
    marcado = st.checkbox(opcao, value=ja_estava_marcado)
    
    if marcado:
        if opcao not in lista_selecionados:
            lista_selecionados.append(opcao)
        txt_anterior = rascunho.get(f"texto_{opcao}", "")
        obs = st.text_area(f"Detalhes para '{opcao}':", value=txt_anterior, key=f"txt_{opcao}")
        novas_respostas[opcao] = obs
    else:
        if opcao in lista_selecionados:
            lista_selecionados.remove(opcao)

# Salvar Rascunho
dados_para_salvar = {
    "car": car, "sp_not": sp_not, "imovel": imovel, 
    "nome": nome_pessoa, "doc": doc_raw, "cidade": cidade,
    "selecionados": lista_selecionados
}
for item in lista_selecionados:
    if item in novas_respostas:
        dados_para_salvar[f"texto_{item}"] = novas_respostas[item]

salvar_dados(dados_para_salvar)

# --- GERAR DOCUMENTOS ---
if st.button("Gerar Documentos Finais"):
    if not (car and sp_not and imovel and nome_pessoa and doc_formatado):
        st.error("❌ Preencha todos os campos obrigatórios!")
    elif not lista_selecionados:
        st.warning("⚠️ Selecione pelo menos uma inconsistência para gerar o relatório.")
    else:
        # --- WORD ABNT ---
        doc = Document()
        for section in doc.sections:
            section.top_margin, section.left_margin = Cm(3), Cm(3)
            section.bottom_margin, section.right_margin = Cm(2), Cm(2)

        def add_linha_mista(label, info):
            p = doc.add_paragraph()
            run_lbl = p.add_run(f"{label}: ")
            run_lbl.bold = True
            run_lbl.font.name = 'Arial'
            run_lbl.font.size = Pt(12)
            run_inf = p.add_run(info)
            run_inf.font.name = 'Arial'
            run_inf.font.size = Pt(12)

        # Cabeçalho
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("Justificativa do Parecer Técnico").bold = True
        p.runs[0].font.size = Pt(14)
        p.runs[0].font.name = 'Arial'
        
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"CAR: {car}").bold = True
        p.runs[0].font.name = 'Arial'
        
        # CORREÇÃO AQUI: Adicionado "SP-NOT: " fixo antes do valor
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"SP-NOT: {sp_not}").bold = True
        p.runs[0].font.name = 'Arial'
        doc.add_paragraph()

        # Dados Pessoais
        add_linha_mista("Nome do Imóvel Rural", imovel)
        p_p = doc.add_paragraph()
        p_p.add_run("Nome: ").bold = True
        p_p.add_run(f"{nome_pessoa}  ")
        p_p.add_run("CPF/CNPJ: ").bold = True
        p_p.add_run(doc_formatado)
        for r in p_p.runs: r.font.name = 'Arial'
        doc.add_paragraph()

        # Loop Numérico
        for i, item in enumerate(lista_selecionados):
            numero = i + 1
            texto_obs = novas_respostas.get(item, "")
            
            p_tit = doc.add_paragraph()
            run_tit = p_tit.add_run(f"{numero}. {item}")
            run_tit.bold = True
            run_tit.font.name = 'Arial'
            run_tit.font.size = Pt(12)
            
            p_txt = doc.add_paragraph(texto_obs)
            p_txt.style.font.name = 'Arial'
            p_txt.style.font.size = Pt(12)
            doc.add_paragraph()

        # Assinatura (Direita, Sem CPF, Data em baixo)
        doc.add_paragraph("\n\n")
        data_hj = date.today().strftime("%d de %B de %Y")
        
        # 1. Linha
        p_line = doc.add_paragraph("________________________________________")
        p_line.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # 2. Nome
        p_name = doc.add_paragraph(f"{nome_pessoa}")
        p_name.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_name.runs[0].font.name = 'Arial'
        
        # 3. Data
        p_date = doc.add_paragraph(f"{cidade}, {data_hj}.")
        p_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_date.runs[0].font.name = 'Arial'

        buf = io.BytesIO()
        doc.save(buf)
        st.download_button("⬇️ Baixar Word", buf.getvalue(), "Parecer_Tecnico.docx")

        # --- PDF ---
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Justificativa do Parecer Técnico", ln=True, align='C')
        pdf.cell(0, 10, f"CAR: {car}", ln=True, align='C')
        
        # CORREÇÃO AQUI: Adicionado "SP-NOT: " fixo antes do valor
        pdf.cell(0, 10, f"SP-NOT: {sp_not}", ln=True, align='C')
        pdf.ln(5)
        
        def pdf_label(lbl, txt):
            pdf.set_font("Arial", 'B', 12)
            pdf.write(8, f"{lbl}: ")
            pdf.set_font("Arial", '', 12)
            pdf.write(8, f"{txt}\n")

        pdf_label("Nome do Imóvel Rural", imovel)
        pdf_label("Nome", nome_pessoa)
        pdf_label("CPF/CNPJ", doc_formatado)
        pdf.ln(5)

        # Loop Numérico PDF
        for i, item in enumerate(lista_selecionados):
            numero = i + 1
            texto_obs = novas_respostas.get(item, "")
            
            pdf.set_font("Arial", 'B', 12)
            titulo_limpo = f"{numero}. {item}".encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 8, titulo_limpo, ln=True)
            
            pdf.set_font("Arial", '', 12)
            texto_limpo = texto_obs.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 7, texto_limpo)
            pdf.ln(4)

        # Assinatura PDF (Direita, Sem CPF, Data em baixo)
        pdf.ln(20)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 6, "________________________________________", ln=True, align='R')
        pdf.cell(0, 6, f"{nome_pessoa}", ln=True, align='R')
        pdf.cell(0, 6, f"{cidade}, {data_hj}.", ln=True, align='R')

        pdf_out = pdf.output(dest='S').encode('latin-1')
        st.download_button("⬇️ Baixar PDF", pdf_out, "Parecer_Tecnico.pdf")