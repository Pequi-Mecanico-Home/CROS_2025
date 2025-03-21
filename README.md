# WakeWord com OpenWakeWord e XTTS

Este projeto treina um modelo de wake word ("Hey Miss") usando síntese de texto para fala (TTS) e técnicas de augmentação. O ambiente é preparado via Docker, e os dados são gerados combinando áudio sintético, ruídos reais e efeitos acústicos (RIR).

## Pré-requisitos

### Docker 

Baixe a imagem com:

```bash
docker pull alexandreacff/tts:xtts
```

E inicie o container (lembre-se de substituir /home/seu/diretório pelo caminho correto):

```
docker run -it --gpus all --ipc host -v /home/seu/diretório:/workspace_cros2025  alexandreacff/tts:xtts bash 
```

### Instação das Dependências

Dentro do container, instale as dependências:

```bash
pip install -r requirements.txt
```
Baixe os recursos necessários:

```bash
python3 download_mit_rirs.py
python3 download_noise_and_fma_audio.py
./setup_openwakeword_resources.sh
```


## Geração de Amostras de Áudio

O projeto gera amostras positivas e negativas usando um modelo TTS. Os arquivos gerados são salvos em diretórios separados.

## Estrutura do Projeto

- `config.yaml`: Arquivo de configuração contendo os parâmetros para a geração de amostras.
- `infer_dataset.py`: Script para gerar amostras de áudio positivas.
- `infer_dataset_negative.py`: Script para gerar amostras de áudio negativas.
- `selected_audios_cml.csv`: Arquivo CSV contendo os caminhos dos áudios e IDs dos falantes.
- `utils/`: Diretório contendo utilitários para geração de texto adversarial.
- `XTTS-v2/`: Diretório contendo o modelo de síntese de texto para fala.

## Dependências adicionais: 

Clone ou baixe os repositórios abaixo, se necessário:

```bash
git clone https://github.com/coqui-ai/TTS.git
git clone https://huggingface.co/coqui/XTTS-v2
wget https://www.openslr.org/resources/146/cml_tts_dataset_portuguese_v0.1.tar.bz
```

## Configuração (config.yaml)

Exemplo de configuração:

```yaml
csv_file: 'selected_audios_cml.csv'          # CSV com dados dos áudios
output_folder: 'generated_samples'           # Pasta para amostras positivas
negative_output_folder: 'negative_samples'   # Pasta para amostras negativas
n_samples_positive: 5000                     # Número de amostras positivas 
n_samples_negative: 5000                     # Número de amostras negativas 
keyword: 'Hey Miss'                          # Palavra-chave para amostras positivas
random: True                                 # Gerar amostras aleatórias
```

### Gerar Amostras 
Para gerar amostras de áudio positivas:

```bash
python infer_dataset.py --config config.yaml
```

Para gerar amostras de áudio negativas:

```bash
python infer_dataset_negative.py --config config.yaml
```

Os arquivos serão salvos nas pastas definidas no config.yaml (com um metadata.csv em cada pasta com informações sobre as amostras).

# Treinamento de Modelos Wake Word

O treinamento usa um arquivo de configuração YAML (por exemplo, my_model.yml) que define:

- Nome do modelo e a palavra/frase-alvo.
- Quantidade de amostras para treinamento e validação.
- Diretórios de recursos (RIR, ruídos do AudioSet e FMA).
- Parâmetros de augmentação, batch sizes, e configurações do modelo (tipo, tamanho das camadas, passos, etc.).
- Diretórios de saída para clipes positivos/negativos e features pré-computadas.

### Visão Geral

A configuração permite definir os seguintes aspectos do treinamento:

- model_name: Nome do modelo, utilizado para nomear diretórios e arquivos gerados.
- target_phrase: Lista de palavras/frases que o modelo deve detectar. Mesmo listando várias, o treinamento resultará em um modelo binário que ativa com qualquer uma delas.
- custom_negative_phrases: Lista opcional de frases que o modelo não deve reconhecer (além das negativas geradas automaticamente via sobreposição de fonemas).
- n_samples: Número total de amostras positivas geradas para treinamento. Recomenda-se um valor alto (ex.: 100K+ para modelos robustos).
- n_samples_val: Número de amostras para validação e early stopping. Geralmente, um décimo de n_samples.
- tts_batch_size: Tamanho do batch usado para gerar áudio sintético com o Piper TTS.
- augmentation_batch_size: Tamanho do batch para aplicar técnicas de augmentação. Manter um tamanho menor pode ajudar a introduzir maior variedade.
- piper_sample_generator_path: Caminho para o repositório do Piper Sample Generator, utilizado para síntese de áudio.
- output_dir: Diretório base para salvar os clipes sintéticos gerados, features extraídas e modelos treinados.
- rir_paths: Lista de diretórios contendo gravações de Room Impulse Responses (RIR) para simular ambientes acústicos.
- background_paths: Diretórios contendo áudios de fundo (por exemplo, provenientes dos datasets AudioSet e FMA) para mixar com os áudios positivos.
- background_paths_duplication_rate: Taxa de duplicação dos arquivos de fundo, permitindo oversampling de determinados tipos de ruído.
- false_positive_validation_data_path: Caminho para os features pré-computados usados na validação de falsos positivos.
- augmentation_rounds: Número de vezes que cada exemplo sintético é reutilizado com augmentação, aumentando a variabilidade.
- feature_data_files: Dicionário que mapeia nomes de arquivos de features (pré-computadas) para seus respectivos caminhos.
- batch_n_per_class: Define a quantidade de exemplos de cada classe por batch no treinamento. A soma dos valores define o tamanho total do batch.
- model_type: Tipo do modelo a ser treinado (por exemplo, DNN – Deep Neural Network).
- layer_size: Tamanho (número de neurônios) das camadas do modelo. Aumentar este valor pode melhorar a performance, mas pode afetar a velocidade de inferência.
- steps: Número máximo de passos de treinamento.
- target_accuracy e target_recall: Métricas desejadas para acurácia e recall, que ajudam a monitorar a qualidade do modelo durante o treinamento.
- max_negative_weight: Peso máximo para exemplos negativos, utilizado para controlar o processo de treinamento automático.
- target_false_positives_per_hour: Meta para o número de falsos positivos por hora no ambiente de deployment.
- Especifica os diretórios onde os clipes positivos e negativos, tanto para treinamento quanto para teste, serão salvos. Essa organização facilita a gestão dos dados gerados e a validação do modelo.

### Augmentação 

Para aplicar augmentação:

```bash
python3 train.py --training_config my_model.yml --augment_clips --overwrite 
```

### Treinamento 

Para inicar o treinamento:

```bash
python3 train.py --training_config my_model.yml --train_model 
```