#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para remover duplicações em raffle_detail.html"""

# Ler arquivo
with open('templates/raffle_detail.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total de linhas originais: {len(lines)}")

# A duplicação começa na linha 226 (índice 225)
# Ve até onde vai a primeira seção válida
# Procurar por "{% endif %}" que fecha o bloco manual antes da duplicaç ão

# Encontrar final da seção manual (linha 224)
# Tudo depois da linha 224 até encontrar "{% endfor %}" são duplicatas

# Estratégia: manter apenas linhas 0-224, pular duplicatas e pegar só o script final + endfor/endblock

# Identificar onde termina a duplicação procurando pelo script de checkbox
valid_section_end = None
for i in range(len(lines)):
    if i > 220 and '{% endif %}' in lines[i] and i < 230:
        valid_section_end = i + 1
        break

if not valid_section_end:
    valid_section_end = 225

print(f"Seção válida termina na linha: {valid_section_end}")

# A partir da linha 225 começa duplicação
# Procurar onde está o script de checkboxes válido (deve ser próximo ao final)
script_start = None
for i in range(len(lines) - 100, len(lines)):
    if '<script>' in lines[i] and 'checkboxes.forEach' in ''.join(lines[i:i+10]):
        script_start = i
        break

print(f"Script válido começa na linha: {script_start}")

# Construir arquivo limpo
clean_lines = []

# 1. Adicionar início até fim da seção válida (0-224)
clean_lines.extend(lines[0:valid_section_end])

# 2. Adicionar linha em branco
clean_lines.append('\r\n')

# 3. Adicionar script final + tags de fechamento
if script_start:
    clean_lines.extend(lines[script_start:])
else:
    # Se não encontrou script, adicionar manualmente os fechamentos
    clean_lines.append('        <script>\r\n')
    clean_lines.append('            const checkboxes = document.querySelectorAll(\'input[type="checkbox"]\');\r\n')
    clean_lines.append('            const countSpan = document.getElementById(\'selected-count\');\r\n')
    clean_lines.append('            const buyBtn = document.getElementById(\'buy-btn\');\r\n')
    clean_lines.append('\r\n')
    clean_lines.append('            checkboxes.forEach(cb => {\r\n')
    clean_lines.append('                cb.addEventListener(\'change\', () => {\r\n')
    clean_lines.append('                    const count = document.querySelectorAll(\'input[type="checkbox"]:checked\').length;\r\n')
    clean_lines.append('                    countSpan.textContent = count;\r\n')
    clean_lines.append('                    if(buyBtn) buyBtn.disabled = count === 0;\r\n')
    clean_lines.append('                });\r\n')
    clean_lines.append('            });\r\n')
    clean_lines.append('        </script>\r\n')
    clean_lines.append('        {% endif %}\r\n')
    clean_lines.append('    </div>\r\n')
    clean_lines.append('</div>\r\n')
    clean_lines.append('{% endfor %}\r\n')
    clean_lines.append('{% endif %}\r\n')
    clean_lines.append('{% endif %}\r\n')
    clean_lines.append('{% endblock %}\r\n')

print(f"Total de linhas limpas: {len(clean_lines)}")

# Salvar
with open('templates/raffle_detail.html', 'w', encoding='utf-8') as f:
    f.writelines(clean_lines)

print("✅ Arquivo limpo criado!")
