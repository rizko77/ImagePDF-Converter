# ImagePDF Converter

A Windows desktop application for converting PDF pages into JPG, PNG, TIF, PSD, CDR, or AI formats. The user interface is built using HTML and runs within a `pywebview` window.

Each PDF page results in a single file. If multiple PDF files are selected, all output files are automatically bundled into a single ZIP archive in the output folder.

## Features

- Select one or multiple PDF files at once.
- Display the page count and file size for each PDF prior to conversion.
- Configure render resolution: 150, 200, 300, or 600 DPI.
- Adjust JPG quality from 60 to 100 (default is 92).
- Choose from the following output formats: JPG, PNG, TIF, PSD, CDR, or AI.
- Monitor conversion progress and open the output folder directly from the application.

PSD files are generated as flattened 8-bit RGB images. CDR files contain a PNG image placed on a single page. AI files are generated as single-page PDFs that can be opened in Adobe Illustrator; they are not native AI documents containing converted vector objects.

## Project Structure

```text
ImageConverter/
├── main.py                    # Application logic and PDF conversion
├── templates/
│   └── index.html             # Application user interface
├── img/
│   ├── ikon.ico               # Windows icon
│   ├── ikon.png               # Icon for the user interface
│   └── splash.png             # Splash screen image
├── ImagePDF Converter.spec    # PyInstaller build configuration
├── app.manifest               # Windows application manifest
├── version.txt                # Windows file version information
├── requirements.txt           # Python dependencies
└── README.md
```

The `build/` and `dist/` folders are created by PyInstaller. They are not part of the application source code and can be regenerated during the build process.

## Requirements

- Windows 10 or Windows 11.
- Python 3.10 or later. The build included in this project was created using Python 3.12; please use Python 3.12 to ensure the most consistent build results.
- Microsoft Edge WebView2 Runtime is required to display the `pywebview` window. This runtime is typically pre-installed on Windows 10/11. If the application window fails to open, please install the WebView2 Runtime from the official Microsoft website.

## Installation and running from source code

Open PowerShell in the project folder, then create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents the script from running, execute the following command in the current session, then attempt to activate the virtual environment again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the application:

```powershell
python main.py
```

## How to use

1. Click **Add PDF File(s)** and select one or more PDF files.
2. Choose an output format. For JPG, adjust the quality settings as needed.
3. Select the DPI resolution. A higher DPI results in larger image files and a longer processing time.
4. Click **Browse** to select an output folder.
5. Click **Convert Now**.
6. Once the conversion is complete, use the **Open** button to view the output folder.

Output files follow the naming pattern `pdf_name_page_number.ext` (e.g., `document_page_1.jpg`). If multiple PDF files are selected, the resulting ZIP file will be named `Hasil_Konversi_YYYYMMDD_HHMMSS.zip`.

## Building an EXE

Build the application using PyInstaller and the `ImagePDF Converter.spec` file. This configuration includes the `templates` and `img` folders, the icon file `img/ikon.ico`, the splash screen `img/splash.png`, `app.manifest`, and `version.txt`.

Ensure your virtual environment is active and that the packages listed in `requirements.txt` are installed. Then, run:

```powershell
pyinstaller --clean --noconfirm "ImagePDF Converter.spec"
```

The result is a **one-folder** application (an executable accompanied by its supporting files), rather than a single standalone executable. Run it via:

```text
dist\ImagePDF Converter\ImagePDF Converter.exe
```

To distribute the application, copy the entire `dist\ImagePDF Converter` folder—do not copy just the executable file. The build process must be performed on Windows. The resulting build package includes the Python runtime and all dependencies, so the target computer does not need to have Python installed. However, the WebView2 Runtime must be present on the Windows system.

If you wish to perform a clean rebuild, manually delete the `build` and `dist` folders before running the build command. Do not delete the `img` or `templates` folders, as they are required for the packaging process.

## Notes

- The conversion code supports a DPI range of 72 to 600. The interface offers options for 150, 200, 300, and 600 DPI.
- Higher DPI settings, multi-page PDFs, and large files require more processing time and memory.
- PDF processing is performed locally by the application.
