#!/usr/bin/env python3
"""
Script to generate email content for audit file requests.
Creates formatted HTML email with Tracking ID, Control Area, and Date Due.
"""

import subprocess
import sys
from datetime import datetime


def generate_email_title(
    tracking_id: str,
    control_area: str,
    date_due: str,
    assessment: str = "2025 (Q4) - Cable Division:Cable ONE",
) -> str:
    """
    Generate email subject/title for audit file request.

    Args:
        tracking_id: The tracking ID (e.g., "REQ-3114359")
        control_area: The control area description (e.g., "AC01* - Access Control Policy")
        date_due: Date due in MM/DD/YYYY format
        assessment: I.T. Assessment description (default: "2025 (Q4) - Cable Division:Cable ONE")

    Returns:
        Formatted email title
    """
    # Convert date from MM/DD/YYYY to M/D/YYYY format (remove leading zeros)
    parts = date_due.split("/")
    if len(parts) == 3:
        month = str(int(parts[0]))
        day = str(int(parts[1]))
        year = parts[2]
        formatted_date = f"{month}/{day}/{year}"
    else:
        formatted_date = date_due

    return f"Updated Request for {assessment} - {control_area}, {tracking_id}, Date Due - {formatted_date}"


def generate_email_html(
    tracking_id: str,
    control_area: str,
    date_due: str | None = None,
    assessment: str = "2025 (Q4) - Cable Division:Cable ONE",
    assigned_to: str = "Business Unit",
    bu_contacts: str = "agent, AI Auditor; agent, AI BU",
) -> str:
    """
    Generate HTML email content for audit file request.

    Args:
        tracking_id: The tracking ID (e.g., "REQ-3114359")
        control_area: The control area description (e.g., "AC01* - Access Control Policy")
        date_due: Date due in MM/DD/YYYY format (defaults to today if not provided)
        assessment: I.T. Assessment description (default: "2025 (Q4) - Cable Division:Cable ONE")
        assigned_to: Assigned to (default: "Business Unit")
        bu_contacts: BU Contact(s) (default: "agent, AI Auditor; agent, AI BU")

    Returns:
        HTML formatted email content
    """
    if date_due is None:
        date_due = datetime.now().strftime("%m/%d/%Y")

    # Extract ID from tracking_id (e.g., "REQ-3114359" -> "3114359")
    tracking_id_number = (
        tracking_id.split("-")[-1] if "-" in tracking_id else tracking_id
    )

    # Build tracking ID link
    tracking_id_link = f"https://ghco-dev.archerirm.us/default.aspx?requestUrl=..%2fGenericContent%2fRecord.aspx%3fid%3d{tracking_id_number}%26moduleId%3d2441"

    # Default links from original example
    assessment_link = "https://ghco-dev.archerirm.us/default.aspx?requestUrl=..%2fGenericContent%2fRecord.aspx%3fid%3d3113377%26moduleId%3d3060"
    control_area_link = "https://ghco-dev.archerirm.us/default.aspx?requestUrl=..%2fGenericContent%2fRecord.aspx%3fid%3d809904%26moduleId%3d1887"

    html = f"""<div dir="ltr">
<table cellspacing="0" width="100%">
<tbody>
<tr>
<td width="100%" colspan="0" rowspan="0" style="vertical-align:top;font-family:Arial;font-size:9pt;border:1px solid rgb(255,255,255)">
<p>The request below has been updated. Please provide the additional evidence requested.</p>
<p></p>
</td>
</tr>
</tbody>
</table>

<table cellspacing="0" width="100%">
<tbody>
<tr><td colspan="1" rowspan="1" style="vertical-align:top;height:24px"></td></tr>
<tr>
<td style="border:1px solid rgb(255,255,255)">
<table width="100%" cellspacing="0" style="font-family:Arial,sans-serif;font-size:9pt">
<tbody>

<tr>
<td width="30%" style="vertical-align:top"><b>Tracking ID</b></td>
<td><div style="width:24px"></div></td>
<td width="70%" style="vertical-align:top"><a href="{tracking_id_link}" target="_blank">{tracking_id}</a></td>
</tr>
<tr><td style="height:18px"></td></tr>

<tr>
<td width="30%" style="vertical-align:top"><b>I.T. Assessments (2022 - forward)</b></td>
<td><div style="width:24px"></div></td>
<td width="70%" style="vertical-align:top"><a href="{assessment_link}" target="_blank">{assessment}</a></td>
</tr>
<tr><td style="height:18px"></td></tr>

<tr>
<td width="30%" style="vertical-align:top"><b>Test Period</b></td>
<td><div style="width:24px"></div></td>
<td width="70%" style="vertical-align:top">Interim</td>
</tr>
<tr><td style="height:18px"></td></tr>

<tr>
<td width="30%" style="vertical-align:top"><b>Requested by</b></td>
<td><div style="width:24px"></div></td>
<td width="70%" style="vertical-align:top">agent, AI Auditor</td>
</tr>
<tr><td style="height:18px"></td></tr>

<tr>
<td width="30%" style="vertical-align:top"><b>Control Area</b></td>
<td><div style="width:24px"></div></td>
<td width="70%" style="vertical-align:top"><a href="{control_area_link}" target="_blank">{control_area}</a></td>
</tr>
<tr><td style="height:18px"></td></tr>

<tr>
<td width="30%" style="vertical-align:top"><b>Request Description</b></td>
<td><div style="width:24px"></div></td>
<td width="70%" style="vertical-align:top"><p>Please submit file.</p></td>
</tr>
<tr><td style="height:18px"></td></tr>

<tr>
<td width="30%" style="vertical-align:top"><b>Interim Comments</b></td>
<td><div style="width:24px"></div></td>
<td width="70%" style="vertical-align:top">&nbsp;</td>
</tr>
<tr><td style="height:18px"></td></tr>

<tr>
<td width="30%" style="vertical-align:top"><b>Date Due</b></td>
<td><div style="width:24px"></div></td>
<td width="70%" style="vertical-align:top">{date_due}</td>
</tr>
<tr><td style="height:18px"></td></tr>

<tr>
<td width="30%" style="vertical-align:top"><b>Assigned to</b></td>
<td><div style="width:24px"></div></td>
<td width="70%" style="vertical-align:top">{assigned_to}</td>
</tr>
<tr><td style="height:18px"></td></tr>

<tr>
<td width="30%" style="vertical-align:top"><b>BU Contact(s)</b></td>
<td><div style="width:24px"></div></td>
<td width="70%" style="vertical-align:top">{bu_contacts}</td>
</tr>
<tr><td style="height:18px"></td></tr>

</tbody>
</table>
</td>
</tr>
<tr><td colspan="1" rowspan="1" style="vertical-align:top;height:24px"></td></tr>
</tbody>
</table>

<table cellspacing="0" width="100%">
<tbody>
<tr>
<td width="100%" colspan="0" rowspan="0" style="vertical-align:top;font-family:Arial;font-size:12px;border:1px solid rgb(255,255,255)">
<p style="margin:0px"><span style="color:rgb(255,0,0)"></span></p>
<p style="margin:0px;text-align:center">
<span style="color:rgb(255,0,0)">
<span style="font-family:'Times New Roman'">
<span style="color:rgb(0,0,0);font-weight:bold">Do NOT reply to this email.</span>
<span style="color:rgb(0,0,0)">It will not be sent to the person who originated this request. Please send a separate email to the requestor for clarification, or update the request comments with your concerns and assign back to the requestor.</span>
</span>
</span>
</p>
</td>
</tr>
</tbody>
</table>
</div>"""

    return html


