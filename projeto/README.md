# MRTI · fontes das artes e vídeos

Arquivos-fonte para refazer ou ajustar as peças em `../artes/`.

| Pasta | Conteúdo |
|---|---|
| `brand/` | Brasão (`crest.png`) e logo completo (`lockup.png`) com fundo transparente |
| `fonts/` | Fontes da marca (Cormorant Garamond, Playfair Display, Inter, JetBrains Mono) |
| `post13/` | Carrossel "13º salário: 6 dúvidas" + story (`post.html`, render com `node render.js post.html out`) |
| `feriado/` | Aviso de feriado 20/11 (feed + story) |
| `screens/` | Vídeo "Sua empresa fatura. Mas cadê o dinheiro?" (`full.html`) e prévia da abertura (`screens.html`) |
| `v5/` | Vídeos originais enviados (`src/`), transcrições, recortes usados (`clips.json`) e linha do tempo |
| `scripts/` | Transcrição, plano de cortes e mixagem de áudio do vídeo |

Renderização (Playwright + ffmpeg): os HTML expõem `window.render(t)` e são gravados quadro a quadro.
