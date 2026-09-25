import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path("/Users/sam/Desktop/Linguo_Poem_Demos/mtg_arcade_cards")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# MTG Trading Card Dimensions (Standard ratio 2.5 x 3.5 inches, rendered at 360 x 504 px)
CARD_W = 360
CARD_H = 504

# Palette: Neo Geo / Metal Slug & MTG Artifact Card
BG_BORDER = (24, 26, 32)        # Dark Gunmetal / Arcade Chassis
BORDER_GOLD = (205, 160, 75)    # Vintage Gold / Brass Card Trim
INNER_FRAME = (35, 38, 48)      # Slate Inner Frame
TEXTBOX_BG = (22, 24, 30)       # Dark Textbox
TEXTBOX_BORDER = (70, 75, 90)   # Metallic Divider
TEXT_GOLD = (240, 200, 110)     # Header Gold
TEXT_WHITE = (235, 235, 240)    # Rules White
TEXT_FLAVOR = (165, 175, 190)   # Italic Flavor Grey
ACCENT_GREEN = (60, 200, 120)   # Correct / Level-up
ACCENT_RED = (235, 75, 75)      # Error alert

def draw_neo_geo_art_box(draw, x0, y0, x1, y1):
    # Metal Slug / Neo Geo gritty arcade military-market palette
    # Dark asphalt ground, gritty metal stall, neon yellow/orange lantern glow
    w = x1 - x0
    h = y1 - y0
    
    # Sky / Background gradient (dusk purple-orange arcade sky)
    for y in range(y0, y1):
        ratio = (y - y0) / h
        r = int(30 * (1 - ratio) + 80 * ratio)
        g = int(25 * (1 - ratio) + 40 * ratio)
        b = int(55 * (1 - ratio) + 30 * ratio)
        draw.line([(x0, y), (x1, y)], fill=(r, g, b))
        
    # Metal Slug style city silhouettes & wires in background
    draw.rectangle([x0 + 20, y0 + 15, x0 + 60, y1 - 25], fill=(30, 25, 35))
    draw.rectangle([x0 + 80, y0 + 30, x0 + 130, y1 - 25], fill=(25, 22, 32))
    draw.rectangle([x0 + 200, y0 + 10, x0 + 260, y1 - 25], fill=(28, 24, 34))

    # Street ground (dark cobblestone / asphalt)
    draw.rectangle([x0, y1 - 25, x1, y1], fill=(20, 22, 26))
    draw.line([(x0, y1 - 25), (x1, y1 - 25)], fill=(60, 65, 75), width=2)

    # Street Food / Market Stall (Metal Slug gritty palette: olive drab, rusted metal, warm canopy)
    stall_x = x0 + 70
    stall_w = 150
    # Canvas canopy (worn olive & amber stripes)
    for i, sx in enumerate(range(stall_x, stall_x + stall_w, 15)):
        color = (190, 100, 35) if i % 2 == 0 else (65, 80, 55)
        draw.polygon([(sx, y0 + 55), (sx + 15, y0 + 55), (sx + 10, y0 + 72), (sx - 5, y0 + 72)], fill=color)
    draw.line([(stall_x - 5, y0 + 72), (stall_x + stall_w, y0 + 72)], fill=(40, 45, 35), width=2)
    
    # Wooden/Steel Counter
    draw.rectangle([stall_x + 10, y0 + 75, stall_x + stall_w - 20, y1 - 25], fill=(50, 45, 40), outline=(85, 75, 65), width=2)
    
    # Glowing Street Lantern (Warm Neon Amber Glow)
    lx, ly = stall_x + 25, y0 + 60
    draw.ellipse([lx - 12, ly - 12, lx + 12, ly + 12], fill=(255, 180, 50, 60))
    draw.ellipse([lx - 6, ly - 6, lx + 6, ly + 6], fill=(255, 230, 130))
    
    # Crates with goods (tropical fruits / supplies)
    draw.rectangle([stall_x + 20, y0 + 85, stall_x + 50, y0 + 105], fill=(130, 80, 45), outline=(70, 40, 20))
    draw.rectangle([stall_x + 60, y0 + 85, stall_x + 90, y0 + 105], fill=(130, 80, 45), outline=(70, 40, 20))
    # Fruits
    draw.ellipse([stall_x + 25, y0 + 80, stall_x + 35, y0 + 90], fill=(220, 50, 40))
    draw.ellipse([stall_x + 35, y0 + 82, stall_x + 45, y0 + 92], fill=(240, 150, 30))
    draw.ellipse([stall_x + 68, y0 + 80, stall_x + 82, y0 + 92], fill=(60, 180, 70))

    # Pixel Soldier / Traveler Sprite (Neo Geo style silhouette holding a bag)
    tx = stall_x + stall_w + 10
    draw.rectangle([tx, y1 - 65, tx + 16, y1 - 45], fill=(80, 95, 60))    # Vest
    draw.rectangle([tx + 2, y1 - 78, tx + 14, y1 - 66], fill=(225, 180, 140)) # Face
    draw.rectangle([tx, y1 - 83, tx + 16, y1 - 77], fill=(45, 55, 35))     # Helmet / Cap
    draw.rectangle([tx + 3, y1 - 44, tx + 13, y1 - 25], fill=(40, 45, 40))  # Trousers