def main():
    """Main function to run the script interactively or with arguments."""

    if len(sys.argv) > 1:
        # Command line arguments provided
        if len(sys.argv) < 3:
            print(
                "Usage: python generate_email_request.py <tracking_id> <control_area> [date_due]"
            )
            print(
                "Example: python generate_email_request.py 'REQ-3114359' 'AC01* - Access Control Policy' '09/25/2025'"
            )
            sys.exit(1)

        tracking_id = sys.argv[1]
        control_area = sys.argv[2]
        date_due = sys.argv[3] if len(sys.argv) > 3 else None
    else:
        # Interactive mode
        print("=== Email Request Generator ===\n")
        tracking_id = input("Enter Tracking ID: ").strip()
        control_area = input("Enter Control Area: ").strip()
        date_due_input = input(
            f"Enter Date Due (MM/DD/YYYY) [default: today - {datetime.now().strftime('%m/%d/%Y')}]: "
        ).strip()
        date_due = date_due_input if date_due_input else None

    # Generate email with defaults
    email_html = generate_email_html(tracking_id, control_area, date_due)

    # Generate title (need to ensure date_due is set for title generation)
    final_date_due = date_due if date_due else datetime.now().strftime("%m/%d/%Y")
    email_title = generate_email_title(tracking_id, control_area, final_date_due)

    # Try to copy to clipboard as HTML
    clipboard_status = ""
    try:
        # Try xclip with HTML target (for rich text paste)
        # Use Popen to avoid hanging and close stdin immediately
        process = subprocess.Popen(
            ["xclip", "-selection", "clipboard", "-t", "text/html"],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.communicate(input=email_html.encode(), timeout=1)
        clipboard_status = "✓ Copied HTML to clipboard!"
    except FileNotFoundError:
        clipboard_status = (
            "⚠ xclip not found (install with: sudo apt-get install xclip)"
        )
    except subprocess.TimeoutExpired:
        # xclip copied but didn't exit - this is normal for some xclip versions
        process.kill()
        clipboard_status = "✓ Copied HTML to clipboard!"
    except Exception as e:
        clipboard_status = f"⚠ Could not copy to clipboard: {e}"

    # Save to temp HTML file
    temp_file = "/tmp/email_request.html"
    try:
        with open(temp_file, "w") as f:
            f.write(
                f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
{email_html}
</body>
</html>"""
            )
        file_status = f"✓ Saved to {temp_file}"
    except Exception as e:
        file_status = f"⚠ Could not save file: {e}"

    # Output
    print("\n" + "=" * 80)
    print("EMAIL HTML CONTENT")
    print("=" * 80 + "\n")
    print(email_html)
    print("\n" + "=" * 80)
    print("EMAIL TITLE/SUBJECT")
    print("=" * 80 + "\n")
    print(email_title)
    print("\n" + "=" * 80)
    print("Email content generated successfully!")
    print(clipboard_status)
    print(file_status)
    print("\nTip: If clipboard paste doesn't work, open the HTML file in a browser")
    print("     and copy from there, or use Ctrl+Shift+V for paste as formatted.")
    print("=" * 80)


if __name__ == "__main__":
    main()
