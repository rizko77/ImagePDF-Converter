import webview
import os
import sys
import fitz
import io
import struct
import ctypes
from PIL import Image
import zipfile
import webbrowser
import time

Image.MAX_IMAGE_PIXELS = None

# Close PyInstaller splash screen if present (compiled mode)
try:
    import pyi_splash
except ImportError:
    pyi_splash = None

# Base directory
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))



# ──────────────────────────────────────────────
#  PSD Writer — creates proper Adobe PSD files
# ──────────────────────────────────────────────
def write_psd(pil_image, output_path, dpi=300):
    """Write a valid PSD file that opens in all Photoshop versions (CS and later)."""
    img = pil_image.convert('RGB')
    width, height = img.size
    r, g, b = img.split()

    with open(output_path, 'wb') as f:
        # ── File Header (26 bytes) ──
        f.write(b'8BPS')                      # Signature
        f.write(struct.pack('>H', 1))         # Version 1
        f.write(b'\x00' * 6)                  # Reserved
        f.write(struct.pack('>H', 3))         # 3 channels (R, G, B)
        f.write(struct.pack('>I', height))    # Rows
        f.write(struct.pack('>I', width))     # Columns
        f.write(struct.pack('>H', 8))         # 8 bits per channel
        f.write(struct.pack('>H', 3))         # Color mode: RGB

        # ── Color Mode Data ──
        f.write(struct.pack('>I', 0))         # No color mode data

        # ── Image Resources (DPI info) ──
        dpi_fixed = dpi * 65536               # 16.16 fixed-point
        res_data = struct.pack('>IHHIHH',
            dpi_fixed, 1, 1,                  # hRes (PPI), hResUnit, widthUnit
            dpi_fixed, 1, 1                   # vRes (PPI), vResUnit, heightUnit
        )
        res_block = bytearray()
        res_block += b'8BIM'                           # Resource signature
        res_block += struct.pack('>H', 0x03ED)         # ID: ResolutionInfo
        res_block += b'\x00\x00'                       # Empty pascal string (padded)
        res_block += struct.pack('>I', len(res_data))  # Data length
        res_block += res_data

        f.write(struct.pack('>I', len(res_block)))
        f.write(res_block)

        # ── Layer and Mask Info ──
        f.write(struct.pack('>I', 0))         # No layers (flattened image)

        # ── Image Data ──
        f.write(struct.pack('>H', 0))         # Compression: 0 = Raw
        f.write(r.tobytes())                  # Red channel
        f.write(g.tobytes())                  # Green channel
        f.write(b.tobytes())                  # Blue channel


# ──────────────────────────────────────────────
#  CDR Writer — Stable CorelDRAW X7 (v17+) 
# ──────────────────────────────────────────────
def write_cdr(pil_image, output_path, dpi=300):
    """
    Creates a stable ZIP-based CDR for X7 and above.
    Uses a flattened structure and mandatory styles.xml for better compatibility.
    """
    w, h = pil_image.size
    mm_w = (w * 25.4) / dpi
    mm_h = (h * 25.4) / dpi

    # Use PNG with NO compression to ensure size and stability
    img_io = io.BytesIO()
    pil_image.save(img_io, format='PNG', compress_level=0)
    png_data = img_io.getvalue()

    with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        # 1. mimetype (Must be first, STORED)
        z.writestr('mimetype', 'application/x-corel-draw', compress_type=zipfile.ZIP_STORED)

        # 2. META-INF/manifest.xml (Proper paths)
        manifest_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">\n'
            '  <manifest:file-entry manifest:full-path="/" manifest:media-type="application/x-corel-draw"/>\n'
            '  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>\n'
            '  <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>\n'
            '  <manifest:file-entry manifest:full-path="image1.png" manifest:media-type="image/png"/>\n'
            '</manifest:manifest>'
        )
        z.writestr('META-INF/manifest.xml', manifest_xml)

        # 3. META-INF/container.xml
        container_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">\n'
            '  <rootfiles>\n'
            '    <rootfile full-path="content.xml" media-type="application/vnd.corel.draw+xml"/>\n'
            '  </rootfiles>\n'
            '</container>'
        )
        z.writestr('META-INF/container.xml', container_xml)

        # 4. styles.xml (Often required)
        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" office:version="1.2">\n'
            '</office:document-styles>'
        )
        z.writestr('styles.xml', styles_xml)

        # 5. content.xml (The drawing structure - FLATTENED path)
        content_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<draw:document xmlns:draw="http://schemas.corel.com/draw/2014/main" '
            'xmlns:svg="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'draw:version="1700">\n'
            f'  <draw:page svg:width="{mm_w:.3f}mm" svg:height="{mm_h:.3f}mm" draw:name="Page 1">\n'
            '    <draw:layer name="Layer 1" draw:printable="true" draw:visible="true">\n'
            f'      <draw:image xlink:href="image1.png" svg:x="0" svg:y="0" '
            f'svg:width="{mm_w:.3f}mm" svg:height="{mm_h:.3f}mm" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/>\n'
            '    </draw:layer>\n'
            '  </draw:page>\n'
            '</draw:document>'
        )
        z.writestr('content.xml', content_xml)

        # 6. image1.png
        z.writestr('image1.png', png_data)


