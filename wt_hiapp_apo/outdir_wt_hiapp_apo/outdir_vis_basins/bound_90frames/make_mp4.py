# tga_to_png_then_mp4_whitebg.py
from glob import glob
import os, shutil, re
import numpy as np
from PIL import Image
import imageio.v2 as iio_v2  # streaming writer
import imageio.v3 as iio

# ---------- Settings ----------
INPUT_GLOB   = "./*.tga"
TMP_DIR      = "_png_frames"
OUTPUT_MP4   = "out_whitebg.mp4"
FPS = 2                          # 0.5 sec per frame
BG_COLOR = (255, 255, 255)       # white background
KEEP_PNG = False
# --------------------------------

def natural_key(s): 
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def convert_to_png_whitebg(paths, outdir):
    if os.path.exists(outdir): 
        shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)

    count = 0
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGBA")
        bg = Image.new("RGBA", im.size, BG_COLOR + (255,))
        merged = Image.alpha_composite(bg, im).convert("RGB")  # white bg
        out_path = os.path.join(outdir, f"frame_{i:06d}.png")
        merged.save(out_path, format="PNG", compress_level=0)
        count += 1
    return count

def stream_encode_h264(png_dir, out_path):
    pngs = sorted(glob(os.path.join(png_dir, "frame_*.png")))
    if not pngs:
        raise SystemExit("No PNG frames to encode.")

    writer = iio_v2.get_writer(
        out_path,
        fps=FPS,
        codec="libx264",
        ffmpeg_params=[
            "-r", str(FPS),
            "-crf", "12",            # lower = better quality
            "-preset", "slow",
            "-pix_fmt", "yuv420p",   # most compatible
            "-profile:v", "high",
            "-tune", "stillimage",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-g", "2", "-x264-params", "scenecut=0",
        ],
    )
    try:
        for p in pngs:
            frame = iio.imread(p)
            if frame.ndim == 2:  # grayscale → RGB
                frame = np.repeat(frame[:, :, None], 3, axis=2)
            elif frame.ndim == 3 and frame.shape[2] == 4:  # RGBA → RGB
                frame = frame[:, :, :3]
            writer.append_data(frame.astype(np.uint8, copy=False))
    finally:
        writer.close()

def main():
    files = sorted(glob(INPUT_GLOB), key=natural_key)
    if not files:
        raise SystemExit(f"No .tga files found for {INPUT_GLOB}")

    print(f"Found {len(files)} TGA files, converting to PNG with white background…")
    count = convert_to_png_whitebg(files, TMP_DIR)
    print(f"Saved {count} PNG frames in {TMP_DIR}")

    print("Encoding MP4 (H.264, BT.709)…")
    stream_encode_h264(TMP_DIR, OUTPUT_MP4)
    print(f"Wrote {OUTPUT_MP4}")

    if not KEEP_PNG:
        shutil.rmtree(TMP_DIR)
        print("Cleaned up temporary PNGs.")

if __name__ == "__main__":
    main()
