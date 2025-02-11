import random
import requests

# Listas de fonemas comuns em português
consoantes = ['b', 'c', 'd', 'f', 'g', 'j', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'z', 
              'br', 'cr', 'dr', 'fr', 'gr', 'pr', 'tr', 'vr', 'bl', 'cl', 'fl', 'gl', 'pl']
vogais = ['a', 'e', 'i', 'o', 'u', 'ai', 'ei', 'oi', 'au', 'ou']

def gerar_silaba():
    # Gera uma sílaba no padrão consoante-vogal ou vogal apenas
    if random.random() < 0.7:  # 70% de chance de começar com consoante
        return random.choice(consoantes) + random.choice(vogais)
    else:
        return random.choice(vogais)

def gerar_palavra_aleatoria():
    # Gera palavras com 2 a 4 sílabas
    num_silabas = random.randint(2, 4)
    palavra = ''.join([gerar_silaba() for _ in range(num_silabas)])
    
    # Ajustes finais para melhor fonética
    palavra = palavra.replace('aa', 'a').replace('ee', 'e').replace('ii', 'i')  # Remove vogais duplicadas
    return palavra[:8]  # Limita o tamanho máximo

def carregar_palavras_brasileiras():
    # Fonte: Lista de palavras mais comuns do português brasileiro
    url = "https://www.ime.usp.br/~pf/dicios/br-utf8.txt"
    
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        palavras = response.text.splitlines()
        
        # Filtra palavras comuns entre 3 e 10 letras
        palavras_filtradas = [p.lower() for p in palavras if 3 <= len(p) <= 8 and p.isalpha()]
        return palavras_filtradas
    
    except Exception as e:
        print(f"Erro ao carregar palavras: {e}")
        return []

def gerar_amostras_negativas(num_amostras=10):
    palavras = carregar_palavras_brasileiras()
    
    if not palavras:
        print("Não foi possível carregar a lista de palavras")
        return []
    
    return random.sample(palavras, min(num_amostras, len(palavras)))


# Exemplo de uso: gerar 20 palavras
if __name__ == "__main__":
    amostras_negativas = [gerar_palavra_aleatoria() for _ in range(20)]
    print("Amostras negativas geradas aleatorias:")
    print('\n'.join(amostras_negativas))
    amostras_negativas = gerar_amostras_negativas(20)
    print("Amostras negativas geradas:")
    print('\n'.join(amostras_negativas))
