import os
import requests
code = 0
def generate_paper_links(base_url, start_year, end_year, paper_code):
    sessions = {'w': 'Oct-Nov', 'm': 'March', 's': 'May-June'}
    links = []
    for year in range(start_year, end_year + 1):
        for session_code, session_name in sessions.items():
            # Add `_42` explicitly to target the correct file
            file_name = f"0625_{session_code}{str(year)[-2:]}_{paper_code}_42.pdf"
            full_url = f"{base_url}{year}-{session_name}/{file_name}"
            links.append((year, session_name, full_url))
    return links

def download_papers(links, base_dir):
    global code

    for year, session_name, link in links:
        code = code + 1
        try:
            response = requests.get(link)
            if response.status_code == 200:
                # Create directory structure if it doesn't exist
                year_dir = os.path.join(base_dir, str(year))
                if not os.path.exists(year_dir):
                    os.makedirs(year_dir)

                # Define the PDF file name
                pdf_name = f"{session_name.replace('-', ' ')}  .pdf"
                file_path = os.path.join(year_dir, pdf_name)

                with open(file_path, 'wb') as file:
                    file.write(response.content)
                print(f"Downloaded: {file_path}")
            else:
                print(f"Failed to download {link}: Status code {response.status_code}")
        except Exception as e:
            print(f"Error downloading {link}: {e}")

def main():
    subjects = {
        "physics": "https://pastpapers.co/cie/IGCSE/Physics-0625/",
        "chemistry": "https://pastpapers.co/cie/IGCSE/Chemistry-0620/",
        "computer science": "https://pastpapers.co/cie/IGCSE/Computer-Science-0478/"
    }

    print("Choose an option:")
    print("1. Download question papers")
    print("2. Print question paper links")
    print("3. Print mark scheme links")
    choice = input("Enter your choice (1/2/3): ").strip()

    subject = input("Enter the subject (Physics/Chemistry/Computer Science): ").strip().lower()
    if subject not in subjects:
        print("Invalid subject. Please choose Physics, Chemistry, or Computer Science.")
        return

    base_url = subjects[subject]

    start_year = int(input("Enter the start year (e.g., 2020): ").strip())
    end_year = int(input("Enter the end year (e.g., 2025): ").strip())

    if choice == "1":
        # Download Question Papers
        links = generate_paper_links(base_url, start_year, end_year, paper_code="ms")
        download_papers(links, f"{subject.capitalize()} Past Papers")
    elif choice == "2":
        # Print Question Paper Links
        links = generate_paper_links(base_url, start_year, end_year, paper_code="ms")
        print("\nGenerated Links for Question Papers:")
        for year, session_name, link in links:
            print(f"{year} {session_name}: {link}")
    elif choice == "3":
        # Print Mark Scheme Links
        links = generate_paper_links(base_url, start_year, end_year, paper_code="ms")
        print("\nGenerated Links for Mark Schemes:")
        for year, session_name, link in links:
            print(f"{year} {session_name}: {link}")
    else:
        print("Invalid choice. Please choose 1, 2, or 3.")

if __name__ == "__main__":
    main()
