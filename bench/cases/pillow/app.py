from PIL import Image, ImageDraw, ImageFont


def thumbnail(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    return img.resize(size, Image.ANTIALIAS)


def text_width(text: str) -> int:
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    return draw.textsize(text, font=ImageFont.load_default())[0]
