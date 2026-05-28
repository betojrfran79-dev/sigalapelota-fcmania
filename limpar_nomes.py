import os

pasta_heads = "heads"
texto_indesejado = "_resultado" # Se o seu XnConvert colocou algo diferente, tipo "_result", mude aqui!

print("Iniciando a limpeza dos nomes...")

if os.path.exists(pasta_heads):
    contador = 0
    for arquivo in os.listdir(pasta_heads):
        if texto_indesejado in arquivo:
            caminho_antigo = os.path.join(pasta_heads, arquivo)
            # Tira o "_resultado" do nome
            novo_nome = arquivo.replace(texto_indesejado, "")
            caminho_novo = os.path.join(pasta_heads, novo_nome)
            
            try:
                os.rename(caminho_antigo, caminho_novo)
                contador += 1
            except Exception as e:
                print(f"Erro ao renomear {arquivo}: {e}")
                
    print(f"Sucesso Total! {contador} arquivos foram corrigidos.")
else:
    print("Erro: A pasta 'heads' não foi encontrada.")