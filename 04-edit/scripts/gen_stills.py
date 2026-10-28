"""Photoreal stills for the stock-footage moments AB uses (money close-ups, a burning bill, a trophy, an X-ray brain,
a $100 bill for the money drop), generated with LCM Dreamshaper v7 (MIT licence) on the CPU.

    python gen_stills.py OUT_DIR [name ...]
"""
import os, sys, time
import torch
from diffusers import DiffusionPipeline

MODEL = "/home/user/work/models/lcm"
NEG = ""
PROMPTS = {
    # name: (prompt, width, height, seed)
    "money_pile": ("macro photo of a messy pile of green US hundred dollar banknotes filling the frame, close up, shallow "
                   "depth of field, warm cinematic light, 8k, realistic", 768, 512, 11),
    "money_fan": ("photo of many hundred dollar bills fanned out and scattered on a dark wooden table, green and beige "
                  "banknotes, cinematic warm lighting, high contrast, shallow depth of field, 35mm", 768, 512, 33),
    "money_close": ("extreme close up photo of a stack of new US hundred dollar bills, blue security ribbon, green ink, "
                    "cinematic lighting, high detail, shallow depth of field", 768, 512, 17),
    "cash_counter": ("photo of a bill counting machine with a stack of green hundred dollar bills flying through it, dark "
                     "background, cinematic lighting, high contrast", 768, 512, 19),
    "trophy_white": ("a single gold trophy cup, product photo, centered, isolated on a pure white background, soft shadow",
                     512, 640, 13),
    "money_pile2": ("close-up photo of stacks of hundred dollar bills on a table, cinematic, shallow depth of field, "
                    "dark moody lighting, realistic", 768, 512, 23),
    "bill_front": ("a single US one hundred dollar bill, flat, front side, top view, isolated on pure white background, "
                   "high detail product photo", 768, 384, 5),
    "bill_back": ("a single US one hundred dollar bill, flat, back side with Independence Hall, top view, isolated on pure "
                  "white background, high detail product photo", 768, 384, 9),
    "burning_bill": ("a hundred dollar bill burning, bright orange flames, black background, dramatic, studio photo, realistic",
                     512, 768, 4),
    "burning_bill2": ("close-up photo of a single US hundred dollar bill held upright, its bottom edge on fire with bright "
                      "orange flames and glowing embers, pure black background, dramatic studio lighting, realistic", 512, 768, 27),
    "burning_bill3": ("a hundred dollar banknote burning, curling paper, orange flames rising from the bottom, isolated on a "
                      "black background, cinematic macro photo", 512, 768, 55),
    "trophy": ("a shiny gold trophy cup, 3D render, studio lighting, isolated on pure white background", 512, 640, 3),
    "brain": ("glowing blue x-ray hologram of a human brain, 3D render, isolated on pure black background", 640, 512, 8),
    "clock": ("a red twin bell alarm clock, 3D render, isolated on pure white background", 512, 512, 6),
    "magnifier": ("a magnifying glass with a black handle, 3D render, isolated on pure white background", 512, 512, 2),
    "trader_screens": ("a trader from behind looking at multiple monitors with candlestick charts at night, dark room, "
                       "cinematic, moody, realistic photo", 768, 512, 12),
    "money_counter": ("a money counting machine counting hundred dollar bills, close up, cinematic, realistic photo", 768, 512, 7),
    "chalkboard": ("dark chalkboard covered in math formulas, moody cinematic close up photo", 768, 512, 14),
    "warehouse": ("a young man working in a warehouse lifting boxes, cinematic, moody light, realistic photo", 768, 512, 21),
    "delivery": ("food delivery driver on a scooter at night in the city, cinematic, moody, realistic photo", 768, 512, 31),
    "night_car": ("a young man sitting alone in his car at night, head in hands, city lights, cinematic, moody, realistic photo",
                  768, 512, 41),
    "graduation": ("a black graduation cap on a white background, 3D render, studio lighting", 512, 512, 2),
    "airplane": ("a passenger airplane flying above clouds at sunset, cinematic photo", 768, 512, 9),
}


def main():
    out = sys.argv[1]
    names = sys.argv[2:] or list(PROMPTS)
    os.makedirs(out, exist_ok=True)
    torch.set_num_threads(os.cpu_count() or 4)
    pipe = DiffusionPipeline.from_pretrained(MODEL, torch_dtype=torch.float32, safety_checker=None)
    pipe.set_progress_bar_config(disable=True)
    for n in names:
        if os.path.exists(f"{out}/{n}.png"):
            continue
        prompt, w, h, seed = PROMPTS[n]
        t = time.time()
        g = torch.Generator().manual_seed(seed)
        im = pipe(prompt, num_inference_steps=int(os.environ.get('LCM_STEPS', 6)), guidance_scale=8.0, width=w, height=h, generator=g,
                  lcm_origin_steps=50, output_type="pil").images[0]
        im.save(f"{out}/{n}.png")
        print(n, f"{time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
