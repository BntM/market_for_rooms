import zipfile
import xml.etree.ElementTree as ET
import os

pptx_file = "Patriot AI and the Cloudforce Way.pptx"

def extract_text_from_pptx(pptx_path):
    text_content = []
    try:
        with zipfile.ZipFile(pptx_path, 'r') as zf:
            # Slides are usually located at ppt/slides/slide*.xml
            slide_files = [f for f in zf.namelist() if f.startswith("ppt/slides/slide") and f.endswith(".xml")]
            
            # Sort slides numerically if possible (slide1.xml, slide2.xml...)
            slide_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))

            for slide_file in slide_files:
                slide_xml = zf.read(slide_file)
                tree = ET.fromstring(slide_xml)
                
                # Namespaces can vary, but usually look something like this
                # We can just iterate all elements and look for <a:t> nodes which contain text
                slide_text = []
                for elem in tree.iter():
                    if elem.tag.endswith('}t'): # Text body tag
                        if elem.text:
                            slide_text.append(elem.text)
                
                if slide_text:
                    text_content.append(f"--- Slide {slide_file} ---\n" + "\n".join(slide_text))
                    
    except Exception as e:
        return f"Error extracting text: {e}"

    return "\n\n".join(text_content)

if __name__ == "__main__":
    if os.path.exists(pptx_file):
        print(extract_text_from_pptx(pptx_file))
    else:
        print(f"File not found: {pptx_file}")
