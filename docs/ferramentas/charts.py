import csv, os
from PIL import Image

here = os.path.dirname(os.path.abspath(__file__))
dest = os.path.join(here, '..', 'img')
os.makedirs(dest, exist_ok=True)

BG, FG, GRID, MUTE = '#0d1b1e', '#e8efe9', '#24373b', '#8aa3a0'
NEW, OLD, WARN = '#2dd4bf', '#f59e0b', '#ff5a4e'
FONT = "font-family='Geist, Segoe UI, Arial, sans-serif'"


def svg(w, h, body):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}' {FONT}>"
            f"<rect width='{w}' height='{h}' fill='{BG}' rx='10'/>{body}</svg>")


def text(x, y, s, size=13, fill=FG, anchor='start', weight='normal'):
    s = str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return f"<text x='{x}' y='{y}' font-size='{size}' fill='{fill}' text-anchor='{anchor}' font-weight='{weight}'>{s}</text>"


# ---------------------------------------------------------------- 1) trajetória do pulo
rows = list(csv.reader(open(os.path.join(here, 'trajetoria.csv')), delimiter=';'))[1:]
t = [float(r[0]) for r in rows]
new = [float(r[1]) for r in rows]
old = [float(r[2]) for r in rows]
W, H, L, R, T, B = 760, 420, 70, 30, 60, 60
x0, x1 = 0, 1.0
ymin, ymax = -60, 110
sx = lambda v: L + (v - x0) / (x1 - x0) * (W - L - R)
sy = lambda v: T + (ymax - v) / (ymax - ymin) * (H - T - B)
b = text(L, 30, 'Pulo do drone: altura acima do ponto de partida (px) × tempo (s)', 16, weight='bold')
b += text(L, 48, 'simulação com a classe Bird real, quadros de 1/60 s', 12, MUTE)
for v in range(-50, 111, 25):
    b += f"<line x1='{L}' x2='{W-R}' y1='{sy(v)}' y2='{sy(v)}' stroke='{GRID}'/>" + text(L - 8, sy(v) + 4, v, 11, MUTE, 'end')
for v in [0, .2, .4, .6, .8, 1.0]:
    b += f"<line y1='{T}' y2='{H-B}' x1='{sx(v)}' x2='{sx(v)}' stroke='{GRID}'/>" + text(sx(v), H - B + 18, f'{v:.1f}', 11, MUTE, 'middle')
b += f"<line x1='{L}' x2='{W-R}' y1='{sy(0)}' y2='{sy(0)}' stroke='{MUTE}' stroke-dasharray='4 4'/>"
for series, col in ((old, OLD), (new, NEW)):
    pts = ' '.join(f'{sx(a):.1f},{sy(v):.1f}' for a, v in zip(t, series))
    b += f"<polyline points='{pts}' fill='none' stroke='{col}' stroke-width='3'/>"