# ──────────────────────────────────────────────
#  Icon helpers for Windows taskbar + title bar


# ──────────────────────────────────────────────
#  Icon helpers for Windows taskbar + title bar
# ──────────────────────────────────────────────
def create_ico_from_png(png_path):
    """Convert PNG to ICO for Windows."""
    ico_path = os.path.splitext(png_path)[0] + '.ico'
    try:
        img = Image.open(png_path)
        img.save(ico_path, format='ICO',
                 sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    except Exception as e:
        print(f"[WARN] ICO creation failed: {e}")
        return None
    return ico_path


def set_window_icon(ico_path, title='PDF Converter Pro'):
    """Apply icon to title bar + Windows taskbar via Win32 API."""
    if not ico_path or not os.path.exists(ico_path):
        print(f"[WARN] ICO not found: {ico_path}")
        return

    import time
    user32 = ctypes.windll.user32

    # Find the pywebview window by its exact title
    hwnd = None
    for attempt in range(20):
        hwnd = user32.FindWindowW(None, title)
        if hwnd:
            print(f"[OK] Found window '{title}' hwnd={hwnd} (attempt {attempt+1})")
            break
        time.sleep(0.3)

    if not hwnd:
        print(f"[WARN] Could not find window '{title}' after 20 attempts")
        return

    try:
        # Load icons at proper sizes
        hicon_sm = user32.LoadImageW(0, ico_path, 1, 16, 16, 0x0010)  # IMAGE_ICON, LR_LOADFROMFILE
        hicon_lg = user32.LoadImageW(0, ico_path, 1, 48, 48, 0x0010)
        print(f"[OK] Loaded icons: small={hicon_sm}, big={hicon_lg}")

        if hicon_sm:
            user32.SendMessageW(hwnd, 0x0080, 0, hicon_sm)  # WM_SETICON, ICON_SMALL
        if hicon_lg:
            user32.SendMessageW(hwnd, 0x0080, 1, hicon_lg)  # WM_SETICON, ICON_BIG
        print("[OK] Icons applied to window")
    except Exception as e:
        print(f"[WARN] set_window_icon SendMessage failed: {e}")


# ──────────────────────────────────────────────
#  Main API exposed to JavaScript via pywebview
# ──────────────────────────────────────────────
class Api:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def open_url(self, url):
        """Open a URL in the default browser."""
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[ERROR] open_url: {e}")

    def select_pdf(self):
        try:
            result = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=True,
                file_types=['PDF files (*.pdf)', 'All files (*.*)']
            )
            if result and len(result) > 0:
                return list(result)
            return []
        except Exception as e:
            print(f"[ERROR] select_pdf: {e}")
            return []

    def select_output_dir(self):
        try:
            result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
            if result and len(result) > 0:
                return str(result[0])
            return None
        except Exception as e:
            print(f"[ERROR] select_output_dir: {e}")
            return None

    def get_pdf_info(self, pdf_paths):
        """Return page count + size info for the file list (used for preview)."""
        infos = []
        for path in (pdf_paths or []):
            try:
                size = os.path.getsize(path) if os.path.exists(path) else 0
                try:
                    doc = fitz.open(path)
                    pages = len(doc)
                    doc.close()
                except Exception:
                    pages = 0
                infos.append({
                    'path': path,
                    'name': os.path.basename(path),
                    'pages': pages,
                    'size_kb': round(size / 1024, 1),
                })
            except Exception as e:
                infos.append({'path': path, 'name': os.path.basename(path),
                              'pages': 0, 'size_kb': 0, 'error': str(e)})
        return infos

    def open_output_folder(self, path):
        """Open folder in Windows Explorer."""
        try:
            if path and os.path.isdir(path):
                os.startfile(path)
                return True
            return False
        except Exception as e:
            print(f"[ERROR] open_output_folder: {e}")
            return False

    def convert_pdf(self, pdf_paths, output_dir, out_format='jpg', dpi=300, quality=92):
        """Convert every page of PDFs into the chosen format."""
        if not pdf_paths or not output_dir:
            return {'status': 'error', 'message': 'Pilih berkas PDF dan folder keluaran terlebih dahulu.'}

        out_format = str(out_format).lower().strip().lstrip('.')
        # 'jpeg' tetap didukung sebagai alias 'jpg'
        if out_format == 'jpeg':
            out_format = 'jpg'
        valid = ('jpg', 'png', 'tif', 'psd', 'cdr', 'ai')
        if out_format not in valid:
            return {'status': 'error', 'message': f'Format tidak didukung: {out_format}'}

        try:
            dpi = int(dpi)
        except Exception:
            dpi = 300
        dpi = max(72, min(600, dpi))

        try:
            quality = int(quality)
        except Exception:
            quality = 92
        quality = max(60, min(100, quality))

        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            pass

        import tempfile
        import shutil
        import datetime

        is_multiple = len(pdf_paths) > 1

        if is_multiple:
            # We will use a temporary directory to store all files, then zip it.
            temp_dir = tempfile.mkdtemp()
            target_dir = temp_dir
        else:
            target_dir = output_dir

        try:
            # Pre-calculate total pages
            total_pages = 0
            docs = []
            for path in pdf_paths:
                try:
                    doc = fitz.open(path)
                    total_pages += len(doc)
                    docs.append((path, doc))
                except Exception as e:
                    print(f"Skipping {path}: {e}")

            if total_pages == 0:
                for _, d in docs:
                    try:
                        d.close()
                    except Exception:
                        pass
                return {'status': 'error', 'message': 'Tidak ada halaman valid pada PDF yang dipilih.'}

            current_page = 0
            
            for path, doc in docs:
                base = os.path.splitext(os.path.basename(path))[0]
                
                for i, page in enumerate(doc):
                    name = f"{base}_page_{i + 1}"

                    # ── AI: PDF satu halaman yang kompatibel dengan Illustrator ──
                    if out_format == 'ai':
                        out_path = os.path.join(target_dir, name + '.ai')
                        tmp = fitz.open()
                        tmp.insert_pdf(doc, from_page=i, to_page=i)
                        tmp.set_metadata({
                            'producer': 'ImagePDF Converter',
                            'creator': 'ImagePDF Converter',
                            'title': name,
                        })
                        tmp.save(out_path, deflate=True)
                        tmp.close()

                    else:
                        # Render page to raster image

                        pix = page.get_pixmap(
                            dpi=dpi,
                            alpha=False
                        )
                        mode = "RGB"
                        pil_img = Image.frombytes(
                            mode,
                            [pix.width, pix.height],
                            pix.samples
                        )

                        if out_format == 'jpg':
                            out_path = os.path.join(target_dir, name + '.jpg')
                            pil_img.convert('RGB').save(
                                out_path, 'JPEG', quality=quality,
                                dpi=(dpi, dpi), optimize=True)

                        elif out_format == 'png':
                            out_path = os.path.join(target_dir, name + '.png')
                            pil_img.save(out_path, 'PNG', dpi=(dpi, dpi))

                        elif out_format == 'tif':
                            out_path = os.path.join(target_dir, name + '.tif')
                            pil_img.save(out_path, 'TIFF', compression='tiff_lzw', dpi=(dpi, dpi))

                        elif out_format == 'psd':
                            out_path = os.path.join(target_dir, name + '.psd')
                            write_psd(pil_img, out_path, dpi=dpi)

                        elif out_format == 'cdr':
                            out_path = os.path.join(target_dir, name + '.cdr')
                            write_cdr(pil_img, out_path, dpi=dpi)

                    current_page += 1
                    pct = int((current_page / total_pages) * 100)
                    try:
                        self._window.evaluate_js(
                            f"updateProgress({pct}, 'Halaman {current_page} dari {total_pages}')"
                        )
                    except Exception:
                        pass

                doc.close()

            ext_label = out_format.upper()
            if out_format == 'ai':
                ext_label = 'AI (.ai)'
            elif out_format == 'cdr':
                ext_label = 'CDR (.cdr)'
            elif out_format == 'psd':
                ext_label = 'PSD (.psd)'
            elif out_format == 'tif':
                ext_label = 'TIF (.tif)'

            if is_multiple:
                # Zip the temp dir
                zip_filename = f"Hasil_Konversi_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                zip_path = os.path.join(output_dir, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zf.write(file_path, arcname)

                # Cleanup temp dir
                shutil.rmtree(temp_dir, ignore_errors=True)

                return {
                    'status': 'success',
                    'message': f"Selesai: {total_pages} halaman -> berkas ZIP ({zip_filename})",
                    'files_count': len(pdf_paths),
                    'zip_name': zip_filename,
                    'total_pages': total_pages,
                }
            else:
                return {
                    'status': 'success',
                    'message': f'Selesai: {total_pages} halaman -> {ext_label}',
                    'files_count': 1,
                    'total_pages': total_pages,
                }

        except Exception as e:
            if is_multiple and 'temp_dir' in locals():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            return {'status': 'error', 'message': f'Konversi gagal: {str(e)}'}




# ──────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────
WINDOW_TITLE = 'ImagePDF Converter'


def on_start():
    icon_ico = os.path.join(BASE_DIR, 'img', 'ikon.ico')

    if os.path.exists(icon_ico):
        set_window_icon(icon_ico, WINDOW_TITLE)

    if pyi_splash:
        try:
            pyi_splash.close()
        except:
            pass


if __name__ == '__main__':

    api = Api()

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            'ImagePDFConverter.1'
        )
    except Exception:
        pass

    index_file = os.path.join(
        BASE_DIR,
        'templates',
        'index.html'
    )

    window = webview.create_window(
        WINDOW_TITLE,
        index_file,
        js_api=api,
        width=1120,
        height=780,
        resizable=True,
        min_size=(980, 680),
    )

    api.set_window(window)

    webview.start(func=on_start)

