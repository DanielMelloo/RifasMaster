#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para inserir rotas PIX no app.py"""

# Ler app.py
with open('app.py', 'r', encoding='utf-8') as f:
    app_lines = f.readlines()

# Ler rotas PIX
with open('pix_routes.py', 'r', encoding='utf-8') as f:
    pix_lines = f.readlines()

# Encontrar linha onde inserir após o último redirect do dashboard dentro do range esperado
insert_line = None
for i in range(len(app_lines) - 1, 0, -1):
    line = app_lines[i]

    # Checa se contém redirect para dashboard e está dentro da faixa indicada
    if (
        "return redirect(url_for" in line
        and "dashboard" in line
        and 400 < i < 500
    ):
        insert_line = i + 1
        break

if insert_line:
    # Inserir rotas PIX
    app_lines.insert(insert_line, "\n")

    # Se a primeira linha do arquivo for vazia ou comentário, pular
    start_index = 1 if pix_lines[0].strip() == "" else 0

    for route_line in pix_lines[start_index:]:
        insert_line += 1
        app_lines.insert(insert_line, route_line)

    # Salvar app.py modificado
    with open("app.py", "w", encoding="utf-8") as f:
        f.writelines(app_lines)

    print(f"✅ Rotas PIX inseridas com sucesso após a linha {insert_line - (len(pix_lines) - start_index)}!")

else:
    print("❌ Não foi possível encontrar o local de inserção.")
