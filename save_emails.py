import mailbox
import os
from email import policy
from email.parser import BytesParser
from email.header import decode_header
from email import quoprimime
import re
from datetime import datetime

def normalize(text):
    # Replace non-ASCII characters with underscores
    normalized_text = ''.join(c if (c.isascii() and not c.isspace()) else '_' if c.isspace() else c for c in text)
    return normalized_text

def make_safe_filename(filename):
    # Remove any characters that are not alphanumeric, underscores, or hyphens
    safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
    return safe_filename

def decode_email_header(header):
    # Decode email header and return the decoded text
    decoded_header, encoding = decode_header(header)[0]
    if encoding is not None:
        decoded_header = decoded_header.decode(encoding, errors='replace')
    return decoded_header

def decode_quoted_printable(encoded_text):
    # Decode quoted-printable content
    return quoprimime.decodestring(encoded_text)

def clean_newlines(text):
    # Remove excessive new lines, keeping at most two consecutive new lines
    return re.sub(r'\n{3,}', '\n\n', text)

def mbox_to_md(mbox_file, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Open the mbox file
    mbox = mailbox.mbox(mbox_file)

    # Process each email in the mbox file
    for i, message in enumerate(mbox):
        # Parse the email using BytesParser
        msg = BytesParser(policy=policy.default).parsebytes(message.as_bytes())

        # Get the email date and format it as YYYYMMDD
        date = datetime.strptime(msg.get("date", "Unknown"), "%a, %d %b %Y %H:%M:%S %z")
        date_str = date.strftime("%Y%m%d")

        # Create a filename based on the email subject
        subject = normalize(decode_email_header(msg.get("subject", "Untitled")))
        safe_subject = make_safe_filename(subject)
        filename = f"{date_str}_{safe_subject}.md"

        # Combine the output folder and filename
        filepath = os.path.join(output_folder, filename)

        # Write email content to the markdown file
        with open(filepath, "w", encoding="utf-8") as md_file:
            # Write metadata
            md_file.write(f"Subject: {subject}\n")
            md_file.write(f"From: {normalize(decode_email_header(msg.get('from', 'Unknown')))}\n")
            md_file.write(f"To: {normalize(decode_email_header(msg.get('to', 'Unknown')))}\n")
            md_file.write(f"Date: {normalize(decode_email_header(msg.get('date', 'Unknown')))}\n\n")

            # Write the body, decoding quoted-printable content and cleaning new lines
            if msg.is_multipart():
                # If the email is multipart, write the plain text part
                for part in msg.iter_parts():
                    if part.get_content_type() == "text/plain":
                        md_file.write(clean_newlines(decode_quoted_printable(part.get_payload())))
                        break
            else:
                # If the email is not multipart, write the body directly
                md_file.write(clean_newlines(decode_quoted_printable(msg.get_payload())))

        print(f"Processed email {i+1} and saved to {filename}")

if __name__ == "__main__":
    # Provide the path to your mbox file and the output folder for MD files
    mbox_file_path = "path/to/your/takeout.mbox"
    output_folder_path = "path/to/output/folder"

    mbox_to_md(mbox_file_path, output_folder_path)