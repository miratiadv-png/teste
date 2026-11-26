# MRTI · fontes das artes e vídeos

Arquivos-fonte para refazer ou ajustar as peças em `../artes/`.

| Pasta | Conteúdo |
|---|---|
| `brand/` | Brasão (`crest.png`) e logo completo (`lockup.png`) com fundo transparente |
| `fonts/` | Fontes da marca (Cormorant Garamond, Playfair Display, Inter, JetBrains Mono) |
| `post13/` | Carrossel "13º salário: 6 dúvidas" + story (`post.html`, render com `node render.js post.html out`) |
| `feriado/` | Aviso de feriado 20/11 (feed + story) |
| `screens/` | Vídeo "Cadê o dinheiro?": v2 (`full.html`), v4 serviço por serviço (`full4.html`), capa da v4 (`capa4.html`, render com `node shot_capa.js capa4.html capa.png`) e prévia da abertura (`screens.html`) |
| `v5/` | Vídeos originais enviados (`src/`), transcrições, recortes usados (`clips.json`, `clips_v4.json`) e linhas do tempo (`timeline.json`, `timeline_v4.json`) |
| `scripts/` | Transcrição, plano de cortes (`plan_screens.py`, `plan_v4.py`) e mixagem de áudio (`audio_screens.py`, `audio_v4.py`) |

Renderização (Playwright + ffmpeg): os HTML expõem `window.render(t)` e são gravados quadro a quadro.
