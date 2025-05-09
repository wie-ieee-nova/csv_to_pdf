import csv
import argparse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


def format_address(data):
    """
    Formats the address fields into a single string.

    Args:
        data (dict): A dictionary containing the address fields.

    Returns:
        str: A formatted address string.
    """
    address_parts = []
    if data.get('Address (Street Address)'):
        address_parts.append(data['Address (Street Address)'])
        # remove the field from data
    if data.get('Address (Address Line 2)'):
        address_parts.append(data['Address (Address Line 2)'])
    city_state_zip = f"{data.get('Address (City)', '')}, {data.get('Address (State / Province)', '')} {data.get('Address (ZIP / Postal Code)', '')}"
    if city_state_zip != ",  ":  # Avoid adding empty city/state/zip
        address_parts.append(city_state_zip)
    if data.get('Address (Note: We are unable to sponsor or provide visas.)'):
        address_parts.append(data['Address (Note: We are unable to sponsor or provide visas.)'])

    del data['Address (Street Address)']
    del data['Address (Address Line 2)']
    del data['Address (City)']
    del data['Address (State / Province)']
    del data['Address (ZIP / Postal Code)']
    del data['Address (Note: We are unable to sponsor or provide visas.)']
    return address_parts


def format_speaker_info(data, styles):
    """
    Formats and returns speaker information as a list of Paragraphs and Spacers.

    Args:
        data (dict): A dictionary containing the data for the entry.
        styles (dict): The styles dictionary from reportlab.

    Returns:
        list: A list of Paragraphs and Spacers.

    """
    speaker_info = []

    speaker_keys = [key for key in data if "Speaker(s)/ Author(s) Info" in key]
    for key in speaker_keys:
        speaker = data.get(key, '')
        if not speaker:
            break
        speaker_info.append(Paragraph(f"<b>{key}:</b>", styles['Normal']))
        speaker = speaker.split('|')
        if speaker[0] and speaker[1]:
            speaker_info.append(Paragraph(f"{speaker[0]}, {speaker[1]}", styles['Normal']))
        if speaker[3]:
            speaker_info.append(Paragraph(f"{speaker[3]}", styles['Normal']))   # email
        if speaker[2]:
            speaker_info.append(Paragraph(f"{speaker[2]}", styles['Normal']))   # organization
        speaker_info.append(Spacer(1, 0.1 * inch))

    primary_email = data.get('Primary/Preferred Email to contact (Enter Email)', '')
    speaker_info.append(Paragraph(f"<b>Primary Email:</b>", styles['Normal']))
    speaker_info.append(Paragraph(primary_email, styles['Normal']))
    speaker_info.append(Spacer(1, 0.1 * inch))

    phone = data.get('Phone', '')
    speaker_info.append(Paragraph(f"<b>Phone:</b>", styles['Normal']))
    speaker_info.append(Paragraph(phone, styles['Normal']))
    speaker_info.append(Spacer(1, 0.1 * inch))

    job_title = data.get('Job Title', '')
    speaker_info.append(Paragraph(f"<b>Job Title:</b>", styles['Normal']))
    speaker_info.append(Paragraph(job_title, styles['Normal']))
    speaker_info.append(Spacer(1, 0.1 * inch))
    
    return speaker_info


def csv_to_pdf(csv_filepath, pdf_filepath, blind_judge=True):
    """
    Converts a CSV file to a PDF file with each row representing a page/set of pages.

    Args:
        csv_filepath (str): The path to the CSV file.
        pdf_filepath (str): The path to the output PDF file.
    """

    doc = SimpleDocTemplate(pdf_filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    with open(csv_filepath, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Get the header row
        header = [h.replace('"', '') for h in header] #Clean up headers

        # Add the header to the PDF
        story.append(Paragraph("Call For Participation Entries", styles['h1']))
        story.append(Spacer(1, 0.2 * inch))

        for row in reader:
            # Create a new page for each row
            data = {}
            for i, col in enumerate(header):
                data[col] = row[i]

            story.append(PageBreak())

            # Use entry ID as the title
            entry_id = data.get('Entry Id', 'No Entry ID')
            story.append(Paragraph(f"Entry ID: {entry_id}", styles['h2']))
            story.append(Spacer(1, 0.1 * inch))

            address = format_address(data)

            for key, value in data.items():
                # Skip empty values
                if not value.strip() or key == 'Entry Id':
                    continue
                if key == 'Entry Id':
                    story.append(Paragraph(f"Entry ID: {value}", styles['h2']))
                    story.append(Spacer(1, 0.1 * inch))
                elif 'Speaker(s)/ Author(s)' in key:
                    formatted_info = format_speaker_info(data, styles)
                    if not blind_judge and formatted_info:
                        story.extend(formatted_info)
                        story.append(Spacer(1, 0.1 * inch))
                elif key in ['Phone', 'Primary/Preferred Email to contact (Enter Email)']:
                    continue
                elif key == 'Job Title':
                    # Use this as an opportunity to add the address
                    story.append(Paragraph(f"<b>Address:</b>", styles['Normal']))
                    if blind_judge:
                        story.append(Paragraph(address[-1], styles['Normal']))
                    else:
                        for a in address:
                            story.append(Paragraph(a, styles['Normal']))
                    story.append(Spacer(1, 0.1 * inch))
                elif "Extended Abstract" in key:
                    story.append(Paragraph(f"<b>Abstract Link:</b>", styles['Normal']))
                    text = f"<a href='{value}'>{value}</a>"
                    story.append(Paragraph(text, styles['Normal']))
                    story.append(Spacer(1, 0.1 * inch))
                else:
                    story.append(Paragraph(f"<b>{key}:</b>", styles['Normal']))
                    story.append(Paragraph(value, styles['Normal']))
                    story.append(Spacer(1, 0.1 * inch))

        doc.build(story)

def main():
    """This script takes a CSV file via command line argument and converts it to a PDF file.
    If blind_judge flag is set to True, it will not include speaker information."""

    parser = argparse.ArgumentParser(description='Convert CSV to PDF.')
    parser.add_argument('csv_file', type=str, help='Path to the CSV file')
    parser.add_argument('pdf_file', type=str, help='Path to the output PDF file')
    parser.add_argument('--blind', action='store_true', help='Exclude speaker information for blind judging')
    args = parser.parse_args()
    if args.blind:
        print("Blind judging mode is enabled. Speaker information will be excluded.")
    else:
        print("Blind judging mode is disabled. Speaker information will be included.")

    csv_to_pdf(args.csv_file, args.pdf_file, blind_judge=args.blind)
    print(f"Successfully converted {args.csv_file} to {args.pdf_file}")


if __name__ == '__main__':
    main()