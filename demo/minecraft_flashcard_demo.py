import os
import io
import base64
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Generate authentic 16x16 Minecraft texture blocks procedurally

def create_grass_block():
    img = Image.new("RGBA", (16, 16))
    random.seed(42) # Deterministic Minecraft seed
    # Dirt base
    for y in range(16):
        for x in range(16):
            # Brown dirt variations
            v = random.choice([
                (134, 96, 67), (115, 84, 56), (145, 107, 75), (105, 75, 48)
            ])
            img.putpixel((x, y), v)
    # Grass top (3-4 pixels deep with classic Minecraft drip teeth)
    for x in range(16):
        drip = 3 + (x % 3 == 0) + (x % 5 == 0)
        for y in range(drip):
            v = random.choice([
                (86, 125, 44), (98, 143, 50), (74, 110, 37), (110, 160, 56)
            ])
            img.putpixel((x, y), v)
    return img

def create_wood_plank():
    img = Image.new("RGBA", (16, 16))
    random.seed(101)
    for y in range(16):
        is_border = (y in (0, 4, 8, 12, 15))
        for x in range(16):
            if is_border:
                c = (140, 100, 60)
            else:
                c = random.choice([(162, 120, 75), (175, 130, 82), (150, 110, 68)])
            img.putpixel((x, y), c)
    return img

def create_steve_avatar():
    # 2D Minecraft character (16x24 pixels)
    img = Image.new("RGBA", (16, 24), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Hair (Dark Brown)
    draw.rectangle([4, 0, 11, 2], fill=(60, 40, 25))
    # Face (Skin)
    draw.rectangle([4, 3, 11, 7], fill=(225, 175, 140))
    # Eyes (Blue & White)
    img.putpixel((5, 5), (255, 255, 255))
    img.putpixel((6, 5), (40, 80, 180))
    img.putpixel((9, 5), (40, 80, 180))
    img.putpixel((10, 5), (255, 255, 255))
    # Nose / Mouth
    img.putpixel((7, 6), (180, 120, 90))
    img.putpixel((8, 6), (180, 120, 90))
    draw.rectangle([6, 7, 9, 7], fill=(120, 70, 50))
    # Shirt (Cyan Blue)
    draw.rectangle([4, 8, 11, 15], fill=(35, 160, 180))
    # Arms (Skin / Sleeves)
    draw.rectangle([2, 8, 3, 10], fill=(35, 160, 180))
    draw.rectangle([2, 11, 3, 14], fill=(225, 175, 140))
    draw.rectangle([12, 8, 13, 10], fill=(35, 160, 180))
    draw.rectangle([12, 11, 13, 14], fill=(225, 175, 140))
    # Pants (Dark Blue)
    draw.rectangle([4, 16, 11, 21], fill=(45, 55, 140))
    # Shoes (Dark Grey)
    draw.rectangle([4, 22, 11, 23], fill=(80, 80, 85))
    return img

def create_minecraft_flashcard(eng_text="I am going to the market.", thai_text="ไปตลาด (bpai dtà-làat)", grammar_tip="Use 'the' for specific physical locations!"):
    # 2D Minecraft scene canvas (320x180 pixels, scales up crisp with nearest neighbor)
    W, H = 320, 180
    canvas = Image.new("RGBA", (W, H), (145, 195, 245, 255)) # Minecraft sky blue
    draw = ImageDraw.Draw(canvas)

    # 1. Cloud
    draw.rectangle([40, 20, 100, 35], fill=(245, 250, 255, 240))
    draw.rectangle([55, 15, 85, 40], fill=(245, 250, 255, 240))
    draw.rectangle([200, 25, 280, 42], fill=(245, 250, 255, 220))

    # 2. Sun (Square Minecraft Sun)
    draw.rectangle([270, 10, 305, 45], fill=(255, 255, 180))

    # 3. Ground (Grass & Dirt blocks)
    grass = create_grass_block()
    plank = create_wood_plank()
    steve = create_steve_avatar()

    # Draw 2 rows of terrain
    for col in range(0, W, 16):
        canvas.paste(grass, (col, 132))
        canvas.paste(grass, (col, 148))
        canvas.paste(grass, (col, 164))

    # 4. Small Market Stall (Wooden Planks & Striped Wool)
    # Legs
    for y in range(84, 132, 16):
        canvas.paste(plank, (160, y))
        canvas.paste(plank, (256, y))
    # Countertop
    for x in range(160, 272, 16):
        canvas.paste(plank, (x, 100))
    # Red/White Wool Awning
    for i, x in enumerate(range(144, 288, 16)):
        wool_color = (220, 50, 50) if i % 2 == 0 else (245, 245, 245)
        draw.rectangle([x, 68, x + 15, 83], fill=wool_color)

    # 5. Place Steve Avatar
    canvas.paste(steve, (90, 108), steve)

    # 6. Minecraft Wooden Signboard (HUD Banner on top)
    draw.rectangle([12, 10, 240, 55], fill=(130, 90, 50), outline=(80, 55, 30), width=2)
    draw.rectangle([15, 13, 237, 52], fill=(185, 140, 90))

    try:
        font_eng = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
        font_thai = ImageFont.truetype("/System/Library/Fonts/Supplemental/Ayuthaya.ttf", 12)
        font_tip = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
    except Exception:
        font_eng = font_thai = font_tip = ImageFont.load_default()

    draw.text((22, 16), "🇬🇧 " + eng_text, fill=(40, 25, 10), font=font_eng)
    draw.text((22, 33), "🇹🇭 " + thai_text, fill=(90, 30, 10), font=font_thai)

    # Scale 2x with NEAREST NEIGHBOR for super crisp pixel-art look
    scaled = canvas.resize((W * 2, H * 2), Image.Resampling.NEAREST)
    return scaled

if __name__ == "__main__":
    out_path = Path("/Users/sam/Desktop/Linguo_Poem_Demos/minecraft_flashcard_market.png")
    img = create_minecraft_flashcard()
    img.save(str(out_path))
    print(f"✅ Minecraft 2D Flashcard image saved to: {out_path}")

    # Display directly inline in iTerm2 terminal!
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_data = base64.b64encode(buf.getvalue()).decode("ascii")
    # iTerm2 inline image escape sequence
    print(f"\n\033]1337;File=inline=1;width=640px:{b64_data}\a\n")