ia, ib = new.index(max(new)), old.index(max(old))
b += f"<circle cx='{sx(t[ia])}' cy='{sy(new[ia])}' r='5' fill='{NEW}'/>" + text(sx(t[ia]) + 10, sy(new[ia]) - 8, f'apogeu {new[ia]:.1f} px em {t[ia]:.2f} s', 12, NEW)
b += f"<circle cx='{sx(t[ib])}' cy='{sy(old[ib])}' r='5' fill='{OLD}'/>" + text(sx(t[ib]) - 10, sy(old[ib]) - 8, f'apogeu {old[ib]:.1f} px em {t[ib]:.2f} s', 12, OLD, 'end')
b += f"<rect x='{L+12}' y='{H-B-62}' width='14' height='4' fill='{NEW}'/>" + text(L + 34, H - B - 56, 'versão acessível: g=1000, v₀=−400', 12)
b += f"<rect x='{L+12}' y='{H-B-42}' width='14' height='4' fill='{OLD}'/>" + text(L + 34, H - B - 36, 'versão original: g=1800, v₀=−600', 12)
b += text((L + W - R) // 2, H - 14, 'tempo desde o toque (s)', 12, MUTE, 'middle')
open(os.path.join(dest, '06_trajetoria_pulo.svg'), 'w', encoding='utf-8').write(svg(W, H, b))

# ---------------------------------------------------------------- 2) sensibilidade ao dt
dts = [('1/30 s', 73.33), ('1/60 s', 76.67), ('1/144 s', 78.62), ('1/240 s', 79.17)]
W, H = 760, 340
b = text(40, 30, 'Mesmo toque, taxas de quadro diferentes: apogeu medido (px)', 16, weight='bold')
b += text(40, 48, 'linha tracejada = valor exato da fórmula v₀² / 2g = 80 px', 12, MUTE)
bx, bw, base_y, scale = 70, 110, 295, 2.4
ytop = lambda v: base_y - v * scale
b += f"<line x1='40' x2='{W-40}' y1='{ytop(80)}' y2='{ytop(80)}' stroke='{WARN}' stroke-dasharray='6 4'/>" + text(W - 40, ytop(80) - 24, 'fórmula: 80,00 px', 12, WARN, 'end')
for i, (lab, v) in enumerate(dts):
    x = bx + i * 170
    b += f"<rect x='{x}' y='{ytop(v)}' width='{bw}' height='{v*scale}' fill='{NEW}' opacity='{0.55 + 0.15*i/3}' rx='4'/>"
    b += text(x + bw / 2, ytop(v) - 8, f'{v:.2f}', 14, FG, 'middle', 'bold') + text(x + bw / 2, base_y + 20, lab, 12, MUTE, 'middle')
open(os.path.join(dest, '07_sensibilidade_dt.svg'), 'w', encoding='utf-8').write(svg(W, H, b))

# ---------------------------------------------------------------- 3) janela de reação
# valores calculados das constantes do GameConfig
def window(speed, gap, r, spawn):
    approach = (480 - (140 + r)) / speed
    return dict(approach=approach, spacing=spawn, expose=(80 + 2 * r) / speed, room=gap - 2 * r)
new_w = window(140, 230, 17, 2.4)
old_w = window(250, 160, 17, 1.5)  # mesmo raio, só para isolar o efeito das constantes que mudaram
W, H = 760, 330
b = text(40, 30, 'Janelas de reação: o que a calibração comprou (mesmo raio de colisão, 17 px)', 16, weight='bold')
b += text(40, 48, 'calculado de GameConfig: velocidade dos racks, abertura e intervalo entre racks', 12, MUTE)
items = [
    ('Tempo vendo o rack chegar (s)', old_w['approach'], new_w['approach'], '{:.2f}'),
    ('Intervalo entre racks (s)', old_w['spacing'], new_w['spacing'], '{:.2f}'),
    ('Folga vertical do centro do drone (px)', old_w['room'], new_w['room'], '{:.0f}'),
]
maxes = [2.6, 2.6, 210]
for i, ((lab, o, n, fmt), mx) in enumerate(zip(items, maxes)):
    y = 100 + i * 76
    b += text(40, y - 22, lab, 13)
    for j, (v, col, tag) in enumerate(((o, OLD, 'original'), (n, NEW, 'acessível'))):
        yy = y + j * 24
        w_ = v / mx * 480
        b += f"<rect x='150' y='{yy-12}' width='{w_:.1f}' height='18' rx='3' fill='{col}'/>"
        b += text(142, yy + 2, tag, 11, MUTE, 'end') + text(150 + w_ + 8, yy + 2, fmt.format(v), 12, FG)
open(os.path.join(dest, '08_janelas_de_reacao.svg'), 'w', encoding='utf-8').write(svg(W, H, b))
print('janelas', new_w, old_w)

# ---------------------------------------------------------------- 4) colisão círculo × retângulo (ponto mais próximo)
W, H = 760, 330
b = text(40, 30, 'Colisão círculo × retângulo: ponto mais próximo', 16, weight='bold')
b += text(40, 48, 'nearest = clamp(centro, borda do retângulo); colide se |centro − nearest|² < r²', 12, MUTE)
rx, ry, rw, rh = 150, 205, 220, 105
b += f"<rect x='{rx}' y='{ry}' width='{rw}' height='{rh}' fill='{WARN}' fill-opacity='.18' stroke='{WARN}' stroke-width='2'/>"
b += text(rx + rw / 2, ry + rh / 2 + 5, 'rack (AABB)', 13, WARN, 'middle')
cases = [(rx - 70, ry - 55, 'quina: erra por perto'), (rx + rw + 20, ry + 40, 'lateral: encosta')]
cx, cy, r = 90, 135, 34
nx, ny = max(rx, min(cx, rx + rw)), max(ry, min(cy, ry + rh))
b += f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='{NEW}' stroke-width='3'/><circle cx='{cx}' cy='{cy}' r='3' fill='{NEW}'/>"
b += f"<line x1='{cx}' y1='{cy}' x2='{nx}' y2='{ny}' stroke='{FG}' stroke-dasharray='4 3'/><circle cx='{nx}' cy='{ny}' r='4' fill='{FG}'/>"
dist = ((cx - nx) ** 2 + (cy - ny) ** 2) ** .5
b += text(cx + r + 12, cy - 6, f'distância {dist:.0f} px > r={r}: passa', 12, NEW)
# caixa quadrada do círculo (o que a AABB faria)
b += f"<rect x='{cx-r}' y='{cy-r}' width='{2*r}' height='{2*r}' fill='none' stroke='{OLD}' stroke-dasharray='3 3'/>"
b += text(cx - r + 20, cy + r + 18, 'a caixa do círculo (laranja) já encostaria no rack', 12, OLD)
# explicação
b += text(440, 150, 'Por que círculo e não caixa', 14, weight='bold')
for k, line in enumerate(['• a hélice, a antena e as quinas do sprite não contam;',
                          '• raspão diagonal na quina é perdoado;',
                          '• o círculo não “enrosca” em canto de rack;',
                          '• raio de 17 px sobre um sprite de 80×58 px.']):
    b += text(440, 176 + k * 24, line, 13, FG)
open(os.path.join(dest, '09_colisao_circulo_retangulo.svg'), 'w', encoding='utf-8').write(svg(W, H, b))

# os PNGs do jogo vêm do Shots.java (saída em docs/img); a folha de contato junta os cinco
names = ['01_menu', '02_prepare-se', '03_jogando', '04_colisao-circulo-e-retangulo', '05_fim-de-jogo']
imgs = [Image.open(os.path.join(dest, n + '.png')).convert('RGB') for n in names]
sheet = Image.new('RGB', (480 * 5 + 16 * 4, 800), (13, 27, 30))
for i, im in enumerate(imgs):
    sheet.paste(im, (i * 496, 0))
sheet.save(os.path.join(dest, '00_folha_de_prints.png'))
