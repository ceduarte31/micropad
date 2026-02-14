import orjson
import os
from .repository import (
    Repository,
    download_repository,
)
from .tokens import TokenManager
from .constants import constants
from .logger import logger


def select_filtered_file():
    """Prompts user to enter the path for the filtered JSON Lines file."""
    while True:
        file_path = input(constants["FilteredDataFile"])
        if os.path.isfile(file_path):
            logger.info(f"User selected filtered file: {file_path}")
            return file_path
        else:
            print(constants["FileDoesNotExist"])
            logger.warning(f"User entered non-existent file path: {file_path}")


def select_number_of_repositories_to_download(total_available: int):
    """Prompts user to enter the number of repositories to download."""
    while True:
        try:
            print(f"Total filtered repositories available: {total_available}")
            number = int(input(constants["NumberOfRepositoriesToDownload"]))
            if number == 0:
                logger.info(f"User selected to download all {total_available} repositories")
                return total_available
            elif 1 <= number <= total_available:
                logger.info(f"User selected to download {number} repositories")
                return number
            else:
                print(f"⚠️ Please enter a number between 0 and {total_available}")
        except ValueError:
            print(constants["InvalidSelection"])


def load_filtered_repositories_from_file(file_path: str) -> list:
    """Loads a list of repository data from a JSON Lines file."""
    with open(file_path, "rb") as f:
        return [orjson.loads(line) for line in f]


def main():
    """
    Main function to download a specified number of repositories from a filtered list.
    """
    print(constants["WelcomeToMicroREFDownloader"])
    logger.info(constants["StartingDownloader"])

    token_manager = TokenManager()
    if not token_manager.tokens:
        print(constants["TokensNotFound"])
        logger.error(constants["TokensNotFound"])
        return

    filtered_file = select_filtered_file()
    all_repos_data = load_filtered_repositories_from_file(filtered_file)
    
    if not all_repos_data:
        print("No repositories found in the filtered file.")
        logger.warning("No repositories found in the provided filtered file.")
        return

    num_to_download = select_number_of_repositories_to_download(len(all_repos_data))
    repos_to_download = all_repos_data[:num_to_download]
    
    successfully_downloaded = 0
    failed_downloads = 0

    for i, repo_data in enumerate(repos_to_download):
        print(f"\n--- Downloading {i+1}/{len(repos_to_download)}: {repo_data['name']} ---")
        logger.info(f"Attempting to download {repo_data['name']}")
        
        try:
            repo = Repository(
                repo_data["name"],
                repo_data["metadata"].get("created_at", ""),
            )
            # Set the default branch from the collected metadata
            repo.default_branch = repo_data["metadata"].get("default_branch", "main")
            
            # Attempt to download the repository
            download_result = download_repository(repo, token_manager)
            
            if download_result:
                successfully_downloaded += 1
                print(f"✅ Successfully downloaded to: {download_result}")
                logger.info(f"Successfully downloaded {repo.name} to {download_result}")
            else:
                failed_downloads += 1
                print(f"❌ Download failed for {repo.name}")
                logger.error(f"Download failed for {repo.name}")

        except Exception as e:
            failed_downloads += 1
            print(f"❌ Unexpected error downloading {repo_data['name']}: {e}")
            logger.error(f"Unexpected error downloading {repo_data['name']}: {e}")

    # Print summary statistics
    print(f"\n{constants['DownloadProcessComplete']}")
    print(f"📊 Download Summary:")
    print(f"   • Total attempted: {len(repos_to_download)}")
    print(f"   • Successfully downloaded: {successfully_downloaded}")
    print(f"   • Failed downloads: {failed_downloads}")
    print(f"   • Success rate: {(successfully_downloaded/len(repos_to_download)*100):.1f}%")
    
    output_dir = os.getenv("OUTPUT_DIR", "./out/repositories")
    print(f"   • Downloaded repositories location: {output_dir}")
    
    logger.info(
        f"Download process complete. Successfully downloaded {successfully_downloaded} out of {len(repos_to_download)} repositories."
    )


if __name__ == "__main__":
    main()