def render_mtg_card(is_revealed=False):
    card = Image.new("RGBA", (CARD_W, CARD_H), BG_BORDER)
    draw = ImageDraw.Draw(card)

    # 1. Outer Card Trim (Gold / Brass Inset)
    draw.rounded_rectangle([6, 6, CARD_W - 7, CARD_H - 7], radius=14, outline=BORDER_GOLD, width=3)
    draw.rounded_rectangle([12, 12, CARD_W - 13, CARD_H - 13], radius=10, fill=INNER_FRAME)

    # 2. Header Box (Card Name & CEFR Mana Cost)
    draw.rounded_rectangle([20, 20, CARD_W - 21, 54], radius=6, fill=TEXTBOX_BG, outline=BORDER_GOLD, width=1)
    
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
        font_badge = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
        font_type = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 11)
        font_text = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
        font_flavor = ImageFont.truetype("/System/Library/Fonts/Times.ttc", 11)
        font_thai = ImageFont.truetype("/System/Library/Fonts/Supplemental/Ayuthaya.ttf", 15)
        font_pt = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
    except Exception:
        font_title = font_badge = font_type = font_text = font_flavor = font_thai = font_pt = ImageFont.load_default()

    # Title & Badge
    draw.text((32, 28), "STREET MARKET", fill=TEXT_GOLD, font=font_title)
    # Mana / CEFR Cost Badge [B1]
    draw.rounded_rectangle([CARD_W - 68, 25, CARD_W - 28, 49], radius=12, fill=(45, 75, 130), outline=BORDER_GOLD, width=1)
    draw.text((CARD_W - 58, 29), "B1", fill=(255, 255, 255), font=font_badge)

    # 3. Art Window (Neo Geo Arcade Scene)
    art_x0, art_y0 = 20, 60
    art_x1, art_y1 = CARD_W - 21, 220
    draw.rectangle([art_x0 - 1, art_y0 - 1, art_x1 + 1, art_y1 + 1], outline=BORDER_GOLD, width=2)
    draw_neo_geo_art_box(draw, art_x0, art_y0, art_x1, art_y1)

    # 4. Type Line
    draw.rounded_rectangle([20, 226, CARD_W - 21, 248], radius=4, fill=TEXTBOX_BG, outline=TEXTBOX_BORDER, width=1)
    draw.text((28, 230), "Survival Thai • Grammar: Articles", fill=TEXT_GOLD, font=font_type)

    # 5. Text Box (Rules & Knowledge)
    draw.rounded_rectangle([20, 254, CARD_W - 21, CARD_H - 45], radius=6, fill=TEXTBOX_BG, outline=BORDER_GOLD, width=1)
    
    if not is_revealed:
        # FRONTE (Active Recall Challenge)
        draw.text((30, 268), "🇬🇧 ENGLISH CHALLENGE:", fill=TEXT_GOLD, font=font_title)
        draw.text((30, 295), "I am going to [ ? ] market tomorrow.", fill=TEXT_WHITE, font=font_text)
        
        draw.line([(30, 330), (CARD_W - 30, 330)], fill=TEXTBOX_BORDER, width=1)
        
        draw.text((30, 345), "🇹🇭 THAI MYSTERY CONCEPT:", fill=(230, 140, 60), font=font_title)
        draw.text((30, 375), "Come si dice 'Andare al mercato'?", fill=TEXT_FLAVOR, font=font_text)
        draw.text((30, 400), "▶ Prova a formulare il tono a voce!", fill=TEXT_GOLD, font=font_flavor)
        
        draw.rounded_rectangle([40, 425, CARD_W - 41, 450], radius=4, fill=(35, 50, 80))
        draw.text((58, 430), "[ PREMI PER SVELARE IL RETRO ]", fill=TEXT_WHITE, font=font_type)
    else:
        # RETRO (Revealed Master Card)
        draw.text((30, 264), "✅ CORRETTO:", fill=ACCENT_GREEN, font=font_type)
        draw.text((30, 280), "I am going to the market tomorrow.", fill=TEXT_WHITE, font=font_text)
        
        draw.text((30, 305), "📖 BRITISH COUNCIL RULE:", fill=TEXT_GOLD, font=font_type)
        draw.text((30, 320), "I luoghi fisici standard richiedono", fill=TEXT_FLAVOR, font=font_text)
        draw.text((30, 336), "l'articolo determinativo 'the'.", fill=TEXT_FLAVOR, font=font_text)
        
        draw.line([(30, 358), (CARD_W - 30, 358)], fill=TEXTBOX_BORDER, width=1)
        
        draw.text((30, 368), "🇹🇭 SURVIVAL THAI BRICK:", fill=(230, 140, 60), font=font_type)
        draw.text((30, 386), "ไปตลาด", fill=(255, 140, 180), font=font_thai)
        draw.text((120, 388), "bpai dtà-làat", fill=TEXT_GOLD, font=font_text)
        
        # Flavor text (Level-up alternative)
        draw.text((30, 415), "🚀 \"I'll be heading down to the local market.\"", fill=TEXT_FLAVOR, font=font_flavor)

    # 6. Power / Toughness Box (MTG Style: Bottom-Right Badge for Tones)
    pt_x0, pt_y0 = CARD_W - 110, CARD_H - 40
    pt_x1, pt_y1 = CARD_W - 20, CARD_H - 12
    draw.rounded_rectangle([pt_x0, pt_y0, pt_x1, pt_y1], radius=8, fill=(45, 50, 65), outline=BORDER_GOLD, width=2)
    # Mid tone / Low tone badge (M / L)
    draw.text((pt_x0 + 15, pt_y0 + 5), "TONI: M / L", fill=TEXT_GOLD, font=font_pt)

    return card

if __name__ == "__main__":
    fronte = render_mtg_card(is_revealed=False)
    retro = render_mtg_card(is_revealed=True)
    
    f_path = OUT_DIR / "CARD_01_STREET_MARKET_FRONTE.png"
    r_path = OUT_DIR / "CARD_01_STREET_MARKET_RETRO.png"
    
    fronte.save(str(f_path))
    retro.save(str(r_path))
    
    print(f"✅ Carta MTG Fronte salvata in: {f_path}")
    print(f"✅ Carta MTG Retro salvata in: {r_path}")
