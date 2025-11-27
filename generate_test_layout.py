import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gabarito_generator_v2 import generate_standard_gabarito_v2

try:
    pdf_content = generate_standard_gabarito_v2(50)
    with open('gabarito_v2_layout_test.pdf', 'wb') as f:
        f.write(pdf_content)
    print("PDF generated successfully: gabarito_v2_layout_test.pdf")
except Exception as e:
    print(f"Error: {e}")
