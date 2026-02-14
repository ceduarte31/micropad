import csv
import argparse
import os
import logging

def setup_logger():
    """Configures a logger to output to console and a file inside the 'logs' folder."""
    logger = logging.getLogger('Deduplicator')
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # --- Create 'logs' directory ---
        log_directory = "logs"
        os.makedirs(log_directory, exist_ok=True)
        log_filepath = os.path.join(log_directory, 'deduplicator.log')
        # -----------------------------

        # File handler (writes to logs/deduplicator.log)
        file_handler = logging.FileHandler(log_filepath, mode='w')
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatters
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

logger = setup_logger()

def get_emails_from_file(filename, email_column):
    """Reads a CSV file and returns a set of all emails."""
    logger.info(f"Reading emails from the source file: '{filename}'")
    emails = set()
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for i, row in enumerate(reader, 1):
                if email_column in row and row[email_column]:
                    email = row[email_column].strip().lower()
                    if email not in emails:
                        emails.add(email)
                        logger.debug(f"Found unique email '{email}' at row {i} in '{filename}'.")
                else:
                    logger.warning(f"Row {i} in '{filename}' is missing the email column '{email_column}' or it's empty.")
        logger.info(f"Successfully found {len(emails)} unique emails in '{filename}'.")
        return emails
    except FileNotFoundError:
        logger.critical(f"FATAL: The file '{filename}' was not found. Aborting.")
        return None
    except Exception as e:
        logger.critical(f"An unexpected error occurred while reading '{filename}': {e}")
        return None

def deduplicate_csv(original_file, new_file, output_file, email_column):
    """
    Compares two CSV files, removes duplicate email entries, and logs everything.
    """
    logger.info("--- 🚀 Starting CSV Deduplicator ---")
    logger.info(f"Original (source) file: {original_file}")
    logger.info(f"New (to be cleaned) file: {new_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Email column name: '{email_column}'")

    original_emails = get_emails_from_file(original_file, email_column)

    if original_emails is None:
        logger.error("Could not proceed due to errors reading the original file.")
        return

    logger.info(f"Now processing the new file: '{new_file}'...")
    try:
        with open(new_file, 'r', newline='', encoding='utf-8') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8') as outfile:

            reader = csv.DictReader(infile)
            if not reader.fieldnames:
                logger.critical(f"The new file '{new_file}' is empty or has no header. Aborting.")
                return
                
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()
            logger.debug(f"Output file header written: {', '.join(reader.fieldnames)}")

            unique_rows_written = 0
            duplicates_found = 0

            for i, row in enumerate(reader, 2):
                email = row.get(email_column, "").strip().lower()

                if not email:
                    logger.warning(f"Row {i} in '{new_file}' has an empty email. Skipping.")
                    continue

                if email in original_emails:
                    duplicates_found += 1
                    logger.info(f"DUPLICATE FOUND: Email '{email}' from row {i} of '{new_file}' exists in the original file. Skipping row.")
                else:
                    writer.writerow(row)
                    unique_rows_written += 1
                    logger.debug(f"UNIQUE: Email '{email}' from row {i} of '{new_file}' is new. Writing to output.")
            
            logger.info("--- ✅ Process Complete ---")
            logger.info(f"Summary:")
            logger.info(f"  - Duplicates found and skipped: {duplicates_found}")
            logger.info(f"  - New, unique rows written: {unique_rows_written}")
            logger.info(f"  - Output file generated at: '{output_file}'")
            logger.info("Log file with detailed steps is available at: 'logs/deduplicator.log'")

    except FileNotFoundError:
        logger.critical(f"FATAL: The file '{new_file}' was not found. Aborting.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred during deduplication: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deduplicate a new CSV file based on emails in an original CSV file, with detailed logging."
    )
    parser.add_argument("original_file", help="The path to the original CSV file.")
    parser.add_argument("new_file", help="The path to the new CSV file to be deduplicated.")
    parser.add_argument("-o", "--output", default="deduplicated_output.csv", help="The name for the output CSV file (default: deduplicated_output.csv).")
    parser.add_argument("-c", "--column", default="email", help="The name of the column containing email addresses (default: 'email').")
    
    args = parser.parse_args()
    deduplicate_csv(args.original_file, args.new_file, args.output, args.column)