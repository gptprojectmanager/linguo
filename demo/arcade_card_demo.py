import sys

# 24-bit ANSI TrueColor half-block renderer
# Foreground = top pixel, Background = bottom pixel
def rgb_block(top_rgb, bot_rgb):
    if top_rgb is None and bot_rgb is None:
        return " "
    if top_rgb is None:
        br, bg, bb = bot_rgb
        return f"\033[38;2;{br};{bg};{bb}m▄\033[0m"
    if bot_rgb is None:
        tr, tg, tb = top_rgb
        return f"\033[38;2;{tr};{tg};{tb}m▀\033[0m"
    tr, tg, tb = top_rgb
    br, bg, bb = bot_rgb
    return f"\033[38;2;{tr};{tg};{tb}m\033[48;2;{br};{bg};{bb}m▀\033[0m"

# Palette: 8-bit Retro Arcade Colors
_ = None                # Transparent / background
R = (235, 60, 60)       # Red awning / fruit
W = (245, 245, 245)     # White stripe
Y = (245, 210, 50)      # Yellow / gold
B = (140, 85, 45)       # Wood brown
G = (60, 195, 75)       # Green awning / leaf
S = (255, 215, 175)     # Skin / customer
C = (40, 160, 220)      # Cyan / apron
D = (50, 50, 60)        # Shadow dark

# 16 wide x 10 tall pixel grid for STREET MARKET (ไปตลาด - bpai dtà-làat)
STREET_MARKET_PIXELS = [
    [_, _, R, R, W, W, R, R, W, W, R, R, W, W, _, _],
    [_, R, R, W, W, R, R, W, W, R, R, W, W, R, R, _],
    [R, R, W, W, R, R, W, W, R, R, W, W, R, R, W, W],
    [B, _, _, _, _, _, _, _, _, _, _, _, _, _, _, B],
    [B, _, R, G, Y, R, G, Y, R, G, _, _, S, S, _, B],
    [B, B, B, B, B, B, B, B, B, B, B, _, C, C, _, B],
    [_, B, D, D, D, D, D, D, D, B, _, _, C, C, _, _],
    [_, B, D, D, D, D, D, D, D, B, _, _, D, D, _, _],
]

def render_sprite(pixel_grid, left_indent="  "):
    lines = []
    h = len(pixel_grid)
    w = len(pixel_grid[0])
    for y in range(0, h, 2):
        row_str = left_indent
        top_row = pixel_grid[y]
        bot_row = pixel_grid[y+1] if y+1 < h else [None]*w
        for x in range(w):
            row_str += rgb_block(top_row[x], bot_row[x])
        lines.append(row_str)
    return "\n".join(lines)

def print_flashcard_demo(revealed=False):
    sprite_art = render_sprite(STREET_MARKET_PIXELS, left_indent="│    ")
    
    print("\n\033[1;36m╭─────────────────────── 🧠 LINGUO FLASHCARD ───────────────────────╮\033[0m")
    print("│                                                                   │")
    print(sprite_art)
    print("│    \033[2m[ARCADE ANCHOR: BANGKOK STREET MARKET]\033[0m                         │")
    print("│                                                                   │")
    print("│  \033[1;33m🎯 TARGET CONCEPT:\033[0m  Andare al mercato (Going to the market)      │")
    print("│  \033[1m🇬🇧 English Fill:\033[0m    I am going to \033[1;32m[ the ]\033[0m market tomorrow morning.   │")
    print("│  \033[1m💡 Grammar Anchor:\033[0m  Ricorda: 'the' per posti fisici specifici!    │")
    print("│                                                                   │")
    print("│  ───────────────────────────────────────────────────────────────  │")
    
    if not revealed:
        print("│  \033[1;35m🇹🇭 COME SI DICE IL CONCETTO IN THAI?\033[0m                             │")
        print("│  \033[33m▶ Prova a pronunciarlo a voce prima di svelare la carta...\033[0m      │")
        print("│                                                                   │")
        print("│  \033[1;36m[ PREMI SPAZIO PER SVELARE THAI & ASCOLTARE L'AUDIO (0.8x) ]\033[0m     │")
    else:
        print("│  \033[1;35m🇹🇭 CONCETTO QUOTIDIANO THAI:\033[0m                                     │")
        print("│      \033[1;35mไปตลาด\033[0m  ➔  \033[1;93mbpai dtà-làat\033[0m                                 │")
        print("│                                                                   │")
        print("│  \033[1;36m🎵 SCHEMA DEI TONI (Essenziale per farsi capire):\033[0m                │")
        print("│      • \033[1mไป\033[0m (bpai)     = andare  ➔ \033[1;32m[── TONO MEDIO]\033[0m (voce piana)   │")
        print("│      • \033[1mตลาด\033[0m (dtà-làat) = mercato ➔ \033[1;34m[╲__ TONO BASSO]\033[0m (voce scende)  │")
        print("│                                                                   │")
        print("│  🎧 \033[2mAudio a 0.8x riprodotto con Premwadee (super scandito)!\033[0m        │")
        
    print("\033[1;36m╰───────────────────────────────────────────────────────────────────╯\033[0m\n")

if __name__ == "__main__":
    rev = "--revealed" in sys.argv
    print_flashcard_demo(revealed=rev)
