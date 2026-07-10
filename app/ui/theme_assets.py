"""Gradientes e ícones para a UI (Pillow + CTkImage)."""

from __future__ import annotations

from PIL import Image, ImageDraw
import customtkinter as ctk


def _hex_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip('#')
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _horizontal_gradient(size: tuple[int, int], left: str, right: str) -> Image.Image:
    width, height = size
    start = _hex_rgb(left)
    end = _hex_rgb(right)
    img = Image.new('RGBA', (width, height))
    pixels = img.load()
    for x in range(width):
        ratio = x / max(width - 1, 1)
        r = int(start[0] + (end[0] - start[0]) * ratio)
        g = int(start[1] + (end[1] - start[1]) * ratio)
        b = int(start[2] + (end[2] - start[2]) * ratio)
        for y in range(height):
            pixels[x, y] = (r, g, b, 255)
    return img


def rounded_gradient_image(
    width: int,
    height: int,
    color_left: str,
    color_right: str,
    *,
    radius: int = 10,
) -> Image.Image:
    width = max(width, 2)
    height = max(height, 2)
    grad = _horizontal_gradient((width, height), color_left, color_right)
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=255)
    grad.putalpha(mask)
    return grad


def gradient_ctk_image(
    width: int,
    height: int,
    color_left: str,
    color_right: str,
    *,
    radius: int = 10,
) -> ctk.CTkImage:
    img = rounded_gradient_image(width, height, color_left, color_right, radius=radius)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(width, height))
