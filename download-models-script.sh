#!/bin/bash
# Script para download de modelos de IA para LocalAI

# Criar diretório para modelos se não existir
mkdir -p infrastructure/localai/models

echo "🤖 Iniciando download dos modelos para LocalAI..."

# Função para verificar se modelo já existe
model_exists() {
    if [ -f "infrastructure/localai/models/$1" ]; then
        return 0 # Existe
    else
        return 1 # Não existe
    fi
}

# Download do modelo Phi-3-mini
PHI3_MINI="phi-3-mini-4k-instruct.Q4_K_M.gguf"
if ! model_exists "$PHI3_MINI"; then
    echo "📥 Baixando modelo Phi-3-mini..."
    curl -L "https://huggingface.co/TheBloke/phi-3-mini-4k-instruct-GGUF/resolve/main/phi-3-mini-4k-instruct.Q4_K_M.gguf" \
        -o "infrastructure/localai/models/$PHI3_MINI"
    echo "✅ Download do Phi-3-mini concluído!"
else
    echo "✅ Modelo Phi-3-mini já existe. Pulando download."
fi

# Download do modelo de embeddings
MINILM="all-MiniLM-L6-v2.gguf"
if ! model_exists "$MINILM"; then
    echo "📥 Baixando modelo de embeddings MiniLM..."
    curl -L "https://huggingface.co/abetlen/all-MiniLM-L6-v2-GGUF/resolve/main/all-MiniLM-L6-v2.F16.gguf" \
        -o "infrastructure/localai/models/$MINILM"
    echo "✅ Download do MiniLM concluído!"
else
    echo "✅ Modelo MiniLM já existe. Pulando download."
fi

# Download do modelo falcon (opcional para summarization)
FALCON="gpt4all-falcon-q4_0.gguf"
if ! model_exists "$FALCON"; then
    echo "📥 Baixando modelo Falcon..."
    curl -L "https://huggingface.co/TheBloke/gpt4all-falcon-gguf/resolve/main/gpt4all-falcon-q4_0.gguf" \
        -o "infrastructure/localai/models/$FALCON"
    echo "✅ Download do Falcon concluído!"
else
    echo "✅ Modelo Falcon já existe. Pulando download."
fi

echo "🎉 Todos os modelos foram baixados com sucesso!"
echo "📂 Os modelos estão em: infrastructure/localai/models/"
echo "🚀 Você pode iniciar o ambiente com: docker-compose up -d"