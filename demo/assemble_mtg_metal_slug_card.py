import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ART_IMAGE_PATH = Path("/Users/sam/.gemini/antigravity-cli/brain/d5c4f072-ad2f-4f70-8120-bbb36bd8e1e1/arcade_market_gag_1790360680716.jpg")
OUT_DIR = Path("/Users/sam/Desktop/Linguo_Poem_Demos/mtg_arcade_cards")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# High-Res MTG Card dimensions: 480 x 672 px (Standard MTG 2.5 x 3.5 ratio)
CARD_W = 480
CARD_H = 672

BG_BORDER = (18, 20, 26)        # Deep Gunmetal
BORDER_GOLD = (215, 170, 75)    # Brass / Gold Frame
INNER_FRAME = (28, 31, 40)      # Slate Background
TEXTBOX_BG = (15, 17, 22)       # Text Box Dark
TEXTBOX_BORDER = (65, 70, 85)   # Border
TEXT_GOLD = (245, 205, 110)     # Header Gold
TEXT_WHITE = (240, 240, 245)    # Text
TEXT_FLAVOR = (175, 185, 200)   # Flavor Grey
ACCENT_GREEN = (70, 215, 130)   # Correct Green
ACCENT_RED = (245, 80, 80)      # Alert Red

def render_master_card(is_revealed=False):
    card = Image.new("RGBA", (CARD_W, CARD_H), BG_BORDER)
    draw = ImageDraw.Draw(card)

    # 1. Outer Metallic Border (MTG Card Bevel)
    draw.rounded_rectangle([8, 8, CARD_W - 9, CARD_H - 9], radius=18, outline=BORDER_GOLD, width=4)
    draw.rounded_rectangle([16, 16, CARD_W - 17, CARD_H - 17], radius=14, fill=INNER_FRAME, outline=(40, 45, 55), width=2)

    # 2. Header Box (Title & CEFR Cost Badge)
    draw.rounded_rectangle([26, 26, CARD_W - 27, 70], radius=8, fill=TEXTBOX_BG, outline=BORDER_GOLD, width=2)
    
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        font_badge = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 17)
        font_type = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
        font_body = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
        font_rule = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
        font_flavor = ImageFont.truetype("/System/Library/Fonts/Times.ttc", 13)
        font_thai = ImageFont.truetype("/System/Library/Fonts/Supplemental/Ayuthaya.ttf", 20)
        font_pt = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
    except Exception:
        font_title = font_badge = font_type = font_body = font_rule = font_flavor = font_thai = font_pt = ImageFont.load_default()

    draw.text((40, 36), "THE MARKET STAMP", fill=TEXT_GOLD, font=font_title)
    
    # CEFR Badge in top right [B1]
    draw.rounded_rectangle([CARD_W - 90, 32, CARD_W - 38, 64], radius=16, fill=(35, 65, 120), outline=BORDER_GOLD, width=2)
    draw.text((CARD_W - 77, 37), "B1", fill=(255, 255, 255), font=font_badge)

    # 3. Art Window: Embed the Metal Slug Neo Geo artwork!
    art_x0, art_y0 = 26, 78
    art_x1, art_y1 = CARD_W - 27, 340
    art_w = art_x1 - art_x0
    art_h = art_y1 - art_y0

    if ART_IMAGE_PATH.exists():
        raw_art = Image.open(str(ART_IMAGE_PATH)).convert("RGBA")
        # Crop & resize to fit art window
        art_fitted = raw_art.resize((art_w, art_h), Image.Resampling.LANCZOS)
        card.paste(art_fitted, (art_x0, art_y0))
    
    # Frame around the art
    draw.rectangle([art_x0 - 2, art_y0 - 2, art_x1 + 1, art_y1 + 1], outline=BORDER_GOLD, width=3)

    # 4. Type Line
    draw.rounded_rectangle([26, 348, CARD_W - 27, 378], radius=6, fill=TEXTBOX_BG, outline=TEXTBOX_BORDER, width=1)
    draw.text((36, 354), "Arcade Encounter • Grammar: Definite Article", fill=TEXT_GOLD, font=font_type)

    # 5. Text Box (Rules / Challenge)
    draw.rounded_rectangle([26, 386, CARD_W - 27, CARD_H - 58], radius=8, fill=TEXTBOX_BG, outline=BORDER_GOLD, width=2)

    if not is_revealed:
        # FRONTE (The Fun Challenge)
        draw.text((38, 400), "🇬🇧 MISSION CHALLENGE:", fill=TEXT_GOLD, font=font_title)
        draw.text((38, 432), "Marco needs to enter! Fill the gap:", fill=TEXT_WHITE, font=font_body)
        draw.text((38, 458), "» \"I am going to [  ?  ] market tomorrow.\"", fill=(255, 220, 100), font=font_body)

        draw.line([(38, 492), (CARD_W - 38, 492)], fill=TEXTBOX_BORDER, width=1)

        draw.text((38, 504), "🇹🇭 THAI SURVIVAL MYSTERY:", fill=(235, 145, 60), font=font_title)
        draw.text((38, 534), "Qual è il mattone da 2 parole per 'Andare al mercato'?", fill=TEXT_FLAVOR, font=font_rule)
        draw.text((38, 554), "▶ Ricordi i 2 toni? Dillo a voce alta prima di girare!", fill=TEXT_GOLD, font=font_flavor)

        # Action callout
        draw.rounded_rectangle([50, 580, CARD_W - 51, 606], radius=6, fill=(35, 55, 95))
        draw.text((88, 586), "🕹️ [ PREMI PER TIMBRARE & SVELARE IL RETRO ]", fill=TEXT_WHITE, font=font_type)
    else:
        # RETRO (The Gag Explained & Knowledge Mastered)
        draw.text((38, 396), "✅ SOLUZIONE TIMBRATA:", fill=ACCENT_GREEN, font=font_type)
        draw.text((38, 414), "\"I am going to THE market tomorrow.\"", fill=TEXT_WHITE, font=font_body)

        draw.text((38, 442), "📖 LA REGOLA DELLA PROFESSORESSA:", fill=TEXT_GOLD, font=font_type)
        draw.text((38, 458), "In inglese non puoi 'andare a mercato'. I posti fisici", fill=TEXT_FLAVOR, font=font_rule)
        draw.text((38, 474), "richiedono il timbro 'THE' (the bank, the station, the market)!", fill=TEXT_FLAVOR, font=font_rule)

        draw.line([(38, 496), (CARD_W - 38, 496)], fill=TEXTBOX_BORDER, width=1)

        draw.text((38, 506), "🇹🇭 MATTONE THAI (2 PAROLE):", fill=(235, 145, 60), font=font_type)
        draw.text((38, 528), "ไปตลาด", fill=(255, 130, 180), font=font_thai)
        draw.text((150, 532), "bpai dtà-làat", fill=TEXT_GOLD, font=font_body)

        draw.text((38, 558), "• ไป = andare (Tono Medio) | ตลาด = mercato (Tono Basso)", fill=TEXT_WHITE, font=font_rule)

        # Gag Flavor Text
        draw.text((38, 584), "💬 \"NO 'THE', NO ENTRY! Stamp approved, soldier!\"", fill=(240, 180, 90), font=font_flavor)

    # 6. Power / Toughness Box (Bottom-Right: Thai Tones)
    pt_x0, pt_y0 = CARD_W - 145, CARD_H - 50
    pt_x1, pt_y1 = CARD_W - 27, CARD_H - 16
    draw.rounded_rectangle([pt_x0, pt_y0, pt_x1, pt_y1], radius=10, fill=(40, 48, 65), outline=BORDER_GOLD, width=2)
    draw.text((pt_x0 + 16, pt_y0 + 8), "TONI: M / L", fill=TEXT_GOLD, font=font_pt)

    return card

if __name__ == "__main__":
    f_card = render_master_card(is_revealed=False)
    r_card = render_master_card(is_revealed=True)

    f_out = OUT_DIR / "MTG_METAL_SLUG_CARD_FRONTE.png"
    r_out = OUT_DIR / "MTG_METAL_SLUG_CARD_RETRO.png"

    f_card.save(str(f_out))
    r_card.save(str(r_out))

    print(f"🎉 Front Card generata: {f_out}")
    print(f"🎉 Back Card generata:  {r_out}")
