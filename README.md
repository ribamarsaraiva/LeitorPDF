# Leitor PDF

Aplicação web para leitura de PDFs organizados em pastas, com rastreamento de progresso por arquivo e por pasta.

## Requisitos

- Python 3.10+
- pip

## Instalação

```bash
cd LeitorPDF/backend
pip install -r requirements.txt
```

## Configuração

Por padrão, a aplicação lê os PDFs da pasta `LeitorPDF/backend/pdfs/`.

Para usar outra pasta, defina a variável de ambiente `PDF_ROOT`:

```bash
# Linux / macOS
export PDF_ROOT="/caminho/para/seus/pdfs"

# Windows (PowerShell)
$env:PDF_ROOT = "C:\caminho\para\seus\pdfs"
```

A estrutura de subpastas é lida automaticamente e exibida como árvore na interface.

## Executando

```bash
cd LeitorPDF/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

Acesse no navegador: [http://localhost:8000](http://localhost:8000)

## Funcionalidades

- Lista PDFs organizados por pastas com colapso/expansão
- Barra de progresso por PDF (páginas lidas / total)
- Barra de progresso por pasta (agregado dos PDFs internos)
- Badge ✓ ao concluir um PDF ou pasta inteira
- Ao abrir um PDF, retoma automaticamente na última página lida
- Progresso salvo automaticamente ao trocar de página e ao fechar

## Estrutura do projeto

```
LeitorPDF/
├── backend/
│   ├── main.py           # API FastAPI
│   ├── requirements.txt  # Dependências Python
│   ├── progress.db       # SQLite gerado automaticamente na primeira execução
│   └── pdfs/             # Coloque seus PDFs aqui (ou configure PDF_ROOT)
│       ├── Pasta A/
│       │   ├── arquivo1.pdf
│       │   └── arquivo2.pdf
│       └── Pasta B/
│           └── arquivo3.pdf
└── frontend/
    ├── index.html        # Lista de PDFs
    └── viewer.html       # Visualizador com tracking de página
```

## Observações

- O tracking de página depende do suporte do navegador ao hash `#page=N` no viewer nativo de PDF.
- Para tracking preciso de página em todos os navegadores, substitua o `<iframe>` no `viewer.html` pelo [PDF.js](https://mozilla.github.io/pdf.js/) — baixe o release em https://github.com/mozilla/pdf.js/releases e aponte o viewer para ele.
- O progresso é armazenado localmente em `progress.db` (SQLite) na pasta `backend/`.
